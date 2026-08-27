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
        "hint": "Field and crop work — weeding, spraying, harvest",
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
        "hint": "Hangar and airside aircraft work — not a consumer drone",
    },
    {
        "id": "construction",
        "product_class": "construction",
        "label": "Construction",
        "hint": "Jobsite earthwork, layout, and finishing",
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
        "marine": "marine",
        "marine_robot": "marine",
        "maritime": "marine",
        "underwater": "marine",
        "avionics": "avionics",
        "aviation": "avionics",
        "aviation_robot": "avionics",
        "aircraft": "avionics",
        "hangar": "avionics",
        "airside": "avionics",
        "construction": "construction",
        "construction_robot": "construction",
    }
    mapped = aliases.get(want)
    if mapped:
        return mapped
    if any(row["id"] == want for row in CLASS_OPTIONS):
        return want
    return None


def apply_asserted_class(profile: dict[str, Any], class_id: str) -> dict[str, Any]:
    """Stamp operator-selected product_class onto a profile dict and rematch."""
    nid = normalize_class_id(class_id)
    if not nid:
        return profile
    row = next(r for r in CLASS_OPTIONS if r["id"] == nid)
    cls = row["product_class"]
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
            "evidence_span": f"Operator selected robot class: {row['label']}",
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
    derivations — this is not a family dump.
    """
    nid = normalize_class_id(class_id)
    if not nid:
        return {
            "company": {"name": (company or "").strip() or "your robot"},
            "selected_product": None,
            "facts": [],
            "sources": [],
            "coverage_level": "low",
            "needs_product_choice": False,
        }
    row = next(r for r in CLASS_OPTIONS if r["id"] == nid)
    company_name = (company or "").strip() or "your robot"
    sources = []
    if source_url:
        sources.append(
            {
                "id": "src_type_lookup",
                "url": source_url,
                "source_type": "other",
                "title": f"{row['label']} type lookup",
                "publisher_role": "operator",
                "confidence": 0.9,
            }
        )
    base: dict[str, Any] = {
        "company": {"name": company_name},
        "selected_product": {"name": row["label"], "display_class": nid},
        "products": [],
        "facts": [],
        "sources": sources,
        "coverage_level": "medium",
        "profile_confidence": "B",
        "needs_product_choice": False,
        "notes": [f"Type-first job lookup for {nid}."],
    }
    return apply_asserted_class(base, nid)
