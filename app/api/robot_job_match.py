"""
Public robot → jobs capability match (homepage / jobs front door).

POST /api/robot-job-match
  { "url": "https://…", "chip": …, "profile": {…Understanding v1…} }

When `profile` is present (research-first path), M2 requirement matching
runs against frozen facts. Chip recovery still uses the legacy corpus matcher.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.robot_job_capability_match import match_from_chip, match_robot_url
from app.services.robot_requirement_match import match_jobs_from_profile
from app.services.robot_url_safety import UrlSafetyError

router = APIRouter(tags=["robot-job-match"])

ChipLiteral = Literal["moves_materials", "manipulates", "cleans", "inspects", "other"]
StateLiteral = Literal[
    "matches",
    "thin_corpus",
    "could_not_understand",
    "select_product",
    "qualify_robot",
]


class RobotJobMatchIn(BaseModel):
    url: Optional[str] = Field(default=None, max_length=2000)
    chip: Optional[ChipLiteral] = None
    robot_name: Optional[str] = Field(default=None, max_length=120)
    product_name: Optional[str] = Field(default=None, max_length=120)
    robot_capabilities: Optional[dict[str, Any]] = None
    page_text: Optional[str] = Field(default=None, max_length=20000)
    asserted_class: Optional[str] = Field(default=None, max_length=40)
    profile: Optional[dict[str, Any]] = None


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
    needs_class_choice: bool = False
    class_options: list[dict[str, str]] = []
    preview_image_url: Optional[str] = None
    research_stages: list[dict[str, Any]] = []
    robot_class: Optional[str] = None
    evidence_urls: list[str] = []
    robot_capabilities: Optional[dict[str, Any]] = None
    matcher: Optional[str] = None
    # Truthful zero-state explainer (only set when no jobs matched).
    zero_reason: Optional[str] = None


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
        "needs_class_choice": False,
        "class_options": [],
        "preview_image_url": None,
        "research_stages": [],
        "robot_class": None,
        "evidence_urls": [],
        "robot_capabilities": None,
        "matcher": None,
    }


@router.post("/robot-job-match", response_model=RobotJobMatchOut)
def post_robot_job_match(body: RobotJobMatchIn) -> dict[str, Any]:
    url = (body.url or "").strip()
    chip = body.chip
    name = body.robot_name or "your robot"
    resolved_name = None if name == "your robot" else name
    profile = body.profile

    if not url and not chip and not body.robot_capabilities and not profile:
        return _empty("could_not_understand", name)

    try:
        if profile and (profile.get("facts") or profile.get("selected_product")):
            if body.asserted_class:
                from app.services.robot_class_qualify import apply_asserted_class

                profile = apply_asserted_class(profile, body.asserted_class)
            result = match_jobs_from_profile(profile)
        elif chip and not url and not body.robot_capabilities:
            result = match_from_chip(chip, robot_name=name)
        else:
            result = match_robot_url(
                url or "https://example.com/",
                chip=chip,
                robot_name=resolved_name,
                product_name=body.product_name,
                robot_capabilities=body.robot_capabilities,
                page_text=body.page_text,
            )
    except UrlSafetyError:
        return _empty("could_not_understand", name, url or None)
    except Exception:
        if chip:
            result = match_from_chip(chip, robot_name=name)
        else:
            return _empty("could_not_understand", name, url or None)

    jobs_out = result.get("jobs") or []
    job_count = int(result.get("job_count") or 0)
    zero_reason = None
    if not jobs_out and job_count == 0 and result.get("state") not in ("select_product",):
        from app.services.zero_state import classify_zero_state, corpus_family_set

        zero_reason = classify_zero_state(result.get("capabilities") or [], corpus_family_set())

    needs_class_choice = False
    class_options: list[dict[str, str]] = []
    if not jobs_out and job_count == 0 and result.get("state") not in ("select_product",):
        from app.services.robot_class_qualify import public_class_options
        from app.services.zero_state import INSUFFICIENT_PROFILE_EVIDENCE

        if zero_reason == INSUFFICIENT_PROFILE_EVIDENCE:
            needs_class_choice = True
            zero_reason = None
            class_options = public_class_options()
            result["state"] = "qualify_robot"

    return {
        "state": result["state"],
        "robot_name": result.get("robot_name") or name,
        "capabilities": result.get("capabilities") or [],
        "families": result.get("families") or [],
        "jobs": jobs_out,
        "job_count": job_count,
        "source_url": result.get("source_url") or (url or None),
        "company_name": result.get("company_name"),
        "products": result.get("products") or [],
        "needs_product_choice": bool(result.get("needs_product_choice")),
        "needs_class_choice": needs_class_choice,
        "class_options": class_options,
        "preview_image_url": next(
            (u for u in ((profile or {}).get("preview_images") or []) if isinstance(u, str) and u),
            None,
        ),
        "research_stages": result.get("research_stages") or [],
        "robot_class": result.get("robot_class"),
        "evidence_urls": result.get("evidence_urls") or [],
        "robot_capabilities": result.get("robot_capabilities"),
        "matcher": result.get("matcher"),
        "zero_reason": zero_reason,
    }
