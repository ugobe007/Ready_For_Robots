"""Pause for ingesting people-hiring postings (job boards, ATS APIs, aggregators).

Paused unless PAUSE_JOB_POSTING_INGEST is explicitly "0". Under CLAUDE.md v2 a
posting for people may only become a labor-pressure signal on a company's
workflow, after checking whether the company already committed in that
workflow. That path does not exist yet, so nothing from these feeds may write
companies, signals, robot_jobs, or sources.
"""
from __future__ import annotations

import os

PAUSED_RESULT = {"status": "paused", "reason": "PAUSE_JOB_POSTING_INGEST"}


def job_posting_ingest_paused() -> bool:
    return os.getenv("PAUSE_JOB_POSTING_INGEST", "1").strip().lower() not in ("0", "false", "no")
