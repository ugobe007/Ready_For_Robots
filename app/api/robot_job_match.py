"""
Public robot → jobs capability match (homepage / jobs front door).

POST /api/robot-job-match
  { "url": "https://…", "chip": "manipulates" | null, "product_name": "Digit" | null }

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
StateLiteral = Literal["matches", "thin_corpus", "could_not_understand", "select_product"]


class RobotJobMatchIn(BaseModel):
    url: Optional[str] = Field(default=None, max_length=2000)
    chip: Optional[ChipLiteral] = None
    robot_name: Optional[str] = Field(default=None, max_length=120)
    product_name: Optional[str] = Field(default=None, max_length=120)


class RobotJobMatchOut(BaseModel):
    state: StateLiteral
    robot_name: str
    capabilities: list[dict[str, Any]]
    families: list[dict[str, Any]]
    jobs: list[dict[str, Any]]
    job_count: int
    source_url: Optional[str] = None
    company_name: Optional[str] = None
    products: list[dict[str, Any]] = []
    needs_product_choice: bool = False
    research_stages: list[dict[str, Any]] = []
    robot_class: Optional[str] = None
    evidence_urls: list[str] = []


def _empty(state: StateLiteral, name: str, url: str | None = None) -> dict[str, Any]:
    return {
        "state": state,
        "robot_name": name,
        "capabilities": [],
        "families": [],
        "jobs": [],
        "job_count": 0,
        "source_url": url,
        "company_name": None,
        "products": [],
        "needs_product_choice": False,
        "research_stages": [],
        "robot_class": None,
        "evidence_urls": [],
    }


@router.post("/robot-job-match", response_model=RobotJobMatchOut)
def post_robot_job_match(body: RobotJobMatchIn) -> dict[str, Any]:
    url = (body.url or "").strip()
    chip = body.chip
    name = body.robot_name or "your robot"

    if not url and not chip:
        return _empty("could_not_understand", name)

    try:
        if chip and not url:
            result = match_from_chip(chip, robot_name=name)
        else:
            result = match_robot_url(url, chip=chip, product_name=body.product_name)
    except UrlSafetyError:
        return _empty("could_not_understand", name, url or None)
    except Exception:
        if chip:
            result = match_from_chip(chip, robot_name=name)
        else:
            return _empty("could_not_understand", name, url or None)

    return {
        "state": result["state"],
        "robot_name": result.get("robot_name") or name,
        "capabilities": result.get("capabilities") or [],
        "families": result.get("families") or [],
        "jobs": result.get("jobs") or [],
        "job_count": int(result.get("job_count") or 0),
        "source_url": result.get("source_url"),
        "company_name": result.get("company_name"),
        "products": result.get("products") or [],
        "needs_product_choice": bool(result.get("needs_product_choice")),
        "research_stages": result.get("research_stages") or [],
        "robot_class": result.get("robot_class"),
        "evidence_urls": result.get("evidence_urls") or [],
    }
