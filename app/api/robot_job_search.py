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
        result = compose_robot_job_search(
            body.url,
            product=body.product,
            max_sources=body.max_sources,
            record_shadow=_shadow,
        )
        # Durable submitter ledger + funnel attribution (fail-open).
        try:
            from app.services.robot_submission_service import (
                record_robot_submission,
                record_submission_match,
            )

            profile_dict = result.get("profile") or {}
            row = record_robot_submission(
                db,
                url=body.url,
                company_name=result.get("company_name"),
                product_name=result.get("robot_name"),
                robot_class=result.get("robot_class"),
                profile_tier=profile_dict.get("profile_confidence"),
            )
            if row is not None:
                result["robot_submission_id"] = row.id
                record_submission_match(
                    db,
                    url=body.url,
                    capabilities=result.get("capabilities"),
                    job_count=result.get("job_count"),
                    source="robot_job_search",
                )
        except Exception:
            logger.exception("robot_submission_hook_failed")
        return result
    except UrlSafetyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("robot_job_search_failed")
        raise HTTPException(status_code=502, detail=f"job_search_failed: {e}") from e
