#!/usr/bin/env python3
"""Re-parse stored Robot Job evidence for employer emails — page only.

Posting HTML is **not** stored. ``job_evidence.excerpt`` is the ROBOT_JOB
signal line (title / function / pay), not the Indeed/JSON-LD page. This
script therefore cannot recover mailboxes for the existing 1,664 rows.

What it does:
  - Scan ``robot_jobs.requirements`` + ``job_evidence.excerpt`` for emails
    that were already captured (mailto / JSON-LD) and copy them onto
    ``employer_email`` when the column exists.
  - Report how many rows still have no mailbox.

What it does **not** do:
  - Guess ``info@`` / ``careers@`` from the employer name
  - Scrape LinkedIn, Apollo, Hunter, or SIGNAL buyer lists
  - Re-fetch job-board URLs (that is a new scrape, not a backfill)

New job-board scrapes fill ``employer_email`` going forward.

  PYTHONPATH=. python3 scripts/backfill_robot_job_contacts.py
  PYTHONPATH=. python3 scripts/backfill_robot_job_contacts.py --apply

Fly leftover: ``alembic upgrade head`` (revision ``jcnt0a1b2c3d4``).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.robot_job_extract import extract_job_contacts, is_board_mailbox
from app.services.email_address import normalize_recipient_email


def _email_from_row(row) -> str | None:
    hit = normalize_recipient_email(getattr(row, "employer_email", None))
    if hit and not is_board_mailbox(hit):
        return hit
    req = getattr(row, "requirements", None) or {}
    if isinstance(req, dict):
        hit = normalize_recipient_email(req.get("employer_email"))
        if hit and not is_board_mailbox(hit):
            return hit
    return None


def _email_from_excerpt(excerpt: str | None) -> str | None:
    if not excerpt:
        return None
    contacts = extract_job_contacts(html=excerpt, description=excerpt)
    return contacts.get("employer_email")


def run(*, apply: bool) -> dict[str, int]:
    from sqlalchemy import inspect as sa_inspect

    from app.database import SessionLocal
    from app.models.robot_directed_discovery import JobEvidence, RobotJob

    stats = {
        "jobs": 0,
        "already_had_email": 0,
        "filled_from_requirements": 0,
        "filled_from_excerpt": 0,
        "still_empty": 0,
        "html_stored": 0,
        "columns_present": 0,
    }
    db = SessionLocal()
    try:
        bind = db.get_bind()
        cols = {c["name"] for c in sa_inspect(bind).get_columns("robot_jobs")}
        stats["columns_present"] = int("employer_email" in cols)
        if "employer_email" not in cols:
            print(
                "robot_jobs.employer_email is missing. "
                "Fly leftover: alembic upgrade head (jcnt0a1b2c3d4)."
            )
        jobs = db.query(RobotJob).all()
        stats["jobs"] = len(jobs)
        for row in jobs:
            existing = _email_from_row(row)
            if existing:
                stats["already_had_email"] += 1
                req = dict(row.requirements or {})
                if apply and "employer_email" in cols and not getattr(row, "employer_email", None):
                    row.employer_email = existing
                    stats["filled_from_requirements"] += 1
                if existing != req.get("employer_email"):
                    req["employer_email"] = existing
                    if apply:
                        row.requirements = req
                continue
            excerpts = (
                db.query(JobEvidence.excerpt)
                .filter(JobEvidence.robot_job_id == row.id)
                .all()
            )
            found = None
            for (excerpt,) in excerpts:
                found = _email_from_excerpt(excerpt)
                if found:
                    break
            if found:
                stats["filled_from_excerpt"] += 1
                if apply:
                    req = dict(row.requirements or {})
                    req["employer_email"] = found
                    row.requirements = req
                    if "employer_email" in cols:
                        row.employer_email = found
            else:
                stats["still_empty"] += 1
        if apply:
            db.commit()
        else:
            db.rollback()
    finally:
        db.close()
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write recovered emails. Default is dry-run.",
    )
    args = parser.parse_args()
    stats = run(apply=args.apply)
    mode = "apply" if args.apply else "dry-run"
    print(f"backfill_robot_job_contacts ({mode}): {stats}")
    print(
        "Posting HTML is not stored (html_stored=0). "
        "New job-board scrapes fill employer_email going forward. "
        "This is not LinkedIn/Apollo/Hunter enrichment."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
