"""V1 robot analysis HTTP endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.deps import require_v1_enabled
from app.api.v1.errors import SCHEMA_VERSION, V1HTTPException
from app.database import SessionLocal, get_db
from app.services.robot_analysis_service import (
    analysis_to_api,
    confirm_analysis,
    create_analysis,
    get_analysis_for_token,
    process_analysis,
)
from app.services.robot_url_safety import UrlSafetyError

router = APIRouter(prefix="/robot-analyses", tags=["v1-robot-analyses"])


class CreateRobotAnalysisIn(BaseModel):
    source_url: str | None = None
    description: str | None = Field(default=None, max_length=4000)


class ProfileCorrectionIn(BaseModel):
    field_path: str
    value: Any
    truth_state: str = "oem_verified"
    note: str | None = Field(default=None, max_length=1000)


class ConfirmRobotProfileIn(BaseModel):
    profile_etag: str
    corrections: list[ProfileCorrectionIn] = Field(default_factory=list)


def _process_in_background(analysis_id: str) -> None:
    db = SessionLocal()
    try:
        from app.models.robot_intelligence import RobotAnalysis

        analysis = db.query(RobotAnalysis).filter(RobotAnalysis.id == analysis_id).first()
        if not analysis:
            analysis = db.query(RobotAnalysis).filter(RobotAnalysis.id == str(analysis_id)).first()
        if analysis and analysis.status == "queued":
            process_analysis(db, analysis)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@router.post("", status_code=202)
def create_robot_analysis(
    body: CreateRobotAnalysisIn,
    background_tasks: BackgroundTasks,
    request: Request,
    response: Response,
    _: None = Depends(require_v1_enabled),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not body.source_url and not body.description:
        raise V1HTTPException(
            status_code=422,
            code="validation_error",
            message="Provide source_url or description",
            field_errors=[{"field": "source_url", "message": "required_unless_description"}],
        )
    scope = idempotency_key or request.client.host if request.client else "anon"
    try:
        # Inline processing keeps local/dev deterministic; background used when
        # V1_ANALYSIS_ASYNC=1.
        import os

        async_mode = os.getenv("V1_ANALYSIS_ASYNC", "").strip().lower() in {"1", "true", "yes"}
        analysis = create_analysis(
            db,
            source_url=body.source_url,
            description=body.description,
            requester_scope=scope,
            process_inline=not async_mode,
        )
        if async_mode and analysis.status == "queued":
            background_tasks.add_task(_process_in_background, str(analysis.id))
        db.commit()
        db.refresh(analysis)
    except UrlSafetyError as exc:
        db.rollback()
        raise V1HTTPException(status_code=422, code="unsafe_url", message=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise V1HTTPException(status_code=422, code="validation_error", message=str(exc)) from exc

    response.headers["Location"] = f"/api/v1/robot-analyses/{analysis.id}"
    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_id": str(analysis.id),
        "analysis_token": analysis.analysis_token,
        "status": "queued" if async_mode else analysis.status,
        "status_url": f"/api/v1/robot-analyses/{analysis.id}",
    }


@router.get("/{analysis_id}")
def get_robot_analysis(
    analysis_id: str,
    _: None = Depends(require_v1_enabled),
    db: Session = Depends(get_db),
    x_analysis_token: str | None = Header(default=None, alias="X-Analysis-Token"),
):
    analysis = get_analysis_for_token(db, analysis_id, x_analysis_token)
    if x_analysis_token and analysis is None:
        # Token provided but mismatch — hide existence.
        raise V1HTTPException(status_code=404, code="not_found", message="Analysis not found")
    if analysis is None:
        # Public read by id for Slice 1 (token optional); still 404 if missing.
        from app.models.robot_intelligence import RobotAnalysis

        analysis = db.query(RobotAnalysis).filter(RobotAnalysis.id == analysis_id).first()
        if not analysis:
            analysis = db.query(RobotAnalysis).filter(RobotAnalysis.id == str(analysis_id)).first()
    if not analysis:
        raise V1HTTPException(status_code=404, code="not_found", message="Analysis not found")
    return analysis_to_api(analysis)


@router.post("/{analysis_id}/confirm")
def confirm_robot_analysis(
    analysis_id: str,
    body: ConfirmRobotProfileIn,
    _: None = Depends(require_v1_enabled),
    db: Session = Depends(get_db),
    x_analysis_token: str | None = Header(default=None, alias="X-Analysis-Token"),
):
    analysis = get_analysis_for_token(db, analysis_id, x_analysis_token)
    if analysis is None:
        from app.models.robot_intelligence import RobotAnalysis

        analysis = db.query(RobotAnalysis).filter(RobotAnalysis.id == analysis_id).first()
        if not analysis:
            analysis = db.query(RobotAnalysis).filter(RobotAnalysis.id == str(analysis_id)).first()
    if not analysis:
        raise V1HTTPException(status_code=404, code="not_found", message="Analysis not found")
    if x_analysis_token and analysis.analysis_token != x_analysis_token:
        raise V1HTTPException(status_code=404, code="not_found", message="Analysis not found")
    try:
        result = confirm_analysis(
            db,
            analysis,
            profile_etag=body.profile_etag,
            corrections=[c.model_dump() for c in body.corrections],
        )
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        message = str(exc)
        code = "conflict" if "already confirmed" in message or "etag" in message.lower() else "validation_error"
        status = 409 if code == "conflict" else 422
        raise V1HTTPException(status_code=status, code=code, message=message) from exc
