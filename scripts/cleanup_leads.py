#!/usr/bin/env python3
"""
Lead cleanup pipeline (run from repo root).

1. Delete companies flagged as junk by `is_junk(name)` (signals/scores cascade).
2. Rename headline-like `companies.name` when a proper name can be parsed from signal text.
3. Re-infer `companies.industry` from name + all signal texts (`infer_industry_from_text`).
4. Rebuild `companies.automation_profile` (rules_v1 JSON) for every remaining row.

Does not register FastAPI/Celery ORM hooks — updates profiles explicitly.

Industry step is **conservative** by default: only fills empty / Unknown / Other / New.
Use `--force-industry` to overwrite every row (NOISY signal text often mislabels companies).

Usage:
  python3 scripts/cleanup_leads.py                    # dry-run (summary only)
  python3 scripts/cleanup_leads.py --apply            # execute all steps
  python3 scripts/cleanup_leads.py --apply --skip-industry   # purge + names + profiles only
  python3 scripts/cleanup_leads.py --apply --force-industry # dangerous full industry rewrite
  python3 scripts/cleanup_leads.py --apply --limit-names 200

After a noisy scraper run, prefer `--skip-industry` unless you intend to refill
industry from signal text. For ML feedback, export decisions with
`scripts/export_quality_decision_log.py` (see docs/lead_quality_pipeline.md).

Env: DATABASE_URL via .env / frontend/nextjs/.env.local (same as other scripts).
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

from dotenv import load_dotenv

_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.company import Company
from app.services.automation_profile import build_automation_profile_dict_from_company
from app.services.company_name_inference import (
    best_name_from_signals,
    should_attempt_name_fix,
)
from app.services.industry_inference import (
    infer_industry_from_text,
    should_skip_industry_reinfer_for_company_name,
)
from app.services.lead_filter import is_junk


@dataclass
class Stats:
    junk_deleted: int = 0
    names_changed: int = 0
    names_would_change: int = 0
    names_skipped_duplicate: int = 0
    names_skipped_no_candidate: int = 0
    industry_updated: int = 0
    profiles_updated: int = 0


def _load_companies_with_signals(db):
    return (
        db.query(Company)
        .options(joinedload(Company.signals))
        .order_by(Company.id)
        .all()
    )


def phase_purge_junk(db, apply: bool, stats: Stats) -> None:
    rows = db.query(Company.id, Company.name).all()
    to_delete = []
    for cid, name in rows:
        bad, reason = is_junk(name)
        if bad:
            to_delete.append((cid, name, reason))

    print(f"\n── Purge junk ──  candidates: {len(to_delete)}")
    for cid, name, reason in to_delete[:25]:
        print(f"  id={cid}  [{reason[:50]}]  {name[:100]!r}")
    if len(to_delete) > 25:
        print(f"  … +{len(to_delete) - 25} more")

    if not apply or not to_delete:
        return

    for cid, _, _ in to_delete:
        c = db.get(Company, cid)
        if c:
            db.delete(c)
            stats.junk_deleted += 1
    db.commit()
    print(f"  ✅ Deleted {stats.junk_deleted} junk companies.")


def phase_infer_names(db, apply: bool, stats: Stats, limit: int | None) -> None:
    companies = _load_companies_with_signals(db)
    n = 0
    for c in companies:
        if limit is not None and n >= limit:
            break
        if not should_attempt_name_fix(c.name):
            continue
        texts = [s.signal_text for s in (c.signals or []) if s.signal_text]
        cand = best_name_from_signals(texts)
        if not cand:
            stats.names_skipped_no_candidate += 1
            continue
        if cand.strip().lower() == (c.name or "").strip().lower():
            continue
        dup = (
            db.query(Company)
            .filter(func.lower(Company.name) == cand.strip().lower())
            .filter(Company.id != c.id)
            .first()
        )
        if dup:
            stats.names_skipped_duplicate += 1
            print(f"  skip rename id={c.id}: duplicate name {cand!r} (existing id={dup.id})")
            continue
        n += 1
        print(f"  rename id={c.id}: {c.name[:80]!r} → {cand!r}")
        if apply:
            c.name = cand.strip()
            stats.names_changed += 1
        else:
            stats.names_would_change += 1
    if apply and stats.names_changed:
        db.commit()
    print(
        f"  Summary: changed={stats.names_changed} would_change={stats.names_would_change} "
        f"(dry-run); no candidate {stats.names_skipped_no_candidate}; duplicate {stats.names_skipped_duplicate}"
    )


def _industry_slot_empty(stored: Optional[str]) -> bool:
    s = (stored or "").strip().lower()
    return not s or s in ("unknown", "other", "new")


def phase_reinfer_industry(db, apply: bool, stats: Stats, *, force_all: bool) -> None:
    companies = _load_companies_with_signals(db)
    n = 0
    for c in companies:
        if not force_all and not _industry_slot_empty(c.industry):
            continue
        if should_skip_industry_reinfer_for_company_name(c.name):
            continue
        parts = [c.name or ""]
        for s in c.signals or []:
            if s.signal_text:
                parts.append(s.signal_text)
        blob = " ".join(parts)
        inf = infer_industry_from_text(blob)
        if inf == "Unknown":
            continue
        if (c.industry or "").strip() == inf:
            continue
        n += 1
        if n <= 50:
            tag = "" if apply else "[dry-run] "
            print(f"  {tag}industry id={c.id} {(c.name or '')[:40]!r} → {inf}")
        elif n == 51:
            mode = "all rows" if force_all else "empty/unknown slots only"
            print(f"  … (suppress further lines; mode={mode})")
        if apply:
            c.industry = inf
    stats.industry_updated = n
    if apply and n:
        db.commit()
    print(
        f"  Industry rows {'updated' if apply else 'to update'}: {n} "
        f"(force_all={'yes' if force_all else 'no — only empty/unknown/other/new'})"
    )


def phase_rebuild_profiles(db, apply: bool, stats: Stats) -> None:
    companies = _load_companies_with_signals(db)
    batch = 0
    for c in companies:
        new_p = build_automation_profile_dict_from_company(c)
        if apply:
            c.automation_profile = new_p
            stats.profiles_updated += 1
            batch += 1
            if batch >= 250:
                db.commit()
                batch = 0
        else:
            stats.profiles_updated += 1
    if apply:
        db.commit()
    print(f"  Automation profiles written: {stats.profiles_updated} companies")


def main() -> None:
    ap = argparse.ArgumentParser(description="Clean junk leads, fix names, reinfer industry, rebuild profiles")
    ap.add_argument("--apply", action="store_true", help="Actually modify the database (default is dry-run)")
    ap.add_argument("--skip-purge", action="store_true")
    ap.add_argument("--skip-names", action="store_true")
    ap.add_argument("--skip-industry", action="store_true")
    ap.add_argument("--skip-profiles", action="store_true")
    ap.add_argument(
        "--force-industry",
        action="store_true",
        help="Overwrite industry for every company (default: only fill empty/Unknown/Other/New)",
    )
    ap.add_argument("--limit-names", type=int, default=None, help="Max headline renames to process (safety)")
    args = ap.parse_args()
    apply = args.apply

    if not apply:
        print("DRY RUN — no writes. Pass --apply to execute.\n")

    db = SessionLocal()
    # With NullPool (Supabase session pooler), each commit closes the connection; default
    # expire_on_commit=True then forces lazy loads that reopen DB — fragile for long batches.
    db.expire_on_commit = False
    stats = Stats()
    try:
        if not args.skip_purge:
            phase_purge_junk(db, apply, stats)
            db.expire_all()

        if not args.skip_names:
            print("\n── Infer names from signal text ──")
            phase_infer_names(db, apply, stats, args.limit_names)

        if not args.skip_industry:
            print("\n── Re-infer industry ──")
            phase_reinfer_industry(db, apply, stats, force_all=args.force_industry)

        if not args.skip_profiles:
            print("\n── Rebuild automation_profile ──")
            phase_rebuild_profiles(db, apply, stats)

        print("\n── Done ──")
        print(stats)
    finally:
        db.close()


if __name__ == "__main__":
    main()
