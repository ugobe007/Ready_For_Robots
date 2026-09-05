#!/usr/bin/env python3
"""Remove stagegate_oem rows from companies — vendors belong in robot_companies, not buyer pipeline."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / ".env")

from app.database import SessionLocal
from app.models.company import Company
from app.models.contact import Contact
from app.models.lead_rep_feedback import LeadRepFeedback
from app.models.score import Score
from app.models.signal import Signal

COMPANY_SOURCE = "stagegate_oem"


def _delete_company_rows(db, company_id: int) -> None:
    db.query(LeadRepFeedback).filter(LeadRepFeedback.company_id == company_id).delete(
        synchronize_session=False
    )
    db.query(Signal).filter(Signal.company_id == company_id).delete(synchronize_session=False)
    db.query(Score).filter(Score.company_id == company_id).delete(synchronize_session=False)
    db.query(Contact).filter(Contact.company_id == company_id).delete(synchronize_session=False)
    db.query(Company).filter(Company.id == company_id).delete(synchronize_session=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete companies.source=stagegate_oem rows")
    parser.add_argument("--apply", action="store_true", help="Perform deletes (default dry-run)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        rows = (
            db.query(Company.id, Company.name)
            .filter(Company.source == COMPANY_SOURCE)
            .order_by(Company.id)
            .all()
        )
        print(f"stagegate_oem companies: {len(rows)}")
        for cid, name in rows[:20]:
            print(f"  id={cid} {name!r}")
        if len(rows) > 20:
            print(f"  ... +{len(rows) - 20} more")

        if not args.apply:
            print("\nDry-run — re-run with --apply to delete.")
            return 0

        for idx, (cid, _name) in enumerate(rows, start=1):
            _delete_company_rows(db, cid)
            if idx % 25 == 0:
                db.commit()
                print(f"  ...deleted {idx}/{len(rows)}")
        db.commit()
        print(f"\nDeleted {len(rows)} stagegate_oem companies.")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
