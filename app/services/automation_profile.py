"""
Automation profile engine — infer high-level robot / automation requirements per lead.

V1 is rule-based: industry + signal types + light keyword scan on signal text.
Persisted on `companies.automation_profile` (JSON); refreshed via ORM hooks when signals change.
Future: optional LLM pass, CRM export.

Bench tests: tests/test_automation_profile.py
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence, Set


# ─── Taxonomy (stable string ids for API / UI) ─────────────────────────────

DEPLOYMENT_CONTEXTS = frozenset({
    "factory_floor",
    "end_of_line",
    "process_manufacturing",
    "logistics_warehouse",
    "distribution_center",
    "last_mile",
    "hospitality_guest_facing",
    "hospitality_back_of_house",
    "healthcare_facility",
    "food_prep_kitchen",
    "mining_construction",
    "outdoor_yard",
})

ROBOT_CATEGORIES = frozenset({
    "articulated_industrial_arm",  # Fanuc, Yaskawa class
    "scara",
    "delta",
    "cartesian_gantry",
    "cobot",
    "amr_amr_forklift",
    "agv",
    "mobile_manipulator",
    "humanoid",
    "service_robot",
    "personal_assistant_robot",
    "drone_indoor",
    "mining_heavy_robot",
})

APPLICATION_AREAS = frozenset({
    "palletizing",
    "depalletizing",
    "packaging",
    "case_packing",
    "pick_and_place",
    "machine_tending",
    "welding",
    "material_handling",
    "sortation",
    "goods_to_person",
    "inventory_cycle_count",
    "food_delivery_mobile",
    "luggage_delivery",
    "housekeeping_support",
    "laundry_logistics",
    "food_prep_automation",
    "room_service_delivery",
    "surgery_support",
    "lab_automation",
    "inspection_vision",
})


@dataclass
class AutomationProfile:
    """Light spec sheet for sales — JSON-serializable."""

    deployment_contexts: List[str] = field(default_factory=list)
    robot_categories: List[str] = field(default_factory=list)
    application_areas: List[str] = field(default_factory=list)
    human_robot_collaboration: str = ""  # e.g. "cobot / shared workspace likely", "fenced industrial"
    sizing_notes: str = ""  # one short paragraph for reps
    confidence: str = "low"  # low | medium | high
    source: str = "rules_v1"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


# Industry (lowercased substring) → seed contexts, robot categories, applications
_INDUSTRY_SEEDS: Dict[str, Dict[str, Set[str]]] = {
    "manufacturing": {
        "deployment": {"factory_floor", "process_manufacturing", "end_of_line"},
        "robots": {"articulated_industrial_arm", "scara", "cobot"},
        "apps": {"machine_tending", "welding", "pick_and_place", "inspection_vision"},
    },
    "food & beverage": {
        "deployment": {"factory_floor", "end_of_line"},
        "robots": {"articulated_industrial_arm", "delta", "cartesian_gantry", "cobot"},
        "apps": {"packaging", "case_packing", "palletizing", "pick_and_place", "food_prep_automation"},
    },
    "food service": {
        "deployment": {"food_prep_kitchen", "hospitality_back_of_house"},
        "robots": {"cobot", "service_robot", "amr_amr_forklift"},
        "apps": {"food_prep_automation", "material_handling", "food_delivery_mobile"},
    },
    "restaurant": {
        "deployment": {"food_prep_kitchen"},
        "robots": {"cobot", "service_robot"},
        "apps": {"food_prep_automation", "food_delivery_mobile"},
    },
    "logistics": {
        "deployment": {"logistics_warehouse", "distribution_center"},
        "robots": {"amr_amr_forklift", "agv", "articulated_industrial_arm"},
        "apps": {"palletizing", "depalletizing", "sortation", "goods_to_person", "material_handling"},
    },
    "warehouse": {
        "deployment": {"logistics_warehouse", "distribution_center"},
        "robots": {"amr_amr_forklift", "agv", "mobile_manipulator"},
        "apps": {"sortation", "palletizing", "pick_and_place", "inventory_cycle_count"},
    },
    "fulfillment": {
        "deployment": {"distribution_center", "last_mile"},
        "robots": {"amr_amr_forklift", "agv"},
        "apps": {"goods_to_person", "sortation", "pick_and_place"},
    },
    "hospitality": {
        "deployment": {"hospitality_guest_facing", "hospitality_back_of_house"},
        "robots": {"service_robot", "amr_amr_forklift", "mobile_manipulator"},
        "apps": {
            "food_delivery_mobile",
            "luggage_delivery",
            "housekeeping_support",
            "room_service_delivery",
        },
    },
    "hotel": {
        "deployment": {"hospitality_guest_facing", "hospitality_back_of_house"},
        "robots": {"service_robot", "amr_amr_forklift"},
        "apps": {"food_delivery_mobile", "luggage_delivery", "room_service_delivery", "laundry_logistics"},
    },
    "healthcare": {
        "deployment": {"healthcare_facility"},
        "robots": {"cobot", "service_robot", "mobile_manipulator"},
        "apps": {"lab_automation", "surgery_support", "material_handling", "inspection_vision"},
    },
    "hospital": {
        "deployment": {"healthcare_facility"},
        "robots": {"service_robot", "mobile_manipulator", "amr_amr_forklift"},
        "apps": {"lab_automation", "material_handling", "surgery_support"},
    },
    "mining": {
        "deployment": {"mining_construction", "outdoor_yard"},
        "robots": {"mining_heavy_robot", "articulated_industrial_arm"},
        "apps": {"material_handling", "inspection_vision"},
    },
}

_DEFAULT_SEED = {
    "deployment": {"factory_floor", "logistics_warehouse"},
    "robots": {"articulated_industrial_arm", "amr_amr_forklift"},
    "apps": {"material_handling", "pick_and_place"},
}

# signal_type → extra applications / robot hints
_SIGNAL_TYPE_MAP: Dict[str, Dict[str, Set[str]]] = {
    "packaging_automation": {"apps": {"packaging", "case_packing", "palletizing"}, "robots": {"articulated_industrial_arm"}},
    "warehouse_throughput": {"apps": {"sortation", "material_handling"}, "robots": {"amr_amr_forklift", "agv"}},
    "material_handling": {"apps": {"material_handling", "palletizing"}, "robots": set()},
    "repetitive_process": {"apps": {"pick_and_place", "machine_tending"}, "robots": {"cobot", "scara"}},
    "labor_shortage": {"apps": set(), "robots": {"cobot", "amr_amr_forklift"}},
    "automation_intent": {"apps": {"pick_and_place"}, "robots": set()},
    "robot_installation": {"apps": set(), "robots": {"articulated_industrial_arm", "amr_amr_forklift"}},
    "production_capacity": {"apps": {"machine_tending", "pick_and_place"}, "robots": set()},
}

# Keyword in signal text (lowercased) → hints
_TEXT_KEYWORDS: List[tuple[str, str, str]] = [
    # (regex pattern, robot_category or "", application_area or "")
    (r"\bcobot\b|\bcollaborative\s+robot", "cobot", ""),
    (r"\bfanuc\b|\byaskawa\b|\bkuka\b|\babb\s+robot", "articulated_industrial_arm", ""),
    (r"\bamr\b|\bautonomous\s+mobile\b|\bagv\b", "amr_amr_forklift", "material_handling"),
    (r"\bpalletiz", "", "palletizing"),
    (r"\bpack\s*out\b|\bpack\s*in\b|\bpackaging\b", "", "packaging"),
    (r"\broom\s+service\b|\bluggage\b|\bhousekeeping\b", "service_robot", "room_service_delivery"),
    (r"\bhumanoid\b", "humanoid", ""),
    (r"\bscara\b", "scara", ""),
]


def _normalize_industry(industry: Optional[str]) -> str:
    if not industry:
        return ""
    return industry.strip().lower()


def _pick_industry_seed(industry: str) -> Dict[str, Set[str]]:
    if not industry or industry in ("unknown", "other", "new"):
        return {k: set(v) for k, v in _DEFAULT_SEED.items()}
    for key, seed in _INDUSTRY_SEEDS.items():
        if key in industry:
            return {k: set(v) for k, v in seed.items()}
    return {k: set(v) for k, v in _DEFAULT_SEED.items()}


def _signal_text_blob(signals: Sequence[Dict[str, Any]]) -> str:
    parts = []
    for s in signals or []:
        t = (s.get("raw_text") or s.get("signal_text") or "") or ""
        parts.append(t)
    return " ".join(parts).lower()


def infer_automation_profile(
    *,
    industry: Optional[str],
    signals: Optional[Sequence[Dict[str, Any]]],
    company_name: Optional[str] = None,
) -> AutomationProfile:
    """
    Build a light automation spec from industry + signals (API-shaped dicts ok).
    """
    ind = _normalize_industry(industry)
    seed = _pick_industry_seed(ind)
    deployment: Set[str] = set(seed["deployment"])
    robots: Set[str] = set(seed["robots"])
    apps: Set[str] = set(seed["apps"])

    sig_list = list(signals or [])
    for s in sig_list:
        st = (s.get("signal_type") or "").strip()
        if st in _SIGNAL_TYPE_MAP:
            m = _SIGNAL_TYPE_MAP[st]
            apps |= m.get("apps", set())
            robots |= m.get("robots", set())

    blob = _signal_text_blob(sig_list)
    for pattern, rcat, app in _TEXT_KEYWORDS:
        if re.search(pattern, blob, re.I):
            if rcat:
                robots.add(rcat)
            if app:
                apps.add(app)

    # Collaboration heuristic
    collab = "mixed — confirm on site visit"
    if "cobot" in robots or re.search(r"\bcobot\b|collaborative|alongside\s+operator", blob, re.I):
        collab = "cobot / collaborative — robots intended to work alongside people in shared or adjacent workspaces"
    elif deployment & {"factory_floor", "end_of_line", "process_manufacturing"} and "articulated_industrial_arm" in robots:
        collab = "typical fenced industrial cells — add cobots only where tasks require human-robot sharing"

    # Confidence
    n_sig = len(sig_list)
    if n_sig >= 4 and (apps | robots):
        conf = "high"
    elif n_sig >= 2:
        conf = "medium"
    else:
        conf = "low"

    name = (company_name or "").strip() or "This account"
    sizing = (
        f"{name}: prioritize {_format_list(sorted(apps)[:6], APPLICATION_AREAS)} applications; "
        f"deploy in {_format_list(sorted(deployment)[:4], DEPLOYMENT_CONTEXTS)} contexts; "
        f"robot forms to emphasize: {_format_list(sorted(robots)[:5], ROBOT_CATEGORIES)}. "
        f"Validate payload, reach, and throughput with customer engineering."
    )

    return AutomationProfile(
        deployment_contexts=sorted(deployment & DEPLOYMENT_CONTEXTS),
        robot_categories=sorted(robots & ROBOT_CATEGORIES),
        application_areas=sorted(apps & APPLICATION_AREAS),
        human_robot_collaboration=collab,
        sizing_notes=sizing[:1200],
        confidence=conf,
        source="rules_v1",
    )


def _format_list(items: List[str], allowed: frozenset) -> str:
    clean = [x for x in items if x in allowed]
    if not clean:
        return "general automation"
    return ", ".join(c.replace("_", " ") for c in clean)


def profile_from_company_api_dict(lead: Dict[str, Any]) -> AutomationProfile:
    """Convenience for `_fmt_company` / dashboard payloads."""
    return infer_automation_profile(
        industry=lead.get("industry"),
        signals=lead.get("signals") or [],
        company_name=lead.get("company_name"),
    )


def build_automation_profile_dict_from_company(
    company: Any,
    industry_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute rules_v1 profile from an ORM Company (needs `.name`, `.industry`, `.signals` loaded).
    Used for persistence and backfills. `industry_override` fixes display when DB industry is wrong.
    """
    sigs = getattr(company, "signals", None) or []
    ind = industry_override if industry_override is not None else getattr(company, "industry", None)
    return profile_from_company_api_dict(
        {
            "company_name": getattr(company, "name", None),
            "industry": ind,
            "signals": [
                {"signal_type": s.signal_type, "raw_text": s.signal_text or ""}
                for s in sigs
            ],
        }
    ).to_dict()


def get_automation_profile_for_response(
    company: Any,
    industry_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    API responses: return DB column when set; otherwise compute (e.g. before first persist).
    If `industry_override` differs from stored company.industry, recompute (ignore stale JSON).
    """
    raw_ind = (getattr(company, "industry", None) or "").strip()
    ov = (industry_override or "").strip()
    if ov and ov.lower() not in ("unknown", "other", "new") and ov != raw_ind:
        return build_automation_profile_dict_from_company(company, industry_override=ov)
    stored = getattr(company, "automation_profile", None)
    if isinstance(stored, dict) and stored.get("source") == "rules_v1":
        return stored
    return build_automation_profile_dict_from_company(company)
