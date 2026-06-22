"""
Industry-specific automation context and rep-facing pipeline actions.

Canonical labels align with ``effective_industry_for_lead`` / ``INDUSTRY_TIE_PRIORITY``.
"""
from __future__ import annotations

from typing import Optional, Sequence, Tuple

# Canonical industry → automation context + rep next-step
_INDUSTRY_COPY: dict[str, dict[str, str]] = {
    "Logistics": {
        "automation_type": "AMRs and warehouse orchestration",
        "pain_point": "throughput bottlenecks and labor shortages",
        "pipeline_action": "Open with dock-to-stock AMR ROI — ask who owns slotting and outbound flow.",
    },
    "Hospitality": {
        "automation_type": "room-service and housekeeping robots",
        "pain_point": "housekeeping labor and guest-service consistency",
        "pipeline_action": "Lead with off-hours cleaning plus daytime runner robots — tie to vacancy rates.",
    },
    "Casinos & Gaming": {
        "automation_type": "commercial cleaning and delivery robots",
        "pain_point": "24/7 facility coverage and housekeeping labor",
        "pipeline_action": "Pitch floor-scrubber and back-of-house delivery pilots before peak weekend traffic.",
    },
    "Cruise Lines": {
        "automation_type": "housekeeping and logistics robots",
        "pain_point": "crew labor on tight turnaround windows",
        "pipeline_action": "Focus on galley/logistics AMRs and cabin-turnover automation between port days.",
    },
    "Healthcare": {
        "automation_type": "hospital logistics and disinfection robots",
        "pain_point": "staff walking time and infection-control load",
        "pipeline_action": "Ask about internal transport and EVS — lead with linen/supply AMR or UV disinfection.",
    },
    "Medical Technology": {
        "automation_type": "lab automation and cleanroom robotics",
        "pain_point": "throughput in regulated production and kitting",
        "pipeline_action": "Qualify manufacturing or lab workflow owners — cobots and mobile manipulators first.",
    },
    "Food Service": {
        "automation_type": "kitchen automation and runner robots",
        "pain_point": "kitchen labor and order accuracy",
        "pipeline_action": "Start with back-of-house prep or runner bots during peak rushes — avoid front-of-house hard sell.",
    },
    "Food Processing & Manufacturing": {
        "automation_type": "packaging and palletizing automation",
        "pain_point": "line labor and throughput on high-volume SKUs",
        "pipeline_action": "Lead with end-of-line palletizing or case packing — ask about capex this quarter.",
    },
    "Manufacturing": {
        "automation_type": "collaborative robots and assembly automation",
        "pain_point": "labor costs and line consistency",
        "pipeline_action": "Identify the bottleneck station — propose a cobot or AMR pilot on one line.",
    },
    "Automotive & Manufacturing": {
        "automation_type": "assembly cobots and material-handling AMRs",
        "pain_point": "labor gaps on the line and kitting",
        "pipeline_action": "Ask about new model lines or rework cells — AMR kitting is an easy wedge.",
    },
    "Airports & Aviation": {
        "automation_type": "baggage-handling automation and terminal service robots",
        "pain_point": "ground-ops staffing and peak-window service",
        "pipeline_action": "Lead with baggage AMR or overnight cleaning — confirm ground ops vs facilities owner.",
    },
    "Retail": {
        "automation_type": "inventory robots and back-of-house automation",
        "pain_point": "labor for stocking and fulfillment backrooms",
        "pipeline_action": "Ask about micro-fulfillment or backroom inventory bots before broad rollout.",
    },
    "Datacenters": {
        "automation_type": "inspection drones and facility service robots",
        "pain_point": "facility uptime and technician travel time",
        "pipeline_action": "Lead with inspection or cable-tracing drones — facilities owns the budget.",
    },
    "Construction & Building": {
        "automation_type": "layout robots and autonomous site equipment",
        "pain_point": "skilled labor gaps and schedule slip",
        "pipeline_action": "Pilot layout or material-delivery robots on one active job site.",
    },
    "Ports & Maritime": {
        "automation_type": "yard tractors and container-handling automation",
        "pain_point": "berth throughput and driver shortages",
        "pipeline_action": "Engage terminal ops on horizontal transport — tie to dwell-time KPIs.",
    },
    "Pharmaceuticals & Life Sciences": {
        "automation_type": "lab automation and GMP-compliant robotics",
        "pain_point": "batch consistency and validated workflows",
        "pipeline_action": "Qualify QA/regulatory stakeholders early — start with non-GMP pilot if needed.",
    },
    "Real Estate & Facilities": {
        "automation_type": "cleaning and security robots",
        "pain_point": "contract labor cost across multi-site portfolios",
        "pipeline_action": "Propose a single-building cleaning pilot with measurable sq-ft coverage.",
    },
}

# Substring fallbacks when stored industry is partial or legacy
_INDUSTRY_ALIASES: tuple[tuple[str, str], ...] = (
    ("logistics", "Logistics"),
    ("warehouse", "Logistics"),
    ("fulfillment", "Logistics"),
    ("hospitality", "Hospitality"),
    ("hotel", "Hospitality"),
    ("casino", "Casinos & Gaming"),
    ("gaming", "Casinos & Gaming"),
    ("cruise", "Cruise Lines"),
    ("healthcare", "Healthcare"),
    ("hospital", "Healthcare"),
    ("medical", "Medical Technology"),
    ("food service", "Food Service"),
    ("restaurant", "Food Service"),
    ("food processing", "Food Processing & Manufacturing"),
    ("manufacturing", "Manufacturing"),
    ("automotive", "Automotive & Manufacturing"),
    ("aviation", "Airports & Aviation"),
    ("airport", "Airports & Aviation"),
    ("airline", "Airports & Aviation"),
    ("retail", "Retail"),
    ("datacenter", "Datacenters"),
    ("construction", "Construction & Building"),
    ("port", "Ports & Maritime"),
    ("maritime", "Ports & Maritime"),
    ("pharma", "Pharmaceuticals & Life Sciences"),
    ("facilities", "Real Estate & Facilities"),
)

_DEFAULT = {
    "automation_type": "robotic automation",
    "pain_point": "operational efficiency and labor costs",
    "pipeline_action": "Confirm the workflow owner and lead with one narrow pilot use case.",
}

_TIER_ACTION_PREFIX = {
    "HOT": "Priority:",
    "WARM": "Next:",
    "COLD": "Watch:",
}


def _resolve_canonical_industry(industry: Optional[str]) -> str:
    raw = (industry or "").strip()
    if not raw or raw.lower() in ("unknown", "other", "new"):
        return ""
    if raw in _INDUSTRY_COPY:
        return raw
    low = raw.lower()
    for key, canonical in _INDUSTRY_ALIASES:
        if key in low:
            return canonical
    return raw


def industry_automation_context(industry: Optional[str]) -> Tuple[str, str]:
    """Returns (automation_type, pain_point) for share copy."""
    canonical = _resolve_canonical_industry(industry)
    block = _INDUSTRY_COPY.get(canonical) or _DEFAULT
    return block["automation_type"], block["pain_point"]


def pipeline_action_for_lead(
    industry: Optional[str],
    *,
    tier: str = "WARM",
    signal_types: Optional[Sequence[str]] = None,
) -> str:
    """One-line rep-facing next step tailored to industry (and lightly to tier)."""
    canonical = _resolve_canonical_industry(industry)
    block = _INDUSTRY_COPY.get(canonical) or _DEFAULT
    action = block["pipeline_action"]
    prefix = _TIER_ACTION_PREFIX.get((tier or "").upper(), "Next:")

    types = [str(t or "").lower() for t in (signal_types or [])]
    if "funding_round" in types or "capex" in types:
        action = action.replace("Lead with", "Budget is moving — lead with").replace(
            "Open with", "Budget is moving — open with"
        )
    elif "labor_shortage" in types or "job_posting" in types:
        action = action.replace("Lead with", "Staffing pressure — lead with").replace(
            "Ask about", "Staffing pressure — ask about"
        )

    return f"{prefix} {action}"
