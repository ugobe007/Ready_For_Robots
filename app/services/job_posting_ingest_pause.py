"""Pause for ingesting postings for people, split by source kind.

Paused unless PAUSE_JOB_POSTING_INGEST is explicitly "0". Under CLAUDE.md v2 a
posting for people may only become a labor-pressure signal on a company's
workflow, after checking whether the company already committed in that
workflow. That path does not exist yet, so nothing from a people-posting kind
may write companies, signals, robot_jobs, or sources.

Procurement kinds (tenders, RFPs, bids) are buyer signals and keep running.
A kind missing from FEED_CLASSIFICATION is treated as a people posting.
"""
from __future__ import annotations

import os

PEOPLE_POSTING = "people_posting"
BUYER_SIGNAL = "buyer_signal"

FEED_CLASSIFICATION: dict[str, str] = {
    "job_board": PEOPLE_POSTING,        # Indeed / SimplyHired HTML search pages
    "amazon_jobs": PEOPLE_POSTING,
    "greenhouse": PEOPLE_POSTING,
    "lever": PEOPLE_POSTING,
    "ashby": PEOPLE_POSTING,
    "smartrecruiters": PEOPLE_POSTING,
    "workday": PEOPLE_POSTING,
    "adzuna": PEOPLE_POSTING,
    "jooble": PEOPLE_POSTING,
    "usajobs": PEOPLE_POSTING,
    "sam_gov": BUYER_SIGNAL,            # federal solicitations / sources sought
}

PAUSED_RESULT = {"status": "paused", "reason": "PAUSE_JOB_POSTING_INGEST"}


def job_posting_ingest_paused() -> bool:
    return os.getenv("PAUSE_JOB_POSTING_INGEST", "1").strip().lower() not in ("0", "false", "no")


def source_kind_paused(kind: str) -> bool:
    if not job_posting_ingest_paused():
        return False
    return FEED_CLASSIFICATION.get(kind, PEOPLE_POSTING) == PEOPLE_POSTING
