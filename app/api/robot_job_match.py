"""
Public robot → jobs capability match (homepage / jobs front door).

POST /api/robot-job-match
  { "url": "https://…", "chip": "manipulates" | null }

No V1 feature flag — this is the product front-door path.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.robot_job_capability_match import match_from_chip, match_robot_url
from app.services.robot_url_safety import UrlSafetyError

router = APIRouter(tags=["robot-job-match"])

ChipLiteral = Literal["moves_materials", "manipulates", "cleans", "inspects", "other"]


class RobotJobMatchIn(BaseModel):
    url: Optional[str] = Field(default=None, max_length=2000)
    chip: Optional[ChipLiteral] = None
    robot_name: Optional[str] = Field(default=None, max_length=120)


class RobotJobMatchOut(BaseModel):
    state: Literal["matches", "thin_corpus", "could_not_understand"]
    robot_name: str
    capabilities: list[dict[str, Any]]
    families: list[dict[str, Any]]
    jobs: list[dict[str, Any]]
    job_count: int
    source_url: Optional[str] = None


@router.post("/robot-job-match", response_model=RobotJobMatchOut)
def post_robot_job_match(body: RobotJobMatchIn) -> dict[str, Any]:
    url = (body.url or "").strip()
    chip = body.chip

    if not url and not chip:
        return {
            "state": "could_not_understand",
            "robot_name": body.robot_name or "your robot",
            "capabilities": [],
            "families": [],
            "jobs": [],
            "job_count": 0,
            "source_url": None,
        }

    try:
        if chip and not url:
            result = match_from_chip(chip, robot_name=body.robot_name or "your robot")
        else:
            result = match_robot_url(url, chip=chip)
    except UrlSafetyError as exc:
        return {
            "state": "could_not_understand",
            "robot_name": body.robot_name or "your robot",
            "capabilities": [],
            "families": [],
            "jobs": [],
            "job_count": 0,
            "source_url": None,
            "error": str(exc),
        }
    except Exception:
        # Network / parse failure — recoverable, not a fake empty library
        if chip:
            result = match_from_chip(chip, robot_name=body.robot_name or "your robot")
        else:
            return {
                "state": "could_not_understand",
                "robot_name": body.robot_name or "your robot",
                "capabilities": [],
                "families": [],
                "jobs": [],
                "job_count": 0,
                "source_url": url or None,
            }

    return {
        "state": result["state"],
        "robot_name": result["robot_name"],
        "capabilities": result.get("capabilities") or [],
        "families": result.get("families") or [],
        "jobs": result.get("jobs") or [],
        "job_count": int(result.get("job_count") or 0),
        "source_url": result.get("source_url"),
    }
