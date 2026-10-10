#!/usr/bin/env python3
"""Look up names/emails for a top-25 jobs JSON using Hunter + leadership pages.

Does not invent people. Writes a table to stdout and --out JSON.
FIND does not call this.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.robot_directed_discovery import RobotJob
from app.services.daily_jobs_hunter import enrich_daily_jobs_with_hunter
from app.services.daily_jobs_report import compose_daily_jobs_report
from app.services.hunter_client import HunterClient, hunter_contact_enabled


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _row(job: dict) -> RobotJob:
    now = datetime.now(timezone.utc)
    return RobotJob(
        id=uuid4(),
        job_key=str(job.get("job_key") or uuid4().hex[:24]),
        company_name=str(job.get("employer") or "").strip() or None,
        locality=str(job.get("locality") or "").strip() or None,
        action=str(job.get("action") or "").strip() or None,
        robot_compatible_task=str(job.get("title") or "").strip() or None,
        observed_workflow=str(job.get("description") or "").strip() or None,
        contact_url=str(job.get("contact_url") or "").strip() or None,
        apply_url=str(job.get("apply_url") or "").strip() or None,
        employer_email=str(job.get("employer_email") or "").strip() or None,
        investigate_status=str(job.get("investigate_status") or "weak"),
        existence_confidence=0.9,
        definition_completeness=0.8,
        created_at=now,
        updated_at=now,
        provenance={},
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jobs_json")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    payload = json.loads(open(args.jobs_json, encoding="utf-8").read())
    jobs = payload.get("jobs") if isinstance(payload, dict) else payload
    if not isinstance(jobs, list):
        print("expected a jobs list", file=sys.stderr)
        return 2
    if not hunter_contact_enabled():
        print("HUNTER_API_KEY missing", file=sys.stderr)
        return 2
    db = _session()
    for job in jobs[:25]:
        if isinstance(job, dict):
            db.add(_row(job))
    db.commit()
    hunter = enrich_daily_jobs_with_hunter(
        db, limit=25, client=HunterClient(), force=True, scrape_pages=True
    )
    report = compose_daily_jobs_report(db, limit=25)
    report["hunter"] = hunter
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
            fh.write("\n")
    print(
        f"looked_up={hunter.get('looked_up')} filled={hunter.get('filled')} "
        f"missed={hunter.get('missed')} skipped={hunter.get('skipped')}"
    )
    print()
    print(f"{'#':<3} {'employer':<42} {'name':<28} {'contact'}")
    for job in report.get("jobs") or []:
        name = str(job.get("decision_maker_name") or job.get("decision_maker") or "")
        contact = str(job.get("employer_email") or job.get("contact") or "")
        print(
            f"{job.get('rank') or 0:<3} {(job.get('employer') or '')[:42]:<42} "
            f"{name[:28]:<28} {contact}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
