"""
Machine-readable ontology loader — makes the ontology library *usable* by the
scraping/parsing → derive → match workflow (not just Markdown docs).

Loads the JSON ontologies under ``ontology/`` (capability, workflow, hardware,
inference rules) and exposes typed accessors. Fails **open**: if a file is
missing or malformed, the baked-in defaults (which mirror the current code) are
returned so production behaviour never breaks. ``tests/test_robot_ontology.py``
enforces that these ontologies stay in sync with the live pipeline, so updating
the ontology JSON is meaningful and safe.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_ONT_DIR = _ROOT / "ontology"

ONTOLOGY_VERSION = "1.0.0"

# ── Baked-in fallbacks (mirror the code so a missing file never breaks prod) ──
_DEFAULT_CONFIDENCE_STATES = ("EXPLICIT", "DERIVED", "LIKELY", "UNKNOWN", "CONFLICTED")
_DEFAULT_DISTINCTIVE = frozenset(
    {
        "manipulate", "dual_arm", "tote_transport", "transport", "food_prep",
        "beverage_prep", "surface_clean", "hard_floor_scrub", "inspect_route",
        "load_unload", "reach",
    }
)
_DEFAULT_GENERIC = frozenset({"mobile"})
_DEFAULT_FAMILIES: dict[str, list[str]] = {
    "pallet": ["manipulate"],
    "gripper": ["manipulate"],
    "transport": ["tote_transport", "transport"],
    "cart": ["tote_transport", "transport"],
    "scrub": ["hard_floor_scrub"],
    "inspect": ["inspect_route"],
    "serve": ["transport"],
    "food_prep": ["food_prep"],
    "beverage": ["beverage_prep"],
    "restroom": ["surface_clean"],
}


def _load(name: str) -> dict[str, Any]:
    try:
        return json.loads((_ONT_DIR / name).read_text(encoding="utf-8"))
    except Exception:
        return {}


@lru_cache(maxsize=1)
def capability_ontology() -> dict[str, Any]:
    return _load("capability_ontology.v1.json")


@lru_cache(maxsize=1)
def workflow_ontology() -> dict[str, Any]:
    return _load("workflow_ontology.v1.json")


@lru_cache(maxsize=1)
def hardware_ontology() -> dict[str, Any]:
    return _load("hardware_ontology.v1.json")


@lru_cache(maxsize=1)
def inference_rules() -> dict[str, Any]:
    return _load("inference_rules.v1.json")


@lru_cache(maxsize=1)
def vertical_ontology() -> dict[str, Any]:
    return _load("vertical_ontology.v1.json")


@lru_cache(maxsize=1)
def task_model_ontology() -> dict[str, Any]:
    return _load("task_model_ontology.v1.json")


@lru_cache(maxsize=1)
def oem_sku_catalog() -> dict[str, Any]:
    """Operator OEM → named SKU identity catalog. Fail-open to {}."""
    return _load("oem_sku_catalog.v1.json")


# ── Accessors used by the pipeline (each fails open to the baked-in default) ──

def confidence_states() -> tuple[str, ...]:
    states = capability_ontology().get("confidence_states")
    return tuple(states) if states else _DEFAULT_CONFIDENCE_STATES


def _capabilities() -> list[dict[str, Any]]:
    return capability_ontology().get("capabilities") or []


def capability_keys() -> frozenset[str]:
    caps = {c["key"] for c in _capabilities() if c.get("key")}
    return frozenset(caps) if caps else (_DEFAULT_DISTINCTIVE | _DEFAULT_GENERIC | {"payload"})


def distinctive_capabilities() -> frozenset[str]:
    caps = {c["key"] for c in _capabilities() if c.get("distinctive")}
    return frozenset(caps) if caps else _DEFAULT_DISTINCTIVE


def generic_capabilities() -> frozenset[str]:
    caps = {c["key"] for c in _capabilities() if c.get("generic")}
    return frozenset(caps) if caps else _DEFAULT_GENERIC


def grounding_predicates(capability: str) -> list[str]:
    for c in _capabilities():
        if c.get("key") == capability:
            return list(c.get("grounded_by") or [])
    return []


def workflow_families() -> frozenset[str]:
    fams = (workflow_ontology().get("families") or {}).keys()
    return frozenset(fams) if fams else frozenset(_DEFAULT_FAMILIES)


def workflow_required_capabilities(family: str) -> list[str]:
    fam = (workflow_ontology().get("families") or {}).get(family)
    if fam and fam.get("required_any"):
        return list(fam["required_any"])
    return list(_DEFAULT_FAMILIES.get(family, []))


_DEFAULT_VERTICALS = frozenset(
    {
        "warehouse", "manufacturing", "retail", "hospitality", "restaurant",
        "healthcare", "eldercare", "airport", "commercial", "utilities",
        "indoor", "construction", "mining", "agriculture", "marine", "aviation",
    }
)


def _verticals() -> list[dict[str, Any]]:
    return vertical_ontology().get("verticals") or []


def verticals() -> frozenset[str]:
    keys = {v["key"] for v in _verticals() if v.get("key")}
    return frozenset(keys) if keys else _DEFAULT_VERTICALS


def in_scope_verticals() -> frozenset[str]:
    return frozenset(v["key"] for v in _verticals() if v.get("in_scope"))
