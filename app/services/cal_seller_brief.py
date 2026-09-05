"""
Cal Seller Brief — OEM-facing conversion artifact.

Seller Brief is Cal talking *to the robot OEM* about jobs that robot
can do at a named employer. It is not a buyer-sales pitch.

Without this as the primary pre-signup proof, OEMs only see a sample
outbound email and have no reason to create an account.
"""
from __future__ import annotations

from typing import Any, Optional


def build_cal_seller_brief(
    *,
    company_name: str,
    industry: str = "",
    signal_text: str = "",
    signal_type: str = "",
    pipeline_action: str = "",
    robot_types: Optional[list[str]] = None,
    share_summary: str = "",
    hermes_job_title: str = "",
) -> dict[str, str]:
    """Return a compact OEM brief. All fields are plain language, no hype."""
    name = (company_name or "This employer").strip() or "This employer"
    ind = (industry or "this workplace").strip() or "this workplace"
    robots = [r.strip() for r in (robot_types or []) if (r or "").strip()]
    robot_line = ", ".join(robots[:3]) if robots else "this robot"
    why = (share_summary or signal_text or "").strip()
    if hermes_job_title.strip():
        why_now = (
            f"{name} has work a robot could be hired to do "
            f"({hermes_job_title.strip()}). That is a Robot Job, not a buyer lead."
        )
    elif why:
        clip = " ".join(why.split())
        if len(clip) > 180:
            clip = clip[:177].rstrip() + "…"
        why_now = clip
    elif signal_type:
        why_now = f"Observed work in {ind} — qualify the robot against this job, do not pitch a sale."
    else:
        why_now = f"Named work in {ind}. Next step is a Job Card, not a robot-sales intro."

    pitch = (pipeline_action or "").strip()
    if not pitch:
        pitch = (
            f"Show {robot_line} against this job: hardware + the task model this work needs. "
            "Do not lead with a generic automation pitch."
        )

    return {
        "headline": f"Jobs {robot_line} can do at {name}",
        "why_now": why_now,
        "pitch": pitch,
        "robot_fit": robot_line,
        "next_step": f"Keep this Job Card → site assessment for {name}",
        "for_whom": "oem",
    }


def format_cal_seller_brief_text(brief: dict[str, Any]) -> str:
    """Single block for panels / copy-to-clipboard."""
    if not brief:
        return ""
    name_bits = [
        brief.get("headline") or "",
        f"Why now: {brief['why_now']}" if brief.get("why_now") else "",
        f"Pitch: {brief['pitch']}" if brief.get("pitch") else "",
        f"Robot fit: {brief['robot_fit']}" if brief.get("robot_fit") else "",
        f"Next: {brief['next_step']}" if brief.get("next_step") else "",
    ]
    return "\n".join(b for b in name_bits if b).strip()
