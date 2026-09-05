#!/usr/bin/env python3
"""
Lead cleanup pipeline (run from repo root).

1. Delete companies that fail the full logic-engine gate `is_valid_lead(name)` —
   junk filter, inference gate, distinctive-word check, optional Wikidata/DNS, etc.
   (not only `is_junk`). Child rows (signals, scores, contacts, feedback) removed first.
   Pass ``--purge-junk-only`` to delete only rows matching ``is_junk()`` (faster, narrower).
2. Normalize `companies.name`: trim whitespace, collapse repeated spaces (safe renames only).
3. Rename headline-like `companies.name` when a proper name can be parsed from signal text.
4. Re-infer `companies.industry` from name + all signal texts (`infer_industry_from_text`).
5. Rebuild `companies.automation_profile` (rules_v1 JSON) for every remaining row.

Does not register FastAPI/Celery ORM hooks — updates profiles explicitly.

Industry step is **conservative** by default: only fills empty / Unknown / Other / New.
Use `--force-industry` to overwrite every row (NOISY signal text often mislabels companies).

Usage:
  python3 scripts/cleanup_leads.py                    # dry-run (summary only)
  python3 scripts/cleanup_leads.py --apply            # execute all steps
  python3 scripts/cleanup_leads.py --apply --skip-industry   # purge + normalize + names + profiles
  python3 scripts/cleanup_leads.py --apply --force-industry # dangerous full industry rewrite
  python3 scripts/cleanup_leads.py --apply --limit-names 200
  python3 scripts/cleanup_leads.py --apply --skip-normalize  # skip whitespace normalization
  python3 scripts/cleanup_leads.py --apply --purge-junk-only --skip-industry  # fast is_junk-only purge

After a noisy scraper run, prefer `--skip-industry` unless you intend to refill
industry from signal text. For ML feedback, export decisions with
`scripts/export_quality_decision_log.py` (see docs/lead_quality_pipeline.md).

Env: DATABASE_URL via repo-root .env / frontend/nextjs/.env.local (same as app/database.py).

Git worktrees (e.g. .cursor/worktrees/.../mkf) use a *different* directory than your main
clone. If DATABASE_URL exists only under Desktop/Ready_For_Robots/.env, either copy that
file into the worktree root, symlink it, or run:

  export DOTENV_PATH=/full/path/to/main/Ready_For_Robots/.env

before python (see app/database.py — DOTENV_PATH overrides after repo-root .env).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

# Must run before load_dotenv: override=True would otherwise stomp `export DATABASE_URL`.
_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_cleanup_dotenv = (os.getenv("DOTENV_PATH") or "").strip()
if _cleanup_dotenv:
    load_dotenv(Path(_cleanup_dotenv).expanduser(), override=True)
_loaded_after_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded_after_dotenv):
    os.environ["DATABASE_URL"] = _shell_database_url

from sqlalchemy import func, text
from sqlalchemy.orm import joinedload

from app.database import DATABASE_URL, SessionLocal, engine
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
from app.services.company_validator import is_valid_lead
from app.services.lead_filter import is_junk
from app.models.lead_rep_feedback import LeadRepFeedback
from app.models.contact import Contact
from app.models.score import Score
from app.models.signal import Signal


@dataclass
class Stats:
    junk_deleted: int = 0
    normalized_names: int = 0
    normalized_would_apply: int = 0
    names_changed: int = 0
    names_would_change: int = 0
    names_skipped_duplicate: int = 0
    names_skipped_no_candidate: int = 0
    industry_updated: int = 0
    profiles_updated: int = 0


def _normalize_whitespace(name: str) -> str:
    """Trim and collapse internal spaces; do not change casing."""
    s = (name or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _delete_company_rows(db, company_id: int) -> None:
    """Remove FK children before companies row (Postgres signals may lack ON DELETE CASCADE)."""
    db.query(LeadRepFeedback).filter(LeadRepFeedback.company_id == company_id).delete(
        synchronize_session=False
    )
    db.query(Signal).filter(Signal.company_id == company_id).delete(synchronize_session=False)
    db.query(Score).filter(Score.company_id == company_id).delete(synchronize_session=False)
    db.query(Contact).filter(Contact.company_id == company_id).delete(synchronize_session=False)
    db.query(Company).filter(Company.id == company_id).delete(synchronize_session=False)


def _load_companies_with_signals(db):
    return (
        db.query(Company)
        .options(joinedload(Company.signals))
        .order_by(Company.id)
        .all()
    )


def _exit_if_db_not_configured() -> None:
    """
    When DATABASE_URL is unset, app.database falls back to SQLite; the worktree
    often has no migrated DB → opaque 'no such table: companies'. Fail fast
    with instructions instead.

    For PostgreSQL URLs, verify TCP/DNS before bulk work (catches typos like
    aws-....pooler.supabase.com).
    """
    from urllib.parse import urlparse as _urlparse

    url = DATABASE_URL or ""
    url_lower = url.lower()

    if "postgresql" in url_lower or "postgres" in url_lower:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.execute(text("SELECT 1 FROM companies LIMIT 1"))
        except Exception as e:
            err_low = str(e).lower()
            raw = str(e)
            if "could not translate host name" in err_low or "nodename nor servname" in err_low:
                u = url.replace("postgresql+psycopg2://", "postgresql://", 1)
                host = (_urlparse(u).hostname or "") or "?"
                extra = ""
                if "...." in host:
                    extra = (
                        "\n  The hostname contains four dots (....) — that is not valid. "
                        "In Supabase → Database → Connection string, copy the full host, e.g. "
                        "aws-0-us-east-1.pooler.supabase.com (your region may differ).\n"
                    )
                print(
                    "\nERROR: PostgreSQL host does not resolve (DNS).\n"
                    f"  Attempted host: {host!r}\n"
                    f"  {raw}\n"
                    f"{extra}",
                    file=sys.stderr,
                )
                sys.exit(3)
            if "no such table" in err_low or "does not exist" in err_low:
                print(
                    "\nERROR: Connected to PostgreSQL but there is no `companies` table "
                    "(wrong database or migrations not applied).\n",
                    file=sys.stderr,
                )
                sys.exit(2)
            raise
        return

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM companies LIMIT 1"))
    except Exception as e:
        err = str(e).lower()
        if "no such table" in err or "does not exist" in err:
            print(
                "\nERROR: DATABASE_URL is not set to PostgreSQL, and there is no local "
                "`companies` table.\n"
                "  Add DATABASE_URL to the repo-root .env next to this script "
                "(same URI as Fly / Supabase session pooler), for example:\n"
                "    DATABASE_URL=postgresql://postgres.PROJECT:PASSWORD@"
                "aws-0-REGION.pooler.supabase.com:5432/postgres\n"
                "  (Use the exact host from Supabase — not aws-....pooler.)\n"
                "  Or export it for one shell:\n"
                "    export DATABASE_URL='postgresql://...'\n"
                "  Do not paste commands and comments together; run each line separately.\n",
                file=sys.stderr,
            )
            sys.exit(2)
        raise


def phase_purge_junk(db, apply: bool, stats: Stats, *, junk_only: bool = False) -> None:
    rows = db.query(Company.id, Company.name).all()
    total = len(rows)
    mode = (
        "is_junk() — regex/substring junk filter (fast)"
        if junk_only
        else "is_valid_lead() — full logic engine + classifier (slow on large DBs)"
    )
    print(
        f"\n── Purge scan ──  {total} companies ({mode}; progress every 500)…",
        flush=True,
    )
    to_delete = []
    for i, (cid, name) in enumerate(rows):
        if i and i % 500 == 0:
            print(f"  … processed {i}/{total} companies", flush=True)
        if junk_only:
            bad, reason = is_junk(name or "")
            if bad:
                to_delete.append((cid, name, reason))
        else:
            ok, reason = is_valid_lead(name or "")
            if not ok:
                to_delete.append((cid, name, reason))

    purge_label = "Purge junk (is_junk)" if junk_only else "Purge invalid (is_valid_lead)"
    print(f"\n── {purge_label} ──  candidates: {len(to_delete)}")
    for cid, name, reason in to_delete[:25]:
        print(f"  id={cid}  [{reason[:72]}]  {name[:100]!r}")
    if len(to_delete) > 25:
        print(f"  … +{len(to_delete) - 25} more")

    if not apply or not to_delete:
        return

    for cid, _, _ in to_delete:
        _delete_company_rows(db, cid)
        stats.junk_deleted += 1
    db.commit()
    print(f"  ✅ Deleted {stats.junk_deleted} invalid companies.")


def phase_normalize_names(db, apply: bool, stats: Stats) -> None:
    """Trim/collapse whitespace on names that still pass validation; skip duplicates."""
    rows = db.query(Company).order_by(Company.id).all()
    nrows = len(rows)
    print(
        f"── Normalize scan ──  {nrows} companies (re-validates each changed name)…",
        flush=True,
    )
    updates: list[tuple[int, str, str]] = []
    for i, c in enumerate(rows):
        if i and i % 500 == 0:
            print(f"  … normalize pass {i}/{nrows}", flush=True)
        old = c.name or ""
        new = _normalize_whitespace(old)
        if new == old:
            continue
        ok, _ = is_valid_lead(new)
        if not ok:
            continue
        dup = (
            db.query(Company.id)
            .filter(func.lower(Company.name) == new.lower())
            .filter(Company.id != c.id)
            .first()
        )
        if dup:
            print(f"  skip normalize id={c.id}: would conflict with id={dup[0]} {new!r}")
            continue
        updates.append((c.id, old, new))

    print(f"\n── Normalize whitespace ──  candidates: {len(updates)}")
    for cid, old, new in updates[:30]:
        print(f"  id={cid}  {old[:70]!r} → {new[:70]!r}")
    if len(updates) > 30:
        print(f"  … +{len(updates) - 30} more")

    if apply:
        for cid, _, new in updates:
            c = db.get(Company, cid)
            if c:
                c.name = new
                stats.normalized_names += 1
        if stats.normalized_names:
            db.commit()
    else:
        stats.normalized_would_apply = len(updates)
    print(
        f"  Summary: normalized={stats.normalized_names} "
        f"(dry-run would={stats.normalized_would_apply})"
    )


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
    ap.add_argument("--skip-normalize", action="store_true", help="Skip trim/collapse-whitespace on names")
    ap.add_argument("--skip-names", action="store_true")
    ap.add_argument("--skip-industry", action="store_true")
    ap.add_argument("--skip-profiles", action="store_true")
    ap.add_argument(
        "--purge-junk-only",
        action="store_true",
        help="Purge phase: delete rows where is_junk() only (faster, narrower than full is_valid_lead)",
    )
    ap.add_argument(
        "--force-industry",
        action="store_true",
        help="Overwrite industry for every company (default: only fill empty/Unknown/Other/New)",
    )
    ap.add_argument("--limit-names", type=int, default=None, help="Max headline renames to process (safety)")
    args = ap.parse_args()
    apply = args.apply

    _exit_if_db_not_configured()

    if not apply:
        print(
            "DRY RUN — no writes. Pass --apply to execute.\n"
            "Large DBs: default purge uses is_valid_lead (slow); use --purge-junk-only for a fast is_junk scan.\n",
            flush=True,
        )

    db = SessionLocal()
    # With NullPool (Supabase session pooler), each commit closes the connection; default
    # expire_on_commit=True then forces lazy loads that reopen DB — fragile for long batches.
    db.expire_on_commit = False
    stats = Stats()
    try:
        if not args.skip_purge:
            phase_purge_junk(db, apply, stats, junk_only=args.purge_junk_only)
            db.expire_all()

        if not args.skip_normalize:
            print()
            phase_normalize_names(db, apply, stats)
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
