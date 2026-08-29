"""Operator qualification when Understanding cannot name a robot class.

The operator (the robot company) knows the SKU. Their selection is an explicit
fact: product_class. Jobs then match from that class. Never a dead-end copy.
"""
from __future__ import annotations

import copy
from typing import Any

CLASS_OPTIONS: list[dict[str, str]] = [
    {
        "id": "humanoid",
        "product_class": "humanoid",
        "label": "Humanoid",
        "hint": "Two legs, arms and hands — NEO, Unitree G1, Walker, Digit",
    },
    {
        "id": "amr",
        "product_class": "amr",
        "label": "AMR / mobile robot",
        "hint": "Rolls on a base and moves materials or itself",
    },
    {
        "id": "mobile_manipulator",
        "product_class": "mobile_manipulator",
        "label": "Mobile manipulator",
        "hint": "Rolling base with an arm that picks or places",
    },
    {
        "id": "cobot",
        "product_class": "cobot",
        "label": "Collaborative arm",
        "hint": "Stationary or cart-mounted arm beside a person",
    },
    {
        "id": "quadruped",
        "product_class": "quadruped",
        "label": "Quadruped",
        "hint": "Four legs — inspection, patrol, unstructured ground",
    },
    {
        "id": "autonomous_scrubber",
        "product_class": "autonomous_scrubber",
        "label": "Floor scrubber",
        "hint": "Cleans floors on its own",
    },
    {
        "id": "agriculture",
        "product_class": "agriculture",
        "label": "Agriculture",
        "hint": "Combines, tractors, weeding — implements mount on a tractor",
    },
    {
        "id": "marine",
        "product_class": "marine",
        "label": "Marine",
        "hint": "Hull, port, and underwater work",
    },
    {
        "id": "avionics",
        "product_class": "avionics",
        "label": "Avionics",
        "hint": "Drones, eVTOL flying cars, autonomous aircraft",
    },
    {
        "id": "aerospace",
        "product_class": "aerospace",
        "label": "Aerospace",
        "hint": "Satellites, rockets, orbital debris and space robots",
    },
    {
        "id": "construction",
        "product_class": "construction",
        "label": "Construction",
        "hint": "Homes and buildings — framing, print, jobsite finish",
    },
    {
        "id": "healthcare",
        "product_class": "healthcare",
        "label": "Healthcare",
        "hint": "Hospital and clinical work — delivery, pharmacy, linen, nursing assist",
    },
]


def public_class_options() -> list[dict[str, str]]:
    return [
        {"id": row["id"], "label": row["label"], "hint": row["hint"]}
        for row in CLASS_OPTIONS
    ]


def normalize_class_id(raw: str | None) -> str | None:
    want = (raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "humanoid": "humanoid",
        "biped": "humanoid",
        "bipedal": "humanoid",
        "amr": "amr",
        "agv": "amr",
        "mobile_robot": "amr",
        "mobile_manipulator": "mobile_manipulator",
        "cobot": "cobot",
        "arm": "cobot",
        "collaborative": "cobot",
        "quadruped": "quadruped",
        "spot": "quadruped",
        "scrubber": "autonomous_scrubber",
        "autonomous_scrubber": "autonomous_scrubber",
        "forklift": "amr",
        "agriculture": "agriculture",
        "agricultural_robot": "agriculture",
        "farm_robot": "agriculture",
        "weeder": "agriculture",
        "weeding": "agriculture",
        "combine": "agriculture",
        "tractor": "agriculture",
        "autonomous_tractor": "agriculture",
        "autonomous_combine": "agriculture",
        "marine": "marine",
        "marine_robot": "marine",
        "maritime": "marine",
        "underwater": "marine",
        "avionics": "avionics",
        "aviation": "avionics",
        "aviation_robot": "avionics",
        "drone": "avionics",
        "uav": "avionics",
        "evtol": "avionics",
        "e_vtol": "avionics",
        "flying_car": "avionics",
        "autonomous_aircraft": "avionics",
        "autonomous_plane": "avionics",
        "aircraft": "avionics",
        "hangar": "avionics",
        "airside": "avionics",
        "aerospace": "aerospace",
        "aerospace_robot": "aerospace",
        "satellite": "aerospace",
        "orbital": "aerospace",
        "space_robot": "aerospace",
        "space_debris": "aerospace",
        "rocket": "aerospace",
        "construction": "construction",
        "construction_robot": "construction",
        "homebuilding": "construction",
        "homebuilder": "construction",
        "healthcare": "healthcare",
        "healthcare_robot": "healthcare",
        "medical": "healthcare",
        "medical_robot": "healthcare",
        "clinical": "healthcare",
        "clinical_robot": "healthcare",
        "hospital": "healthcare",
        "hospital_robot": "healthcare",
        "nursing": "healthcare",
        "pharmacy": "healthcare",
    }
    mapped = aliases.get(want)
    if not mapped:
        from app.services.robot_ontology import industry_class_aliases

        mapped = industry_class_aliases().get(want)
    if mapped:
        return mapped
    if any(row["id"] == want for row in CLASS_OPTIONS):
        return want
    return None


def infer_class_from_work_language(text: str) -> str | None:
    """FIND class from ontology industry work language (R33). Single source."""
    from app.services.robot_ontology import find_class_from_work_language

    return find_class_from_work_language(text)


# FIND tiles the operator picks with no SKU. A named SKU class is not a tile.
FIND_TILE_CLASSES: frozenset[str] = frozenset(row["id"] for row in CLASS_OPTIONS)

# SKU configuration classes. Type-first lookup must stamp the configuration,
# never company → category → jobs. eVTOL stays eVTOL (not Avionics).
# agricultural_robot / construction_robot stay themselves (not the parent tile).
_CONFIGURATION_PRODUCT_CLASSES: dict[str, tuple[str, str]] = {
    "evtol": ("evtol", "eVTOL"),
    "e_vtol": ("evtol", "eVTOL"),
    "flying_car": ("evtol", "eVTOL"),
    "drone": ("drone", "Drone"),
    "uav": ("drone", "Drone"),
    "autonomous_aircraft": ("autonomous_aircraft", "Autonomous aircraft"),
    "autonomous_plane": ("autonomous_aircraft", "Autonomous aircraft"),
    "agricultural_robot": ("agricultural_robot", "Agricultural robot"),
    "farm_robot": ("agricultural_robot", "Agricultural robot"),
    "weeder": ("agricultural_robot", "Agricultural robot"),
    "weeding": ("agricultural_robot", "Agricultural robot"),
    "combine": ("agricultural_robot", "Agricultural robot"),
    "tractor": ("agricultural_robot", "Agricultural robot"),
    "autonomous_tractor": ("agricultural_robot", "Agricultural robot"),
    "autonomous_combine": ("agricultural_robot", "Agricultural robot"),
    "construction_robot": ("construction_robot", "Construction robot"),
    "homebuilding": ("construction_robot", "Construction robot"),
    "homebuilder": ("construction_robot", "Construction robot"),
    "construction_print": ("construction_robot", "Construction robot"),
    "construction_block": ("construction_robot", "Construction robot"),
    "construction_layout": ("construction_robot", "Construction robot"),
}


def lookup_class_id(raw: str | None) -> str | None:
    """Class used to match jobs: SKU configuration over the parent FIND tile."""
    want = (raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    if want in _CONFIGURATION_PRODUCT_CLASSES:
        return _CONFIGURATION_PRODUCT_CLASSES[want][0]
    return normalize_class_id(raw)


def resolve_asserted_product_class(class_id: str | None) -> tuple[str, str] | None:
    """Return ``(product_class, label)`` for a picker tile or a SKU configuration."""
    want = (class_id or "").strip().lower().replace(" ", "_").replace("-", "_")
    if want in _CONFIGURATION_PRODUCT_CLASSES:
        return _CONFIGURATION_PRODUCT_CLASSES[want]
    nid = normalize_class_id(class_id)
    if not nid:
        return None
    row = next(r for r in CLASS_OPTIONS if r["id"] == nid)
    return row["product_class"], row["label"]


def apply_asserted_class(profile: dict[str, Any], class_id: str) -> dict[str, Any]:
    """Stamp operator-selected product_class onto a profile dict and rematch."""
    resolved = resolve_asserted_product_class(class_id)
    if not resolved:
        return profile
    cls, label = resolved
    out = copy.deepcopy(profile)
    subject = (
        ((out.get("selected_product") or {}).get("name"))
        or ((out.get("company") or {}).get("name"))
        or "robot"
    )
    facts = [
        f
        for f in (out.get("facts") or [])
        if not (isinstance(f, dict) and f.get("predicate") == "product_class")
    ]
    facts.insert(
        0,
        {
            "id": "fact_operator_class",
            "subject": subject,
            "predicate": "product_class",
            "value": cls,
            "units": None,
            "epistemic": "explicit",
            "source_id": "operator_qualification",
            "confidence": 0.95,
            "evidence_span": f"Operator selected robot class: {label}",
        },
    )
    out["facts"] = facts
    selected = dict(out.get("selected_product") or {})
    if selected:
        selected["display_class"] = cls
        out["selected_product"] = selected
    out["research_morphology"] = cls
    if (out.get("coverage_level") or "").lower() == "low":
        out["coverage_level"] = "medium"
    notes = list(out.get("notes") or [])
    notes.append(f"Operator qualified class as {cls}.")
    out["notes"] = notes
    return out


def thin_class_profile(
    company: str,
    class_id: str,
    *,
    source_url: str | None = None,
) -> dict[str, Any]:
    """Grounded-enough profile to match jobs for a robot *type*.

    Used when the operator listed a group of SKUs that share a class
    (Fourier GR-1/GR-2/GR-3 are all humanoid). Does not scrape a product
    page. The matcher still inspects requirements from product_class
    derivations — this is not a family dump. Named SKU classes
    (eVTOL, drone, agricultural_robot, construction_robot) stay
    configuration; they are not remapped onto a FIND tile.
    """
    resolved = resolve_asserted_product_class(class_id)
    if not resolved:
        return {
            "company": {"name": (company or "").strip() or "your robot"},
            "selected_product": None,
            "facts": [],
            "sources": [],
            "coverage_level": "low",
            "needs_product_choice": False,
        }
    cls, label = resolved
    company_name = (company or "").strip() or "your robot"
    sources = []
    if source_url:
        sources.append(
            {
                "id": "src_type_lookup",
                "url": source_url,
                "source_type": "other",
                "title": f"{label} type lookup",
                "publisher_role": "operator",
                "confidence": 0.9,
            }
        )
    base: dict[str, Any] = {
        "company": {"name": company_name},
        "selected_product": {"name": label, "display_class": cls},
        "products": [],
        "facts": [],
        "sources": sources,
        "coverage_level": "medium",
        "profile_confidence": "B",
        "needs_product_choice": False,
        "notes": [f"Type-first job lookup for {cls}."],
    }
    return apply_asserted_class(base, cls)
