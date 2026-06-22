#!/usr/bin/env python3
"""
Quarantine Unknown-industry RSS / market-report noise (soft-hide, not hard delete).

Targets rows where the name is junk, a market-report headline, or classify_lead
marks display junk — but spares known brands and names that map to real industries
(e.g. Novartis → Medical Technology).

Dry-run (default):
  python3 scripts/quarantine_unknown_rss_noise.py

Apply:
  python3 scripts/quarantine_unknown_rss_noise.py --apply
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
_cleanup_dotenv = (os.getenv("DOTENV_PATH") or "").strip()
if _cleanup_dotenv:
    load_dotenv(Path(_cleanup_dotenv).expanduser(), override=True)
_loaded_after_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded_after_dotenv):
    os.environ["DATABASE_URL"] = _shell_database_url

from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.company import Company
from app.services.lead_filter import classify_lead, is_junk
from app.services.pipeline_delete_policy import is_quarantined, unknown_rss_noise_quarantine_allowed
from app.services.rectifier import quarantine


def main() -> None:
    parser = argparse.ArgumentParser(description="Quarantine Unknown RSS/market-report noise")
    parser.add_argument("--apply", action="store_true", help="Set is_internal=False on matches")
    parser.add_argument("--report", default="", help="Optional CSV path")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    db = SessionLocal()
    rows: list[tuple[int, str, str, str, bool]] = []
    try:
        q = (
            db.query(Company)
            .options(joinedload(Company.signals), joinedload(Company.scores))
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
        companies = q.all()
        print(f"Scanning {len(companies)} active Unknown-industry companies...")

        for company in companies:
            name = (company.name or "").strip()
            if not name:
                continue
            sigs = company.signals or []
            junk_pair = is_junk(name)
            classify_pair = classify_lead(company, company.scores, sigs)
            ok, reason, bucket = unknown_rss_noise_quarantine_allowed(
                name,
                company.industry,
                sigs,
                from_is_junk=junk_pair,
                from_classify=classify_pair,
            )
            if ok:
                rows.append((company.id, name, bucket, reason, is_quarantined(company)))
    finally:
        db.close()

    buckets = Counter(bucket for _, _, bucket, _, _ in rows)
    report_path = args.report or str(
        _root
        / "reports"
        / f"unknown_rss_quarantine_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    )
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["company_id", "name", "bucket", "reason", "action"])
        for cid, name, bucket, reason, _ in rows:
            action = "quarantine" if args.apply else "would_quarantine"
            writer.writerow([cid, name, bucket, reason, action])

    print(f"Quarantine candidates: {len(rows)}")
    for key, count in buckets.most_common():
        print(f"  {count:5d}  {key}")
    print(f"Report: {report_path}")
    for cid, name, bucket, reason, _ in rows[:15]:
        print(f"  {cid}: [{bucket}] {name!r} — {reason[:70]}")
    if len(rows) > 15:
        print(f"  ... and {len(rows) - 15} more")

    if not args.apply:
        print("Dry-run only. Re-run with --apply to quarantine.")
        return

    db = SessionLocal()
    applied = 0
    try:
        for cid, name, bucket, reason, _ in rows:
            company = db.query(Company).filter(Company.id == cid).first()
            if not company or is_quarantined(company):
                continue
            quarantine(company, db, reason=reason)
            applied += 1
            if applied % 100 == 0:
                db.commit()
        db.commit()
        print(f"Quarantined: {applied}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
