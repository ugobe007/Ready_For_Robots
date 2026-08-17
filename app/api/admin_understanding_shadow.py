"""
Admin review loop for Understanding v1.0 observe-only production shadow.

Auth: X-Admin-Key or admin JWT (require_admin_jwt_or_key).

GET  /api/admin/understanding-shadow              — list recent observations
GET  /api/admin/understanding-shadow/metrics      — trust % + theme aggregates
GET  /api/admin/understanding-shadow/{id}         — one observation (+ snapshot)
POST /api/admin/understanding-shadow/{id}/review  — set GOOD|INCOMPLETE|WRONG|UNVERIFIABLE
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.admin_auth import require_admin_jwt_or_key
from app.database import get_db
from app.services.understanding_shadow import (
    REVIEW_LABELS,
    compute_trust_metrics,
    get_shadow_observation,
    list_shadow_observations,
    observation_to_summary,
    set_shadow_review,
)

router = APIRouter(
    prefix="/understanding-shadow",
    tags=["admin-understanding-shadow"],
    dependencies=[Depends(require_admin_jwt_or_key)],
)


class ShadowReviewIn(BaseModel):
    review_label: str = Field(..., description="GOOD | INCOMPLETE | WRONG | UNVERIFIABLE")
    review_notes: Optional[str] = Field(default=None, max_length=4000)
    failure_themes: Optional[list[str]] = Field(
        default=None,
        description="Optional tags: pdf, js_page, cn_oem, multi_product, sparse_startup, fetch_failure, identity, other",
    )
    reviewed_by: Optional[str] = Field(default=None, max_length=120)


@router.get("")
def list_shadow(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    review_label: Optional[str] = Query(None),
    unreviewed_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        rows = list_shadow_observations(
            db,
            limit=limit,
            offset=offset,
            review_label=review_label,
            unreviewed_only=unreviewed_only,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "items": [observation_to_summary(r) for r in rows],
        "limit": limit,
        "offset": offset,
        "review_labels": list(REVIEW_LABELS),
    }


@router.get("/metrics")
def shadow_metrics(db: Session = Depends(get_db)) -> dict[str, Any]:
    return compute_trust_metrics(db)


@router.get("/{observation_id}")
def get_shadow(observation_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    row = get_shadow_observation(db, observation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="shadow_observation_not_found")
    out = observation_to_summary(row)
    out["profile_snapshot"] = row.profile_snapshot
    return out


@router.post("/{observation_id}/review")
def review_shadow(
    observation_id: str,
    body: ShadowReviewIn,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin_jwt_or_key),
) -> dict[str, Any]:
    reviewed_by = body.reviewed_by or admin.get("email") or admin.get("auth")
    try:
        row = set_shadow_review(
            db,
            observation_id,
            review_label=body.review_label,
            review_notes=body.review_notes,
            failure_themes=body.failure_themes,
            reviewed_by=reviewed_by,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="shadow_observation_not_found") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return observation_to_summary(row)
