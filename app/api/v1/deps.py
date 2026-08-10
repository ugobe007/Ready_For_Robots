"""V1 feature-flag and dependency helpers."""
from __future__ import annotations

from app.api.v1.errors import V1HTTPException
from app.config import Config


def v1_robot_intelligence_enabled() -> bool:
    return bool(getattr(Config, "V1_ROBOT_INTELLIGENCE", False))


def require_v1_enabled() -> None:
    """Gate all /api/v1 routes until the flag is on."""
    if not v1_robot_intelligence_enabled():
        raise V1HTTPException(
            status_code=404,
            code="v1_disabled",
            message="V1 robot intelligence API is not enabled",
            retryable=False,
        )
