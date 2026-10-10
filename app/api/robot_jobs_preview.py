"""Public named-employer job preview for FIND home.

Anonymous GET. Live RobotJob rows when the table has named employers.
If that table is empty, named-employer corpus rows so the home board is
not blank. Does not invent names, emails, or payback.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.daily_jobs_report import (
    CONTACT_EMPTY,
    CONTACT_HUNTER_MISS,
    DECISION_MAKER_EMPTY,
    DECISION_MAKER_HUNTER_MISS,
    _serialize_job,
    select_daily_report_rows,
)
from app.services.robot_job_extract import is_job_employer_name
from app.services.robot_requirement_match import is_named_robot_job

_CORPUS_PATH = Path(__file__).resolve().parents[1] / "data" / "robot_job_match_corpus.json"

router = APIRouter(tags=["robot-jobs-preview"])

_PREVIEW_CAP = 8


def _public_job(row: Any, rank: int) -> dict[str, Any]:
    data = _serialize_job(row, rank)
    contact_source = str(data.get("contact_source") or "").strip().lower()
    is_hunter = contact_source.startswith("hunter") or contact_source == "decision_maker_agent"
    
    if is_hunter:
        decision = DECISION_MAKER_EMPTY
        contact = CONTACT_EMPTY
    else:
        decision = str(data.get("decision_maker") or "").strip()
        if decision == DECISION_MAKER_HUNTER_MISS:
            decision = DECISION_MAKER_EMPTY
        contact = str(data.get("contact") or "").strip()
        if contact == CONTACT_HUNTER_MISS:
            contact = CONTACT_EMPTY
    
    return {
        "job_key": data.get("job_key") or "",
        "employer": data.get("employer") or "",
        "workplace": data.get("locality") or "",
        "work": data.get("job_type") or data.get("title") or "",
        "description": data.get("description") or "",
        "timing": data.get("timing") or "",
        "decision_maker": decision,
        "contact": contact,
    }


def corpus_preview_jobs(limit: int) -> list[dict[str, Any]]:
    """Named-employer corpus rows with no invented people or mailboxes."""
    cap = max(1, min(int(limit), _PREVIEW_CAP))
    try:
        payload = json.loads(_CORPUS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    out: list[dict[str, Any]] = []
    for raw in payload.get("jobs") or []:
        if not isinstance(raw, dict):
            continue
        employer = str(raw.get("company_name") or "").strip()
        locality = str(raw.get("locality") or "").strip()
        title = str(raw.get("title") or "").strip()
        key = str(raw.get("job_key") or "").strip()
        if not key or not title:
            continue
        if not is_named_robot_job(employer, locality):
            continue
        if not is_job_employer_name(employer, title=title):
            continue
        out.append(
            {
                "job_key": key,
                "employer": employer,
                "workplace": locality,
                "work": title,
                "description": "",
                "timing": "",
                "decision_maker": DECISION_MAKER_EMPTY,
                "contact": CONTACT_EMPTY,
            }
        )
        if len(out) >= cap:
            break
    return out


@router.get("/robot-jobs/preview")
def get_robot_jobs_preview(
    limit: int = Query(default=3, ge=1, le=_PREVIEW_CAP),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rows = select_daily_report_rows(db, limit=limit)
    jobs = [_public_job(row, rank) for rank, row in enumerate(rows, start=1)]
    source = "live"
    if not jobs:
        jobs = corpus_preview_jobs(limit)
        source = "corpus"
    return {"count": len(jobs), "limit": limit, "source": source, "jobs": jobs}
