#!/usr/bin/env python3
"""Quarantine pipeline rows that are retail/QSR store openings, not automation buyers."""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from dotenv import load_dotenv

load_dotenv(_root / ".env")

from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.company import Company
from app.services.lead_filter import classify_lead
from app.services.pipeline_delete_policy import is_quarantined
from app.services.rectifier import quarantine


def main() -> int:
    parser = argparse.ArgumentParser(description="Quarantine weak retail store-opening leads")
    parser.add_argument("--apply", action="store_true", help="Set is_internal=False on matches")
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    db = SessionLocal()
    rows: list[tuple[int, str, str]] = []
    try:
        companies = (
            db.query(Company)
            .options(joinedload(Company.signals), joinedload(Company.scores))
            .filter(Company.is_internal.isnot(False))
            .limit(args.limit * 20)
            .all()
        )
        for company in companies:
            junk, reason, _pri = classify_lead(company, company.scores, company.signals)
            if not junk:
                continue
            low = (reason or "").lower()
            if "retail/qsr" not in low and "store opening" not in low:
                continue
            rows.append((company.id, company.name or "", reason))
            if len(rows) >= args.limit:
                break

        report = _root / "reports" / f"retail_store_quarantine_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        report.parent.mkdir(parents=True, exist_ok=True)
        with report.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["company_id", "name", "reason", "action"])
            for cid, name, reason in rows:
                action = "quarantine" if args.apply else "would_quarantine"
                w.writerow([cid, name, reason, action])
        print(f"Wrote {report}")
        print(f"Candidates: {len(rows)}")

        if args.apply:
            n = 0
            for cid, _name, reason in rows:
                company = db.query(Company).filter(Company.id == cid).first()
                if not company or is_quarantined(company):
                    continue
                quarantine(company, db, reason=reason)
                n += 1
            print(f"Quarantined: {n}")
        else:
            print("Dry-run — re-run with --apply to quarantine.")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
