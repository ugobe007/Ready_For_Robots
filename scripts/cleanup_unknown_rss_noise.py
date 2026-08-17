#!/usr/bin/env python3
"""
Phase 4: audit Unknown-industry leads that fail name-based delete policy.

Default is dry-run:
  python3 scripts/cleanup_unknown_rss_noise.py

Delete after reviewing the CSV report (requires env):
  PIPELINE_HARD_DELETE_OK=1 python3 scripts/cleanup_unknown_rss_noise.py --apply --delete --yes

Only targets companies with industry empty / Unknown / Other / New AND a name that
fails is_junk or high-confidence headline entity classification.
RSS/HTML signal format alone is NOT a delete criterion.
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

from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.company import Company
from app.models.contact import Contact
from app.models.lead_rep_feedback import LeadRepFeedback
from app.models.score import Score
from app.models.signal import Signal
from app.services.lead_filter import is_junk
from app.services.pipeline_delete_policy import unknown_industry_delete_allowed
from app.services.scraper_blocklist import add_bulk_to_blocklist

_HARD_DELETE_ENV = "PIPELINE_HARD_DELETE_OK"


def _delete_company_rows(db, company_id: int) -> None:
    db.query(LeadRepFeedback).filter(LeadRepFeedback.company_id == company_id).delete(
        synchronize_session=False
    )
    db.query(Signal).filter(Signal.company_id == company_id).delete(synchronize_session=False)
    db.query(Score).filter(Score.company_id == company_id).delete(synchronize_session=False)
    db.query(Contact).filter(Contact.company_id == company_id).delete(synchronize_session=False)
    db.query(Company).filter(Company.id == company_id).delete(synchronize_session=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Purge Unknown RSS/headline noise leads")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--delete", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--report",
        default="",
        help="CSV path (default reports/unknown_rss_noise_cleanup_<ts>.csv)",
    )
    args = parser.parse_args()
    if args.delete and not args.apply:
        parser.error("--delete requires --apply")

    db = SessionLocal()
    candidates: list[dict] = []
    try:
        rows = (
            db.query(Company)
            .options(joinedload(Company.signals))
            .filter(
                (Company.industry == None)
                | (Company.industry == "")
                | (func.lower(Company.industry) == "unknown")
                | (func.lower(Company.industry) == "other")
                | (func.lower(Company.industry) == "new")
            )
            .order_by(Company.id)
            .all()
        )
        print(f"Scanning {len(rows)} unknown-industry companies...")
        for company in rows:
            junk_pair = is_junk(company.name or "")
            ok, reason, bucket = unknown_industry_delete_allowed(
                company.name,
                company.industry,
                company.signals or [],
                from_is_junk=junk_pair,
                company=company,
            )
            if not ok:
                continue
            sig_preview = ""
            if company.signals:
                sig_preview = (company.signals[0].signal_text or "")[:160]
            candidates.append(
                {
                    "company_id": company.id,
                    "name": company.name or "",
                    "industry": company.industry or "",
                    "bucket": bucket,
                    "reason": reason,
                    "signal_count": len(company.signals or []),
                    "signal_preview": sig_preview,
                }
            )

        buckets = Counter(c["bucket"] for c in candidates)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = Path(args.report or f"reports/unknown_rss_noise_cleanup_{ts}.csv")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(candidates[0].keys()) if candidates else [
                "company_id", "name", "industry", "bucket", "reason", "signal_count", "signal_preview",
            ])
            writer.writeheader()
            for row in candidates:
                writer.writerow(row)

        print(f"\nDelete candidates: {len(candidates)} of {len(rows)} unknown-industry rows")
        for key, count in buckets.most_common():
            print(f"  {count:5d}  {key}")
        print(f"Report: {report_path}")
        for row in candidates[:25]:
            print(f"  id={row['company_id']} [{row['bucket']}] {row['name']!r}")
        if len(candidates) > 25:
            print(f"  ... +{len(candidates) - 25} more")

        if not (args.apply and args.delete):
            print("\nDRY RUN — no rows deleted. Review CSV before any delete.")
            return

        if not os.environ.get(_HARD_DELETE_ENV):
            print(
                f"\nRefusing hard delete: set {_HARD_DELETE_ENV}=1 after CSV review.",
                file=sys.stderr,
            )
            sys.exit(2)

        to_delete = candidates
        if args.limit:
            to_delete = to_delete[: args.limit]
        if not args.yes:
            confirm = input(f"\nDelete {len(to_delete)} companies? Type 'yes': ")
            if confirm.strip().lower() != "yes":
                print("Aborted.")
                return

        names_blocklisted: list[str] = []
        for idx, row in enumerate(to_delete, start=1):
            _delete_company_rows(db, row["company_id"])
            if row["name"]:
                names_blocklisted.append(row["name"])
            if idx % 100 == 0:
                db.commit()
                print(f"  ...deleted {idx}/{len(to_delete)}")
        db.commit()
        if names_blocklisted:
            add_bulk_to_blocklist(names_blocklisted, reason="unknown_rss_noise_cleanup")
        print(f"\nDeleted {len(to_delete)} companies; blocklisted {len(names_blocklisted)} names.", flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
