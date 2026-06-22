#!/usr/bin/env python3
"""
Quarantine active companies that match known robotics OEM / vendor names.

Buyer-mode junk — these are manufacturers, not end-user deployment opportunities.
Soft-hide via ``is_internal=False`` (rectifier quarantine).

Dry-run (default):
  python3 scripts/quarantine_vendor_oem_leaks.py

Apply:
  python3 scripts/quarantine_vendor_oem_leaks.py --apply
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timezone
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

from app.database import SessionLocal
from app.models.company import Company
from app.services.lead_filter import is_junk
from app.services.pipeline_delete_policy import is_quarantined
from app.services.rectifier import quarantine

_VENDOR_REASON = "robotics vendor / OEM (not a buyer opportunity)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Quarantine robotics OEM/vendor company rows")
    parser.add_argument("--apply", action="store_true", help="Set is_internal=False on matches")
    parser.add_argument("--report", default="", help="Optional CSV path")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    db = SessionLocal()
    rows: list[tuple[int, str, str, bool]] = []
    try:
        q = db.query(Company).filter(Company.is_internal.is_(True)).order_by(Company.id)
        if args.limit:
            q = q.limit(args.limit)
        for company in q.all():
            name = (company.name or "").strip()
            if not name:
                continue
            junk, reason = is_junk(name, mode="buyer")
            if junk and reason == _VENDOR_REASON:
                rows.append((company.id, name, reason, is_quarantined(company)))
    finally:
        db.close()

    report_path = args.report or str(
        _root
        / "reports"
        / f"vendor_oem_quarantine_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    )
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["company_id", "name", "reason", "action"])
        for cid, name, reason, _ in rows:
            action = "quarantine" if args.apply else "would_quarantine"
            writer.writerow([cid, name, reason, action])

    print(f"Vendor/OEM quarantine candidates: {len(rows)}")
    print(f"Report: {report_path}")
    for cid, name, reason, _ in rows[:20]:
        print(f"  {cid}: {name!r} — {reason}")
    if len(rows) > 20:
        print(f"  ... and {len(rows) - 20} more")

    if not args.apply:
        print("Dry-run only. Re-run with --apply to quarantine.")
        return

    db = SessionLocal()
    applied = 0
    try:
        for cid, name, reason, _ in rows:
            company = db.query(Company).filter(Company.id == cid).first()
            if not company or is_quarantined(company):
                continue
            quarantine(company, db, reason=reason)
            applied += 1
        print(f"Quarantined: {applied}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
