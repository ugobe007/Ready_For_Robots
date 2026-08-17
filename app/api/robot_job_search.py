"""
POST /api/robot-job-search — one composed URL → profile → jobs transaction.

The UI must not stream this progressively. Reveal once when this returns.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.robot_job_search import compose_robot_job_search
from app.services.robot_url_safety import UrlSafetyError
from app.services.understanding_shadow import record_shadow_observation

logger = logging.getLogger(__name__)

router = APIRouter(tags=["robot-job-search"])


class RobotJobSearchIn(BaseModel):
    url: str = Field(..., max_length=2000)
    product: Optional[str] = Field(default=None, max_length=120)
    max_sources: int = Field(default=6, ge=1, le=12)
    correlation_id: Optional[str] = Field(default=None, max_length=64)


@router.post("/robot-job-search")
def post_robot_job_search(
    body: RobotJobSearchIn,
    db: Session = Depends(get_db),
    x_correlation_id: Optional[str] = Header(default=None, alias="X-Correlation-Id"),
) -> dict[str, Any]:
    correlation = (body.correlation_id or x_correlation_id or "").strip() or str(uuid.uuid4())

    def _shadow(profile_obj, duration_ms: int) -> None:
        record_shadow_observation(
            db,
            profile_obj,
            research_duration_ms=duration_ms,
            correlation_id=correlation,
        )

    try:
        return compose_robot_job_search(
            body.url,
            product=body.product,
            max_sources=body.max_sources,
            record_shadow=_shadow,
        )
    except UrlSafetyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("robot_job_search_failed")
        raise HTTPException(status_code=502, detail=f"job_search_failed: {e}") from e
