"""
Cal Seller Brief — OEM-facing conversion artifact.

BuyerCal writes notes *to* operating companies.
Seller Brief is Cal talking *to the robot OEM* about a buyer:
why this account fits their robot, why now, what to pitch, next step.

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
    name = (company_name or "This buyer").strip() or "This buyer"
    ind = (industry or "their operations").strip() or "their operations"
    robots = [r.strip() for r in (robot_types or []) if (r or "").strip()]
    robot_line = ", ".join(robots[:3]) if robots else "the robot class you sell"
    why = (share_summary or signal_text or "").strip()
    if hermes_job_title.strip():
        why_now = f"{name} is hiring for {hermes_job_title.strip()} — timing that usually means operational load is already rising."
    elif why:
        clip = " ".join(why.split())
        if len(clip) > 180:
            clip = clip[:177].rstrip() + "…"
        why_now = clip
    elif signal_type:
        why_now = f"Active {signal_type.replace('_', ' ')} signal in {ind}."
    else:
        why_now = f"Live buying pressure in {ind} — worth a first conversation this week."

    pitch = (pipeline_action or "").strip()
    if not pitch:
        pitch = f"Lead with how {robot_line} removes a concrete workflow bottleneck — not a generic automation pitch."

    return {
        "headline": f"Why {name} is a fit for your robot",
        "why_now": why_now,
        "pitch": pitch,
        "robot_fit": robot_line,
        "next_step": f"Save {name} → copy the outreach note → start the conversation",
        "for_whom": "oem",  # seller brief, not buyer email
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
