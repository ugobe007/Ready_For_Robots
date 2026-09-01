"""Employer MATCH + post-job draft. Prefix: /api.

POST /api/employer-robot-match — work class → named catalog robots.
POST /api/employer-job-draft — persist onto robot_jobs after they saw matches.
No invented emails. No SIGNAL. Not Cal.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.employer_robot_match import EMPTY_COPY, match_catalog_robots
from app.services.robot_job_extract import job_function_from_title
from app.services.robot_job_lifecycle import upsert_robot_job_from_extract

router = APIRouter(tags=["employer-jobs"])


class EmployerRobotMatchIn(BaseModel):
    work_class: Optional[str] = Field(default=None, max_length=40)
    description: Optional[str] = Field(default=None, max_length=4000)
    job_url: Optional[str] = Field(default=None, max_length=2000)


class EmployerJobDraftIn(BaseModel):
    employer: str = Field(..., max_length=240)
    title: str = Field(..., max_length=200)
    workplace: Optional[str] = Field(default=None, max_length=240)
    description: Optional[str] = Field(default=None, max_length=4000)
    work_class: Optional[str] = Field(default=None, max_length=40)
    job_url: Optional[str] = Field(default=None, max_length=2000)
    shortlisted: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/employer-robot-match")
def post_employer_robot_match(body: EmployerRobotMatchIn) -> dict[str, Any]:
    return match_catalog_robots(
        work_class=body.work_class,
        description=body.description,
        limit=12,
    )


@router.post("/employer-job-draft")
def post_employer_job_draft(
    body: EmployerJobDraftIn,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    employer = (body.employer or "").strip()
    title = (body.title or "").strip()
    if not employer or not title:
        return {
            "ok": False,
            "persisted": False,
            "job_key": None,
            "detail": "Name the employer and the work. We will not invent either.",
        }
    extract: dict[str, Any] = {
        "employer": employer,
        "job_title": title,
        "workplace": (body.workplace or "").strip() or None,
        "job_function": job_function_from_title(title),
        "status": "open",
        "industry_id": (body.work_class or "").strip() or None,
        "work_language_terms": [body.work_class] if body.work_class else [],
        "unknowns": [],
    }
    if body.description:
        extract["unknowns"] = []
        extract["job_function"] = extract["job_function"] or "work"
    try:
        row = upsert_robot_job_from_extract(
            db,
            company_id=None,
            extract=extract,
            source_url=(body.job_url or "").strip() or None,
        )
        if row is None:
            return {
                "ok": False,
                "persisted": False,
                "job_key": None,
                "detail": (
                    "We could not store this posting. Check the employer name "
                    "is a real company, not a board or a robot SKU."
                ),
            }
        db.commit()
        return {
            "ok": True,
            "persisted": True,
            "job_key": getattr(row, "job_key", None),
            "empty_copy": EMPTY_COPY,
            "detail": None,
        }
    except Exception:
        db.rollback()
        return {
            "ok": False,
            "persisted": False,
            "job_key": None,
            "detail": "Could not store this posting right now. Your shortlist is still on this device.",
        }
