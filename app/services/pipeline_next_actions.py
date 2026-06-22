"""Top autonomous next actions from the public pipeline feed."""
from __future__ import annotations

from typing import Any, Optional

from app.services.humanoid_pilot_ranking import humanoid_pilot_sort_key

_TIER_ORDER = {"HOT": 0, "WARM": 1, "COLD": 2}
_TIER_PRIORITY = {"HOT": "high", "WARM": "medium", "COLD": "low"}


def _lead_score(lead: dict[str, Any]) -> float:
    score = lead.get("priority_score")
    if isinstance(score, (int, float)):
        return float(score)
    raw = lead.get("score")
    if isinstance(raw, dict):
        val = raw.get("overall_score") or raw.get("overall_intent_score")
        if isinstance(val, (int, float)):
            return float(val)
    if isinstance(raw, (int, float)):
        return float(raw)
    return 0.0


def _lead_tier(lead: dict[str, Any]) -> str:
    tier = str(lead.get("priority_tier") or lead.get("tier") or "WARM").upper()
    return tier if tier in _TIER_ORDER else "WARM"


def _action_label(lead: dict[str, Any]) -> str:
    hp_action = (lead.get("humanoid_pilot_action") or "").strip()
    if hp_action and lead.get("humanoid_pilot_tier") in ("ACTIVE_PILOT", "PILOT_INTENT"):
        return f"Humanoid · {hp_action}"
    action = (lead.get("pipeline_action") or "").strip()
    if action:
        return action
    tier = _lead_tier(lead)
    if tier == "HOT":
        return "Prioritize outreach — HOT intent detected"
    if tier == "WARM":
        return "Review signals and draft intro"
    return "Monitor and qualify when timing improves"


def collect_pipeline_next_actions(
    leads: list[dict[str, Any]],
    *,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Rank pipeline cards into rep-facing next actions (top `limit`)."""
    lim = max(1, min(int(limit), 10))
    ranked = sorted(
        [lead for lead in leads if lead.get("id") and not lead.get("is_junk")],
        key=lambda row: (
            humanoid_pilot_sort_key(row)[0],
            _TIER_ORDER.get(_lead_tier(row), 9),
            humanoid_pilot_sort_key(row)[1],
            humanoid_pilot_sort_key(row)[2],
        ),
    )

    actions: list[dict[str, Any]] = []
    for lead in ranked[:lim]:
        tier = _lead_tier(lead)
        cid = lead.get("id")
        actions.append(
            {
                "id": f"pipeline:{cid}",
                "action_type": "pipeline_outreach",
                "label": _action_label(lead),
                "companyName": lead.get("company_name") or f"Company #{cid}",
                "priority": _TIER_PRIORITY.get(tier, "medium"),
                "route": "/pipeline",
                "entity_type": "company",
                "entity_id": str(cid),
                "score": round(_lead_score(lead), 1),
                "meta": {
                    "tier": tier,
                    "industry": lead.get("industry"),
                    "humanoid_pilot_tier": lead.get("humanoid_pilot_tier"),
                    "humanoid_pilot_label": lead.get("humanoid_pilot_label"),
                },
            }
        )
    return actions
