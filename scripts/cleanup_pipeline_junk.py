#!/usr/bin/env python3
"""
Pipeline junk audit — report rows that fail the canonical hard-delete policy.

IMPORTANT: Prefer ``scripts/cleanup_leads.py`` for production cleanup.
Hard delete is only allowed when ``is_valid_lead(name)`` fails — same gate as
``cleanup_leads.py`` phase 1. This script never deletes for:
  - rectifier quarantine (is_internal=False)
  - RSS/HTML signal format
  - classify_lead buyer-opportunity display junk

Default dry-run (CSV report only):
  python3 scripts/cleanup_pipeline_junk.py

Hard delete (requires env + flags):
  PIPELINE_HARD_DELETE_OK=1 python3 scripts/cleanup_pipeline_junk.py --apply --delete --yes

Optional: pass --blocklist to add deleted names to scraper blocklist (default off).
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter
from dataclasses import dataclass
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

from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.company import Company
from app.models.contact import Contact
from app.models.lead_rep_feedback import LeadRepFeedback
from app.models.score import Score
from app.models.signal import Signal
from app.services.lead_filter import classify_lead
from app.services.pipeline_delete_policy import hard_delete_allowed, is_quarantined
from app.services.scraper_blocklist import add_bulk_to_blocklist

_HARD_DELETE_ENV = "PIPELINE_HARD_DELETE_OK"


@dataclass
class JunkCandidate:
    company_id: int
    name: str
    industry: str
    bucket: str
    reason: str
    signal_count: int
    audit_note: str = ""


def _delete_company_rows(db, company_id: int) -> None:
    db.query(LeadRepFeedback).filter(LeadRepFeedback.company_id == company_id).delete(
        synchronize_session=False
    )
    db.query(Signal).filter(Signal.company_id == company_id).delete(synchronize_session=False)
    db.query(Score).filter(Score.company_id == company_id).delete(synchronize_session=False)
    db.query(Contact).filter(Contact.company_id == company_id).delete(synchronize_session=False)
    db.query(Company).filter(Company.id == company_id).delete(synchronize_session=False)


def _pipeline_junk_bucket(company: Company) -> tuple[bool, str, str, str]:
    """
    Returns (hard_delete, reason, bucket, audit_note).

    ``audit_note`` captures display-tier junk that must NOT be hard-deleted.
    """
    allowed, reason, bucket = hard_delete_allowed(company, company.signals or [])
    if allowed:
        return True, reason, bucket, ""

    if is_quarantined(company):
        return False, "", "", "quarantined — hidden from API; do not delete"

    junk_c, reason_c, _ = classify_lead(company, company.scores, company.signals or [])
    if junk_c:
        return False, reason_c, "display_junk", "classify_lead junk — keep in DB; run secondary pass"

    return False, "", "", ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit pipeline hard-delete candidates (policy-aligned with cleanup_leads.py)"
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--delete", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--report", default="")
    parser.add_argument(
        "--blocklist",
        action="store_true",
        help="Add deleted names to scraper blocklist (default: off)",
    )
    args = parser.parse_args()
    if args.delete and not args.apply:
        parser.error("--delete requires --apply")

    db = SessionLocal()
    hard_delete_candidates: list[JunkCandidate] = []
    audit_rows: list[JunkCandidate] = []
    try:
        rows = (
            db.query(Company)
            .options(joinedload(Company.signals), joinedload(Company.scores))
            .order_by(Company.id)
            .all()
        )
        print(f"Scanning {len(rows)} pipeline companies...")
        print("Policy: hard delete only when is_valid_lead(name) fails.")
        print("        Prefer scripts/cleanup_leads.py for production cleanup.\n")

        for company in rows:
            ok, reason, bucket, note = _pipeline_junk_bucket(company)
            row = JunkCandidate(
                company_id=company.id,
                name=company.name or "",
                industry=company.industry or "",
                bucket=bucket or "ok",
                reason=reason or note,
                signal_count=len(company.signals or []),
                audit_note=note,
            )
            if ok:
                hard_delete_candidates.append(row)
            elif note:
                audit_rows.append(row)

        buckets = Counter(c.bucket for c in hard_delete_candidates)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = Path(args.report or f"reports/pipeline_junk_cleanup_{ts}.csv")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "company_id",
                    "name",
                    "industry",
                    "bucket",
                    "reason",
                    "signal_count",
                    "audit_note",
                ],
            )
            writer.writeheader()
            for c in hard_delete_candidates + audit_rows:
                writer.writerow(c.__dict__)

        print(f"Hard-delete candidates: {len(hard_delete_candidates)} of {len(rows)}")
        for key, count in buckets.most_common():
            print(f"  {count:5d}  {key}")
        print(f"Display/quarantine audit rows (NOT deleted): {len(audit_rows)}")
        print(f"Report: {report_path}")
        for c in hard_delete_candidates[:20]:
            print(f"  DELETE id={c.company_id} [{c.bucket}] {c.name!r}")
        if len(hard_delete_candidates) > 20:
            print(f"  ... +{len(hard_delete_candidates) - 20} more hard-delete candidates")

        if not (args.apply and args.delete):
            print("\nDRY RUN — no rows deleted.")
            print("Use scripts/cleanup_leads.py --apply for the canonical cleanup pipeline.")
            return

        if not os.environ.get(_HARD_DELETE_ENV):
            print(
                f"\nRefusing hard delete: set {_HARD_DELETE_ENV}=1 after CSV review.",
                file=sys.stderr,
            )
            sys.exit(2)

        to_delete = hard_delete_candidates
        if args.limit:
            to_delete = to_delete[: args.limit]
        if not args.yes:
            confirm = input(f"\nDelete {len(to_delete)} companies? Type 'yes': ")
            if confirm.strip().lower() != "yes":
                print("Aborted.")
                return

        names: list[str] = []
        for idx, c in enumerate(to_delete, start=1):
            _delete_company_rows(db, c.company_id)
            if args.blocklist and c.name:
                names.append(c.name)
            if idx % 100 == 0:
                db.commit()
                print(f"  ...deleted {idx}/{len(to_delete)}", flush=True)
        db.commit()
        if names:
            add_bulk_to_blocklist(names, reason="pipeline_junk_cleanup")
        print(f"\nDeleted {len(to_delete)} invalid-name companies.")
        if args.blocklist:
            print(f"Blocklisted {len(names)} names.")
        else:
            print("Blocklist unchanged (pass --blocklist to add names).")
        print(f"Remaining companies: {len(rows) - len(to_delete)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
