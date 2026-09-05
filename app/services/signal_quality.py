"""
Signal quality: time decay, announcement noise vs buyer intent, use-case depth.

Ontology: concept names are internal labels (e.g. warehouse_automation), not company names.
Ambiguous proper names in headlines belong in scraper/lead_filter passes, not concept regexes.

Penalty penetration differs by domain — press noise hits expansion hardest; labor_pain is
protected; depth hits automation and industry_fit harder than labor.
"""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from app.services.semantic_parser import ParseResult

# ── Time decay (exponential half-life) ───────────────────────────────────────
SIGNAL_HALF_LIFE_DAYS = 45.0
# Floors so very old rows still nudge scores slightly (avoid hard zero)
MIN_TIME_WEIGHT = 0.12
MAX_TIME_WEIGHT = 1.0

# ── Announcement / sector-media phrasing (often not a buyer) ────────────────
_ANNOUNCEMENT_NOISE = [
    re.compile(r"(?i)\bunveils?\b"),
    re.compile(r"(?i)\bannounces?\s+(its\s+)?(latest|new|next|first)\b"),
    re.compile(r"(?i)\b(launches?|introduces?|debuts?)\s+(a\s+)?(new\s+)?(humanoid|robot|model|platform)\b"),
    re.compile(r"(?i)\b(stock|shares?)\s+(jump|surge|fall|drop|rise|soar)"),
    re.compile(r"(?i)\b(nasdaq|nyse)\b.*\b(stock|share)"),
    re.compile(r"(?i)\brobot\s+sector\b"),
    re.compile(r"(?i)\bhumanoid\s+(race|wars?|market)\b"),
    re.compile(r"(?i)\b(vc|venture)\s+funding\b.*\b(robot|humanoid)\s+(startup|company)\b"),
    re.compile(r"(?i)\b(?:said|according to)\s+(the\s+)?(ceo|founder)\b.*\b(robot|humanoid)\b"),
]

# Strong buyer / operational signals — if present, do not apply announcement penalty
_BUYER_OVERRIDE = [
    re.compile(r"(?i)\b(rfp|rfq|request for proposal)\b"),
    re.compile(r"(?i)\b(pilot|proof of concept|poc)\b.*\b(rollout|expand|success)\b"),
    re.compile(r"(?i)\b(labor\s+shortage|short\s+staff|hiring\s+difficult)\b"),
    re.compile(r"(?i)\b(warehouse|distribution|fulfillment)\s+.{0,40}(automat|robot|expand)\b"),
    re.compile(r"(?i)\b(deploy|installed|went live|fleet of).{0,30}(robot|amr|agv|cobot)\b"),
    re.compile(r"(?i)\b(head|director|vp).{0,40}(automation|robotics|fulfillment)\b"),
]

# Per-domain penetration for (1 - multiplier): not all finals get the same haircut.
NOISE_DOMAIN_PENETRATION: Dict[str, float] = {
    "automation": 0.88,
    "labor_pain": 0.32,
    "expansion": 1.0,
    "industry_fit": 0.72,
}
DEPTH_DOMAIN_PENETRATION: Dict[str, float] = {
    "automation": 1.0,
    "labor_pain": 0.28,
    "expansion": 0.72,
    "industry_fit": 0.88,
}


def _domain_factor(mult: float, penetration: float) -> float:
    """Map base mult in [0,1] to domain-specific factor; penetration 0 → 1.0, 1 → mult."""
    p = max(0.0, min(1.0, penetration))
    m = max(0.0, min(1.0, mult))
    return 1.0 - (1.0 - m) * p


# Ontology concept names — concrete workflow / deployment intent (not generic "AI")
USE_CASE_WORKFLOW_CONCEPTS = frozenset({
    "warehouse_automation",
    "amr_agv",
    "pick_place",
    "wms_integration",
    "computer_vision",
    "service_robot",
    "cobots",
    "robot_installation",
    "pilot_success",
    "disinfection_robot",
    "floor_scrubber_automation",
    "strategic_automation_hire",
    "operations_technology_hire",
    "automation_intent",
    "equipment_integration",
    "labor_shortage",
    "reduce_labor_costs",
    "warehouse_expansion",
    "capex_announcement",
    "roi_documented",
    "vendor_selection",
})


def time_weight_for_signal(created_at: Optional[datetime], now: Optional[datetime] = None) -> float:
    """
    Weight in (MIN_TIME_WEIGHT, 1.0] by age. Missing timestamp → full weight.
    """
    if created_at is None:
        return MAX_TIME_WEIGHT
    now = now or datetime.now(timezone.utc)
    ca = created_at
    if ca.tzinfo is None:
        ca = ca.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (now - ca).total_seconds() / 86400.0)
    # Half-life decay: w = 2^(-age/half_life)
    w = math.exp(-math.log(2.0) * age_days / float(SIGNAL_HALF_LIFE_DAYS))
    return max(MIN_TIME_WEIGHT, min(MAX_TIME_WEIGHT, w))


def _text_hits_noise(text: str) -> bool:
    t = text or ""
    if not any(p.search(t) for p in _ANNOUNCEMENT_NOISE):
        return False
    if any(p.search(t) for p in _BUYER_OVERRIDE):
        return False
    return True


def announcement_noise_ratio(signal_texts: List[str]) -> float:
    """
    0.0 = no announcement-style noise detected; 1.0 = all fragments look like noise.
    """
    if not signal_texts:
        return 0.0
    hits = sum(1 for s in signal_texts if _text_hits_noise(s))
    return min(1.0, hits / float(len(signal_texts)))


def _max_domain_score(parse: "ParseResult") -> float:
    return max(
        parse.domain_score("automation"),
        parse.domain_score("labor_pain"),
        parse.domain_score("expansion"),
        parse.domain_score("industry_fit"),
    )


def use_case_workflow_count(parse: "ParseResult", min_confidence: float = 0.26) -> int:
    n = 0
    for name, act in parse.activations.items():
        if name in USE_CASE_WORKFLOW_CONCEPTS and act.confidence >= min_confidence:
            n += 1
    return n


def quality_multipliers(
    parse: "ParseResult",
    signal_texts: List[str],
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Returns (noise_mult, depth_mult, detail_dict) in [0,1] each, combined applied to domain finals.
    """
    noise_r = announcement_noise_ratio(signal_texts)
    max_dom = _max_domain_score(parse)
    workflow_n = use_case_workflow_count(parse)

    # Noise: high press-style ratio + weak ontology evidence → downweight
    if noise_r >= 0.55 and max_dom < 0.42:
        noise_mult = 0.68
    elif noise_r >= 0.35 and max_dom < 0.30:
        noise_mult = 0.82
    elif noise_r >= 0.5 and max_dom < 0.50:
        noise_mult = 0.78
    else:
        noise_mult = 1.0

    # Use-case depth: strong domain scores without any workflow anchor → generic "robot" hype
    if workflow_n >= 2:
        depth_mult = 1.0
    elif workflow_n == 1:
        depth_mult = 0.96
    else:
        if max_dom >= 0.48:
            depth_mult = 0.86
        elif max_dom >= 0.38:
            depth_mult = 0.92
        else:
            depth_mult = 1.0

    detail = {
        "announcement_noise_ratio": round(noise_r, 4),
        "max_domain_score": round(max_dom, 4),
        "workflow_concept_hits": workflow_n,
        "noise_multiplier": noise_mult,
        "depth_multiplier": depth_mult,
    }
    return noise_mult, depth_mult, detail


def apply_quality_to_domain_finals(
    automation: float,
    labor_pain: float,
    expansion: float,
    industry_fit: float,
    signal_texts: List[str],
    parse: "ParseResult",
) -> Tuple[float, float, float, float, Dict[str, Any]]:
    """
    Adjust domain finals (0–1) with **different** noise/depth factors per domain.
    Caller recomputes overall_intent from the four domains using engine weights.
    """
    nm, dm, detail = quality_multipliers(parse, signal_texts)

    fa = _domain_factor(nm, NOISE_DOMAIN_PENETRATION["automation"]) * _domain_factor(
        dm, DEPTH_DOMAIN_PENETRATION["automation"]
    )
    fl = _domain_factor(nm, NOISE_DOMAIN_PENETRATION["labor_pain"]) * _domain_factor(
        dm, DEPTH_DOMAIN_PENETRATION["labor_pain"]
    )
    fe = _domain_factor(nm, NOISE_DOMAIN_PENETRATION["expansion"]) * _domain_factor(
        dm, DEPTH_DOMAIN_PENETRATION["expansion"]
    )
    fi = _domain_factor(nm, NOISE_DOMAIN_PENETRATION["industry_fit"]) * _domain_factor(
        dm, DEPTH_DOMAIN_PENETRATION["industry_fit"]
    )

    detail["per_domain_combined_factor"] = {
        "automation": round(fa, 4),
        "labor_pain": round(fl, 4),
        "expansion": round(fe, 4),
        "industry_fit": round(fi, 4),
    }
    # Legacy single scalar: geometric mean of domain factors (for dashboards / alerts)
    detail["combined_multiplier"] = round(
        (fa * fl * fe * fi) ** 0.25, 4
    )

    if min(fa, fl, fe, fi) >= 0.999:
        return automation, labor_pain, expansion, industry_fit, detail

    return (
        min(1.0, automation * fa),
        min(1.0, labor_pain * fl),
        min(1.0, expansion * fe),
        min(1.0, industry_fit * fi),
        detail,
    )
