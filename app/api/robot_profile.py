"""
POST /api/robot-profile — Understanding v1 Phases 1–3.

Returns auditable Robot Profile JSON. No jobs.
Does not replace /api/robot-job-match.

Observe-only shadow: after a successful build, persist a shadow observation
(fail-open). Shadow never mutates the response payload or job-match results.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.robot_url_safety import UrlSafetyError
from app.services.robot_understanding_v1 import build_robot_profile
from app.services.understanding_shadow import record_shadow_observation

logger = logging.getLogger(__name__)

router = APIRouter(tags=["robot-profile"])


class RobotProfileIn(BaseModel):
    url: str = Field(..., max_length=2000)
    product: Optional[str] = Field(default=None, max_length=120)
    max_sources: int = Field(default=6, ge=1, le=12)
    correlation_id: Optional[str] = Field(default=None, max_length=64)


@router.post("/robot-profile")
def post_robot_profile(
    body: RobotProfileIn,
    db: Session = Depends(get_db),
    x_correlation_id: Optional[str] = Header(default=None, alias="X-Correlation-Id"),
) -> dict[str, Any]:
    correlation = (body.correlation_id or x_correlation_id or "").strip() or str(uuid.uuid4())
    t0 = time.perf_counter()
    try:
        profile = build_robot_profile(
            body.url,
            product_name=body.product,
            max_sources=body.max_sources,
        )
    except UrlSafetyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"profile_build_failed: {e}") from e

    duration_ms = int((time.perf_counter() - t0) * 1000)
    # Fail-open shadow write — never change or withhold the profile response.
    try:
        record_shadow_observation(
            db,
            profile,
            research_duration_ms=duration_ms,
            correlation_id=correlation,
        )
    except Exception:
        logger.exception("understanding_shadow_hook_failed")

    return profile.to_dict()
