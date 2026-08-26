"""Jobs CRM account API — keep, next-steps SKUs, apply, inbox. Prefix: /api/jobs-crm."""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth_deps import _require_user
from app.database import get_db
from app.services.jobs_crm import (
    apply_to_job,
    application_with_thread,
    catalog_skus_for_oem,
    keep_jobs,
    list_activity,
    list_kept_jobs,
    paste_inbound_reply,
    record_activity,
    reply_on_application,
)

router = APIRouter()


class KeepJobsBody(BaseModel):
    jobs: list[dict[str, Any]] = Field(default_factory=list)
    robot_name: Optional[str] = Field(default=None, max_length=240)
    robot_url: Optional[str] = Field(default=None, max_length=2000)
    robot_submission_id: Optional[int] = None


class ApplyBody(BaseModel):
    job_key: str = Field(..., min_length=1, max_length=160)
    robot_name: str = Field(..., min_length=1, max_length=240)
    selected_models: list[str] = Field(default_factory=list)
    monthly_price: str = Field(..., min_length=1, max_length=160)
    poc_evidence: Optional[str] = None
    poc_skipped: bool = False
    job: Optional[dict[str, Any]] = None


class ReplyBody(BaseModel):
    body: str = Field(..., min_length=1, max_length=20000)


class PasteInboundBody(BaseModel):
    body: str = Field(..., min_length=1, max_length=20000)
    from_email: Optional[str] = Field(default=None, max_length=320)


class ActivityBody(BaseModel):
    kind: str = Field(..., min_length=1, max_length=32)
    label: str = Field(..., min_length=1, max_length=240)
    job_key: Optional[str] = Field(default=None, max_length=160)
    company: Optional[str] = Field(default=None, max_length=240)


@router.post("/keep")
def post_keep_jobs(
    body: KeepJobsBody,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    if not body.jobs:
        raise HTTPException(status_code=400, detail="Select at least one Job Card to keep.")
    result = keep_jobs(
        db,
        user,
        body.jobs,
        robot_name=body.robot_name,
        robot_url=body.robot_url,
        robot_submission_id=body.robot_submission_id,
    )
    return result


@router.get("/jobs")
def get_kept_jobs(user: dict = Depends(_require_user), db: Session = Depends(get_db)):
    jobs = list_kept_jobs(db, user)
    return {"jobs": jobs, "saved_count": len(jobs)}


@router.get("/skus")
def get_catalog_skus(
    url: Optional[str] = Query(default=None, max_length=2000),
    company: Optional[str] = Query(default=None, max_length=240),
    user: dict = Depends(_require_user),
):
    del user
    skus = catalog_skus_for_oem(url=url, company_name=company)
    return {"skus": skus, "count": len(skus)}


@router.post("/apply")
def post_apply(
    body: ApplyBody,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        return apply_to_job(
            db,
            user,
            job_key=body.job_key,
            robot_name=body.robot_name,
            selected_models=body.selected_models,
            monthly_price=body.monthly_price,
            poc_evidence=body.poc_evidence or "",
            poc_skipped=body.poc_skipped,
            job=body.job,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/applications/{application_id}")
def get_application_thread(
    application_id: UUID,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        return application_with_thread(db, user, str(application_id))
    except KeyError:
        raise HTTPException(status_code=404, detail="Application not found.")


@router.post("/applications/{application_id}/reply")
def post_application_reply(
    application_id: UUID,
    body: ReplyBody,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        return reply_on_application(db, user, str(application_id), body.body)
    except KeyError:
        raise HTTPException(status_code=404, detail="Application not found.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/applications/{application_id}/paste-inbound")
def post_paste_inbound(
    application_id: UUID,
    body: PasteInboundBody,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        return paste_inbound_reply(
            db,
            user,
            str(application_id),
            body=body.body,
            from_email=body.from_email,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Application not found.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/activity")
def get_activity(
    job_key: Optional[str] = Query(default=None, max_length=160),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    return {"events": list_activity(db, user, job_key)}


@router.post("/activity")
def post_activity(
    body: ActivityBody,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    record_activity(
        db,
        user,
        kind=body.kind,
        label=body.label,
        job_key=body.job_key,
        company=body.company,
    )
    db.commit()
    return {"ok": True}
