"""Public named-employer job preview for FIND home.

Anonymous GET. Live RobotJob rows only. Does not call Hunter, Apollo, or the
extract DAG. Does not invent names, emails, or payback.
"""
from __future__ import annotations

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


@router.get("/robot-jobs/preview")
def get_robot_jobs_preview(
    limit: int = Query(default=3, ge=1, le=_PREVIEW_CAP),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rows = select_daily_report_rows(db, limit=limit)
    jobs = [_public_job(row, rank) for rank, row in enumerate(rows, start=1)]
    return {"count": len(jobs), "limit": limit, "jobs": jobs}
