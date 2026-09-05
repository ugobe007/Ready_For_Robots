#!/usr/bin/env python3
"""
Rescue active Unknown-industry rows via ontology map + inference; quarantine headline stubs.

Dry-run (default):
  python3 scripts/rescue_unknown_industry_ontology.py

Apply industry updates + quarantine:
  python3 scripts/rescue_unknown_industry_ontology.py --apply
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)

from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.company import Company
from app.services.pipeline_delete_policy import is_quarantined
from app.services.rectifier import quarantine
from app.services.unknown_industry_rescue import unknown_industry_rescue_action

_cleanup_dotenv = (os.getenv("DOTENV_PATH") or "").strip()
if _cleanup_dotenv:
    load_dotenv(Path(_cleanup_dotenv).expanduser(), override=True)
_loaded_after_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded_after_dotenv):
    os.environ["DATABASE_URL"] = _shell_database_url


def main() -> None:
    parser = argparse.ArgumentParser(description="Rescue Unknown industry via ontology")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", default="")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    db = SessionLocal()
    rows: list[dict] = []
    try:
        q = (
            db.query(Company)
            .options(joinedload(Company.signals))
            .filter(Company.is_internal.is_(True))
            .filter(
                or_(
                    Company.industry == None,
                    Company.industry == "",
                    func.lower(Company.industry) == "unknown",
                    func.lower(Company.industry) == "other",
                    func.lower(Company.industry) == "new",
                )
            )
            .order_by(Company.id)
        )
        if args.limit:
            q = q.limit(args.limit)
        companies = [c for c in q.all() if c.signals]
        print(f"Scanning {len(companies)} active Unknown-industry companies with signals...")

        for company in companies:
            action, value, reason = unknown_industry_rescue_action(
                company.name,
                company.industry,
                company.signals or [],
            )
            if action == "skip":
                continue
            rows.append(
                {
                    "company_id": company.id,
                    "name": company.name or "",
                    "action": action,
                    "value": value,
                    "reason": reason,
                }
            )
    finally:
        db.close()

    actions = Counter(r["action"] for r in rows)
    report_path = args.report or str(
        _root
        / "reports"
        / f"unknown_industry_rescue_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    )
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["company_id", "name", "action", "value", "reason", "applied"]
        )
        writer.writeheader()
        for row in rows:
            row["applied"] = "yes" if args.apply else "dry_run"
            writer.writerow(row)

    print(f"Rescue actions: {len(rows)}")
    for key, count in actions.most_common():
        print(f"  {count:5d}  {key}")
    print(f"Report: {report_path}")
    for row in rows[:15]:
        print(f"  {row['company_id']}: [{row['action']}] {row['name']!r} → {row['value'] or row['reason'][:50]}")
    if len(rows) > 15:
        print(f"  ... and {len(rows) - 15} more")

    if not args.apply:
        print("Dry-run only. Re-run with --apply to persist.")
        return

    db = SessionLocal()
    applied_ind = 0
    quarantined = 0
    try:
        for row in rows:
            company = db.query(Company).filter(Company.id == row["company_id"]).first()
            if not company or is_quarantined(company):
                continue
            if row["action"] == "apply":
                company.industry = row["value"]
                applied_ind += 1
            elif row["action"] == "quarantine":
                quarantine(company, db, reason=row["reason"])
                quarantined += 1
            if (applied_ind + quarantined) % 50 == 0:
                db.commit()
        db.commit()
        print(f"Industries applied: {applied_ind}; quarantined: {quarantined}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
