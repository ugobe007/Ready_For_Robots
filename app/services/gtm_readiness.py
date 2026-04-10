"""
GTM-oriented readiness for lead payloads: where the account sits in the robot
buying journey (deploy / evaluate / explore) and concise “why now” bullets.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Sequence

from app.services.lead_filter import DEPLOYMENT_SIGNAL_TYPES

_FRESH_DAYS = 14

# Order matters: strongest GTM story first when multiple deployment types exist.
_DEPLOYMENT_ORDER = (
    "robot_installation",
    "pilot_success",
    "scale_expansion",
    "vendor_selection",
    "rfp_posted",
)

_WHY_DEPLOYMENT: Dict[str, str] = {
    "robot_installation": "Robots or automation hardware in deployment",
    "pilot_success": "Pilot traction — moving past trial",
    "scale_expansion": "Scaling proven automation",
    "vendor_selection": "Vendor or integrator selection underway",
    "rfp_posted": "Formal RFP or public procurement",
}


def _latest_signal_time(signals: Sequence[Any]) -> Optional[datetime]:
    latest: Optional[datetime] = None
    for s in signals:
        ts = getattr(s, "created_at", None)
        if ts is None:
            continue
        if latest is None or ts > latest:
            latest = ts
    return latest


def _signals_fresh(signals: Sequence[Any], days: int = _FRESH_DAYS) -> bool:
    latest = _latest_signal_time(signals)
    if latest is None:
        return False
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    return latest >= datetime.now(timezone.utc) - timedelta(days=days)


def _short_reason(text: str, max_len: int = 120) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def _reason_distinct(line: str, existing: List[str]) -> bool:
    if not line:
        return False
    for w in existing:
        if line == w or line in w or w in line:
            return False
    return True


def compute_gtm_readiness(
    signals: Sequence[Any],
    priority_tier: str,
    priority_reasons: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Pure function — safe for API JSON. Uses signal types + tier + rule reasons.

    readiness_stage:
      deploying  — deployment/procurement signals (robots, pilot success, RFP, etc.)
      evaluating — HOT/WARM without deployment signals (active pipeline)
      exploring  — COLD / early
    """
    tier_u = (priority_tier or "").upper()
    reasons = [r for r in (priority_reasons or ()) if (r or "").strip()]
    type_set = {getattr(s, "signal_type", "") or "" for s in signals}
    type_set.discard("")

    deployment_hits = [t for t in _DEPLOYMENT_ORDER if t in type_set]

    if deployment_hits:
        stage = "deploying"
        readiness_label = "Deploy / scale"
    elif tier_u in ("HOT", "WARM"):
        stage = "evaluating"
        readiness_label = "Active evaluation" if tier_u == "HOT" else "Evaluating"
    else:
        stage = "exploring"
        readiness_label = "Early / nurture"

    why_now: List[str] = []
    for t in deployment_hits:
        line = _WHY_DEPLOYMENT.get(t)
        if line and line not in why_now:
            why_now.append(line)
        if len(why_now) >= 2:
            break

    for r in reasons:
        line = _short_reason(r)
        if _reason_distinct(line, why_now):
            why_now.append(line)
        if len(why_now) >= 4:
            break

    if _signals_fresh(signals) and not any("Recent signal" in w for w in why_now):
        if len(why_now) < 4:
            why_now.append("Recent signal activity (last ~2 weeks)")

    if not why_now:
        why_now.append("Intent and signals support outreach this quarter")

    suggested_motion = {
        "deploying": "Prioritize rollout fit, references, and expansion plays.",
        "evaluating": "Book discovery: quantify ROI and align on pilot scope.",
        "exploring": "Nurture with case studies, peer proof, and light technical content.",
    }[stage]

    return {
        "readiness_stage": stage,
        "readiness_label": readiness_label,
        "why_now": why_now[:4],
        "suggested_motion": suggested_motion,
        "deployment_signal_types": deployment_hits,
    }
