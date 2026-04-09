"""
Vendor (robot company) list score — 0–100 composite for outreach prioritization.

Uses stored `lead_score` plus structured CRM fields (U.S. presence, urgency, partnership stage).
Buyer leads use `signal_ranker` + ML; vendors are 1-D product sellers but still need ranked lists.
"""
from __future__ import annotations

from typing import Any, Dict

from app.models.robot_company import RobotCompany


def compute_vendor_list_score(rc: RobotCompany) -> Dict[str, Any]:
    """
    Returns vendor_list_score (0–100) and component breakdown for UI / sorting.
    """
    stored = min(100, max(0, int(rc.lead_score or 0)))

    us = (rc.us_presence or "").lower()
    us_u = {"office": 1.0, "distributor": 0.78, "none": 0.38}.get(us, 0.55)

    urg = (rc.distributor_urgency or "").lower()
    urg_u = {"high": 1.0, "medium": 0.68, "low": 0.36}.get(urg, 0.48)

    ps = (rc.partnership_stage or "").lower()
    ps_u = {"established": 1.0, "active": 0.82, "exploring": 0.45}.get(ps, 0.42)

    tier = (rc.priority_tier or "").lower()
    tier_u = {"hot": 1.0, "warm": 0.62, "cold": 0.28}.get(tier, 0.42)

    verified_u = 1.0 if rc.verified else 0.78

    # Weighted blend (sums to 1.0)
    composite = (
        0.28 * (stored / 100.0)
        + 0.22 * us_u
        + 0.18 * urg_u
        + 0.14 * ps_u
        + 0.12 * tier_u
        + 0.06 * verified_u
    )
    score = round(min(100.0, composite * 100.0), 1)

    return {
        "vendor_list_score": score,
        "vendor_score_components": {
            "stored_lead_score": stored,
            "us_presence_unit": round(us_u * 100, 1),
            "distributor_urgency_unit": round(urg_u * 100, 1),
            "partnership_stage_unit": round(ps_u * 100, 1),
            "priority_tier_unit": round(tier_u * 100, 1),
            "verified": bool(rc.verified),
        },
    }
