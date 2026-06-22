#!/usr/bin/env python3
"""
Strip RSS/HTML from signal_text on Unknown-industry companies.

Archives raw bodies to ``ingestion_raw_text`` when the column exists (same as
``cleanup_signal_text.py``), then normalizes ``signal_text``.

Dry-run (default):
  python3 scripts/strip_unknown_industry_signal_html.py

Apply:
  python3 scripts/strip_unknown_industry_signal_html.py --apply
  python3 scripts/strip_unknown_industry_signal_html.py --apply --limit 500
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

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

from sqlalchemy import func, inspect, or_
from sqlalchemy.orm import joinedload

from app.database import SessionLocal, engine
from app.models.company import Company
from app.models.signal import Signal
from app.services.automation_profile import build_automation_profile_dict_from_company
from app.services.lead_signal_display import normalize_signal_text_for_storage
from app.services.rss_noise_lead import signals_contain_google_rss_html


def _signals_has_ingestion_raw(eng) -> bool:
    insp = inspect(eng)
    try:
        cols = {c["name"] for c in insp.get_columns("signals")}
    except Exception:
        return False
    return "ingestion_raw_text" in cols


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize Unknown-industry signal HTML")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Max signals to rewrite")
    parser.add_argument("--since-id", type=int, default=None)
    args = parser.parse_args()

    has_raw = _signals_has_ingestion_raw(engine)
    db = SessionLocal()
    changed = 0
    scanned = 0
    company_ids: set[int] = set()
    try:
        q = (
            db.query(Signal)
            .join(Company, Signal.company_id == Company.id)
            .filter(
                or_(
                    Company.industry == None,
                    Company.industry == "",
                    func.lower(Company.industry) == "unknown",
                    func.lower(Company.industry) == "other",
                    func.lower(Company.industry) == "new",
                )
            )
            .order_by(Signal.id)
        )
        if args.since_id:
            q = q.filter(Signal.id >= args.since_id)
        if args.limit:
            q = q.limit(args.limit)

        for sig in q.all():
            scanned += 1
            raw = sig.signal_text or ""
            if not raw or not signals_contain_google_rss_html([sig]):
                continue
            cleaned = normalize_signal_text_for_storage(raw)
            if not cleaned or cleaned == raw.strip():
                continue
            changed += 1
            if args.apply:
                if has_raw and getattr(sig, "ingestion_raw_text", None) is None:
                    sig.ingestion_raw_text = raw
                sig.signal_text = cleaned
                company_ids.add(sig.company_id)
                if changed % 200 == 0:
                    db.commit()
                    print(f"  ...rewrote {changed} signals")

        if args.apply and changed:
            db.commit()
            for cid in sorted(company_ids):
                c = (
                    db.query(Company)
                    .options(joinedload(Company.signals))
                    .filter(Company.id == cid)
                    .first()
                )
                if c:
                    c.automation_profile = build_automation_profile_dict_from_company(c)
            db.commit()
    finally:
        db.close()

    print(f"Scanned {scanned} Unknown-industry signals; would rewrite {changed}")
    if not args.apply:
        print("Dry-run only. Re-run with --apply to persist.")
    else:
        print(f"Rewrote {changed} signals across {len(company_ids)} companies.")


if __name__ == "__main__":
    main()
