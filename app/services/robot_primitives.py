"""
Map robot categories / vendor catalog text → primitives.v1 capability set.

Same spine as work_unit_reconstruct so MATCH is constraint overlap, not free-text.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from app.domain.enums import load_primitives_ontology

# Category / keyword → supported primitives (Knowledge / OEM_VERIFIED proxy)
_CATEGORY_PRIMITIVES: Dict[str, Set[str]] = {
    "autonomous_forklift": {
        "mob.navigate_indoor",
        "mob.navigate_mixed_traffic",
        "mob.narrow_aisle",
        "eng.acquire_pallet_floor",
        "man.lift_vertical",
        "tr.point_to_point",
        "tr.dock_to_storage",
        "plc.floor_place",
        "plc.staging_place",
        "per.localize",
        "per.detect_pallet",
        "per.detect_human",
        "exc.handle_blocked_path",
        "exc.call_for_help",
    },
    "amr": {
        "mob.navigate_indoor",
        "mob.navigate_mixed_traffic",
        "eng.acquire_cart_or_tote",
        "tr.point_to_point",
        "plc.floor_place",
        "plc.staging_place",
        "per.localize",
        "per.detect_human",
        "exc.handle_blocked_path",
        "exc.call_for_help",
    },
    "amr_amr_forklift": {
        "mob.navigate_indoor",
        "mob.navigate_mixed_traffic",
        "mob.narrow_aisle",
        "eng.acquire_pallet_floor",
        "man.lift_vertical",
        "tr.point_to_point",
        "plc.floor_place",
        "plc.staging_place",
        "per.localize",
        "per.detect_pallet",
        "per.detect_human",
        "exc.handle_blocked_path",
    },
    "agv": {
        "mob.navigate_indoor",
        "tr.point_to_point",
        "tr.line_replenishment",
        "eng.tow_hitch",
        "eng.acquire_cart_or_tote",
        "plc.staging_place",
        "per.localize",
    },
    "autonomous_tugger": {
        "mob.navigate_indoor",
        "mob.navigate_mixed_traffic",
        "eng.tow_hitch",
        "eng.acquire_cart_or_tote",
        "tr.line_replenishment",
        "plc.staging_place",
        "per.localize",
        "per.detect_human",
        "int.human_handoff",
        "exc.handle_blocked_path",
        "exc.call_for_help",
    },
    "material_movement": {
        "mob.navigate_indoor",
        "eng.acquire_pallet_floor",
        "eng.acquire_cart_or_tote",
        "tr.point_to_point",
        "plc.floor_place",
        "per.detect_pallet",
        "per.localize",
    },
    "mobile_manipulator": {
        "mob.navigate_indoor",
        "man.case_pick",
        "man.dexterous_adjust",
        "eng.acquire_cart_or_tote",
        "tr.point_to_point",
        "per.localize",
        "int.human_handoff",
    },
    "humanoid": {
        "mob.navigate_indoor",
        "mob.navigate_mixed_traffic",
        "man.case_pick",
        "man.dexterous_adjust",
        "int.human_handoff",
        "per.detect_human",
        "exc.call_for_help",
    },
    "service_robot": {
        "mob.navigate_indoor",
        "mob.navigate_mixed_traffic",
        "tr.point_to_point",
        "per.detect_human",
        "int.human_handoff",
    },
    "articulated_industrial_arm": {
        "man.case_pick",
        "man.lift_vertical",
        "man.dexterous_adjust",
        "plc.floor_place",
        "plc.staging_place",
    },
    "cobot": {
        "man.case_pick",
        "man.dexterous_adjust",
        "int.human_handoff",
        "per.detect_human",
    },
}

_KEYWORD_ALIASES: Tuple[Tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(autonomous\s+forklift|forklift\s+amr|counterbalance)\b", re.I), "autonomous_forklift"),
    (re.compile(r"\b(tugger|tow\s+tractor|autonomous\s+tow)\b", re.I), "autonomous_tugger"),
    (re.compile(r"\b\bamr\b|autonomous\s+mobile\s+robot", re.I), "amr"),
    (re.compile(r"\bagv\b", re.I), "agv"),
    (re.compile(r"\bhumanoid\b", re.I), "humanoid"),
    (re.compile(r"\bcobot\b|collaborative\s+robot", re.I), "cobot"),
    (re.compile(r"material\s+handl", re.I), "material_movement"),
)


def _valid() -> frozenset[str]:
    return frozenset(p["code"] for p in load_primitives_ontology()["primitives"])


def normalize_category(raw: str) -> Optional[str]:
    low = (raw or "").strip().lower().replace("-", "_").replace(" ", "_")
    if low in _CATEGORY_PRIMITIVES:
        return low
    # loose contains
    for key in _CATEGORY_PRIMITIVES:
        if key in low or low in key:
            return key
    for pattern, cat in _KEYWORD_ALIASES:
        if pattern.search(raw or ""):
            return cat
    return None


def primitives_for_categories(categories: Sequence[str]) -> Set[str]:
    out: Set[str] = set()
    valid = _valid()
    for cat in categories or []:
        key = normalize_category(str(cat))
        if key:
            out |= _CATEGORY_PRIMITIVES[key]
    return {c for c in out if c in valid}


def primitives_from_vendor_text(
    *,
    robot_categories: Sequence[str] | None = None,
    name: str | None = None,
    primary_industries: Sequence[str] | None = None,
) -> Dict[str, Any]:
    """Infer Knowledge-layer robot capability primitives for a vendor/manufacturer row."""
    cats = [str(c) for c in (robot_categories or [])]
    blob = " ".join([name or "", *cats, *[str(i) for i in (primary_industries or [])]])
    inferred_cats: List[str] = []
    for c in cats:
        key = normalize_category(c)
        if key and key not in inferred_cats:
            inferred_cats.append(key)
    for pattern, cat in _KEYWORD_ALIASES:
        if pattern.search(blob) and cat not in inferred_cats:
            inferred_cats.append(cat)
    codes = sorted(primitives_for_categories(inferred_cats))
    return {
        "categories": inferred_cats,
        "supported_primitives": codes,
        "confidence": 0.55 if codes else 0.1,
        "truth_state": "OEM_VERIFIED" if codes else "INFERRED",
        "source": "robot_primitives_v1",
        "layer": "knowledge",
    }
