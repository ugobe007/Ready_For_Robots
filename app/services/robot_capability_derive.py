"""
Phase 4 (M2) — derive capabilities from frozen Understanding facts.

Extractors stay closed. This module only reads grounded facts already on a
Robot Profile and names primitives the matcher can inspect.

Forbidden: robot type → family → jobs. A product_class fact may support a
named derivation (documented below); it does not select a job family.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

GROUNDED = frozenset({"explicit", "strongly_inferred"})

# product_class values that are themselves evidence of a manipulation morphology
MANIP_CLASSES = frozenset(
    {"mobile_manipulator", "humanoid", "cobot", "manipulator", "arm"}
)
SCRUB_CLASSES = frozenset({"autonomous_scrubber", "scrubber"})
TRANSPORT_CLASSES = frozenset({"amr"})
INSPECT_CLASSES = frozenset({"quadruped"})
GRASP_EFFECTORS = frozenset({"dexterous_hand", "gripper", "vacuum", "suction"})


@dataclass
class DerivedCapability:
    key: str
    label: str
    present: bool
    derivation: str  # "explicit" | "inferred"
    derived_from: list[str] = field(default_factory=list)
    evidence: Optional[str] = None
    value: Any = None
    units: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "present": self.present,
            "derivation": self.derivation,
            "derived_from": list(self.derived_from),
            "evidence": self.evidence,
            "value": self.value,
            "units": self.units,
        }


def _grounded_facts(profile: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for f in profile.get("facts") or []:
        if (f.get("epistemic") or "") not in GROUNDED:
            continue
        if f.get("value") in (None, "", "UNKNOWN"):
            continue
        out.append(f)
    return out


def _values(facts: Iterable[dict[str, Any]], predicate: str) -> list[dict[str, Any]]:
    return [f for f in facts if f.get("predicate") == predicate]


def _truthy(facts: Iterable[dict[str, Any]], predicate: str) -> Optional[dict[str, Any]]:
    for f in _values(facts, predicate):
        val = f.get("value")
        if val is True or val == "true" or val == 1:
            return f
    return None


def _classes(facts: Iterable[dict[str, Any]]) -> set[str]:
    return {str(f.get("value") or "").lower() for f in _values(facts, "product_class")}


def derive_capabilities(profile: dict[str, Any]) -> dict[str, DerivedCapability]:
    """Return capability key → DerivedCapability from a frozen profile dict."""
    facts = _grounded_facts(profile)
    caps: dict[str, DerivedCapability] = {}
    classes = _classes(facts)

    arm_facts = _values(facts, "arm_count")
    arm_count = None
    arm_fact = None
    for f in arm_facts:
        try:
            n = int(float(f.get("value")))
        except (TypeError, ValueError):
            continue
        if arm_count is None or n > arm_count:
            arm_count = n
            arm_fact = f

    hands = _truthy(facts, "has_dexterous_hands")
    effector_facts = _values(facts, "end_effector")
    effector_ok = next(
        (f for f in effector_facts if str(f.get("value") or "").lower() in GRASP_EFFECTORS),
        None,
    )
    manip_class = next((c for c in classes if c in MANIP_CLASSES), None)

    manipulate = bool(arm_count and arm_count >= 1) or bool(hands) or bool(effector_ok) or bool(
        manip_class
    )
    if manipulate:
        derived_from = []
        evidence_bits = []
        derivation = "inferred"
        if arm_fact:
            derived_from.append("arm_count")
            evidence_bits.append(arm_fact.get("evidence_span") or f"arm_count={arm_count}")
            derivation = "explicit"
        if hands:
            derived_from.append("has_dexterous_hands")
            evidence_bits.append(hands.get("evidence_span") or "dexterous hands")
            derivation = "explicit"
        if effector_ok:
            derived_from.append("end_effector")
            evidence_bits.append(effector_ok.get("evidence_span") or str(effector_ok.get("value")))
            derivation = "explicit"
        if manip_class and not derived_from:
            derived_from.append("product_class")
            evidence_bits.append(manip_class)
            derivation = "inferred"
        label = "dual-arm manipulation" if (arm_count or 0) >= 2 else "manipulation"
        caps["manipulate"] = DerivedCapability(
            key="manipulate",
            label=label,
            present=True,
            derivation=derivation,
            derived_from=derived_from,
            evidence="; ".join(str(x) for x in evidence_bits if x),
            value=arm_count,
        )
    else:
        caps["manipulate"] = DerivedCapability(
            key="manipulate",
            label="manipulation",
            present=False,
            derivation="explicit",
            derived_from=["arm_count", "has_dexterous_hands", "end_effector", "product_class"],
            evidence="no grounded arm, hand, effector, or manipulator class",
        )

    if (arm_count or 0) >= 2:
        caps["dual_arm"] = DerivedCapability(
            key="dual_arm",
            label="dual-arm manipulation",
            present=True,
            derivation="explicit",
            derived_from=["arm_count"],
            evidence=(arm_fact or {}).get("evidence_span") or f"arm_count={arm_count}",
            value=arm_count,
        )

    mobile_base = _truthy(facts, "has_mobile_base")
    nav = _truthy(facts, "autonomous_navigation")
    mobility_arch = _values(facts, "mobility_architecture")
    mobile_class = bool(classes & (TRANSPORT_CLASSES | INSPECT_CLASSES | SCRUB_CLASSES | {"mobile_manipulator", "humanoid"}))
    mobile = bool(mobile_base or nav or mobility_arch or mobile_class)
    if mobile:
        derived_from = []
        evidence_bits = []
        derivation = "inferred"
        if mobile_base:
            derived_from.append("has_mobile_base")
            evidence_bits.append(mobile_base.get("evidence_span") or "mobile base")
            derivation = "explicit"
        if nav:
            derived_from.append("autonomous_navigation")
            evidence_bits.append(nav.get("evidence_span") or "autonomous navigation")
            derivation = "explicit"
        if mobility_arch:
            derived_from.append("mobility_architecture")
            evidence_bits.append(str(mobility_arch[0].get("value")))
            derivation = "explicit"
        if not derived_from and mobile_class:
            derived_from.append("product_class")
            evidence_bits.append(",".join(sorted(classes)))
        caps["mobile"] = DerivedCapability(
            key="mobile",
            label="mobile platform",
            present=True,
            derivation=derivation,
            derived_from=derived_from,
            evidence="; ".join(str(x) for x in evidence_bits if x),
        )
    else:
        caps["mobile"] = DerivedCapability(
            key="mobile",
            label="mobile platform",
            present=False,
            derivation="explicit",
            derived_from=["has_mobile_base", "autonomous_navigation", "product_class"],
            evidence="no grounded mobility",
        )

    tote = _truthy(facts, "supports_tote_handling")
    warehouse_transport = _truthy(facts, "claims_warehouse_transport")
    if tote or warehouse_transport:
        derived_from = []
        evidence_bits = []
        if tote:
            derived_from.append("supports_tote_handling")
            evidence_bits.append(tote.get("evidence_span") or "tote handling")
        if warehouse_transport:
            derived_from.append("claims_warehouse_transport")
            evidence_bits.append(warehouse_transport.get("evidence_span") or "warehouse transport")
        caps["tote_transport"] = DerivedCapability(
            key="tote_transport",
            label="tote / warehouse transport",
            present=True,
            derivation="explicit",
            derived_from=derived_from,
            evidence="; ".join(str(x) for x in evidence_bits if x),
        )
    else:
        caps["tote_transport"] = DerivedCapability(
            key="tote_transport",
            label="tote / warehouse transport",
            present=False,
            derivation="explicit",
            derived_from=["supports_tote_handling", "claims_warehouse_transport"],
        )

    # Autonomous item delivery / transport (service & delivery robots). Distinct
    # from warehouse tote handling: a hospitality/healthcare delivery robot carries
    # and delivers items point-to-point. Grounded from an explicit delivery claim.
    delivery = _truthy(facts, "claims_item_delivery")
    if delivery:
        caps["transport"] = DerivedCapability(
            key="transport",
            label="autonomous item transport / delivery",
            present=True,
            derivation="explicit",
            derived_from=["claims_item_delivery"],
            evidence=delivery.get("evidence_span") or "item delivery / transport",
        )
    else:
        caps["transport"] = DerivedCapability(
            key="transport",
            label="autonomous item transport / delivery",
            present=False,
            derivation="explicit",
            derived_from=["claims_item_delivery"],
        )

    # Food preparation / cooking (kitchen robots). Distinct dexterous capability —
    # deliberately NOT generic `manipulate`, so a fry/assembly robot maps to food
    # work rather than falsely matching industrial CNC/case handling.
    food_prep = _truthy(facts, "claims_food_prep")
    caps["food_prep"] = DerivedCapability(
        key="food_prep",
        label="food preparation / cooking",
        present=bool(food_prep),
        derivation="explicit",
        derived_from=["claims_food_prep"],
        evidence=(food_prep or {}).get("evidence_span") if food_prep else None,
    )

    # Beverage / drink preparation (barista & bartender robots).
    beverage = _truthy(facts, "claims_beverage_prep")
    caps["beverage_prep"] = DerivedCapability(
        key="beverage_prep",
        label="beverage / drink preparation",
        present=bool(beverage),
        derivation="explicit",
        derived_from=["claims_beverage_prep"],
        evidence=(beverage or {}).get("evidence_span") if beverage else None,
    )

    # Surface / restroom cleaning (fixtures, restrooms, carpet/vacuum) — broader
    # than hard-floor scrubbing, which stays its own capability.
    surface_clean = _truthy(facts, "claims_surface_cleaning")
    caps["surface_clean"] = DerivedCapability(
        key="surface_clean",
        label="surface / restroom cleaning",
        present=bool(surface_clean),
        derivation="explicit",
        derived_from=["claims_surface_cleaning"],
        evidence=(surface_clean or {}).get("evidence_span") if surface_clean else None,
    )

    # Retail shelf / inventory scanning (autonomous inventory robots, e.g. Simbe
    # Tally). A distinct perception capability — scan, not manipulate/transport.
    shelf_scan = _truthy(facts, "claims_shelf_scan")
    caps["shelf_scan"] = DerivedCapability(
        key="shelf_scan",
        label="shelf / inventory scanning",
        present=bool(shelf_scan),
        derivation="explicit",
        derived_from=["claims_shelf_scan"],
        evidence=(shelf_scan or {}).get("evidence_span") if shelf_scan else None,
    )

    scrub = _truthy(facts, "supports_hard_floor_scrubbing")
    if scrub:
        caps["hard_floor_scrub"] = DerivedCapability(
            key="hard_floor_scrub",
            label="hard-floor scrubbing",
            present=True,
            derivation="explicit",
            derived_from=["supports_hard_floor_scrubbing"],
            evidence=scrub.get("evidence_span") or "hard-floor scrubbing",
        )
    elif classes & SCRUB_CLASSES:
        caps["hard_floor_scrub"] = DerivedCapability(
            key="hard_floor_scrub",
            label="hard-floor scrubbing",
            present=True,
            derivation="inferred",
            derived_from=["product_class"],
            evidence="autonomous_scrubber class",
        )
    else:
        caps["hard_floor_scrub"] = DerivedCapability(
            key="hard_floor_scrub",
            label="hard-floor scrubbing",
            present=False,
            derivation="explicit",
            derived_from=["supports_hard_floor_scrubbing", "product_class"],
        )

    if classes & INSPECT_CLASSES:
        caps["inspect_route"] = DerivedCapability(
            key="inspect_route",
            label="mobile inspection route",
            present=True,
            derivation="inferred",
            derived_from=["product_class"],
            evidence="quadruped morphology — named derivation inspect_from_quadruped",
        )
    else:
        caps["inspect_route"] = DerivedCapability(
            key="inspect_route",
            label="mobile inspection route",
            present=False,
            derivation="explicit",
            derived_from=["product_class"],
        )

    reach_facts = _values(facts, "reach_or_workspace")
    reach = None
    reach_fact = None
    for f in reach_facts:
        try:
            reach = float(f.get("value"))
            reach_fact = f
            break
        except (TypeError, ValueError):
            continue
    if reach is not None and reach_fact is not None:
        units = reach_fact.get("units") or "m"
        caps["reach"] = DerivedCapability(
            key="reach",
            label=f"working reach {reach} {units}".strip(),
            present=True,
            derivation="explicit",
            derived_from=["reach_or_workspace"],
            evidence=reach_fact.get("evidence_span") or f"{reach} {units}",
            value=reach,
            units=units,
        )
    else:
        caps["reach"] = DerivedCapability(
            key="reach",
            label="working reach",
            present=False,
            derivation="explicit",
            derived_from=["reach_or_workspace"],
        )

    payload_facts = _values(facts, "carrying_capacity")
    if payload_facts:
        pf = payload_facts[0]
        caps["payload"] = DerivedCapability(
            key="payload",
            label=f"payload {pf.get('value')} {pf.get('units') or ''}".strip(),
            present=True,
            derivation="explicit",
            derived_from=["carrying_capacity"],
            evidence=pf.get("evidence_span"),
            value=pf.get("value"),
            units=pf.get("units"),
        )
    else:
        caps["payload"] = DerivedCapability(
            key="payload",
            label="payload",
            present=False,
            derivation="explicit",
            derived_from=["carrying_capacity"],
        )

    load_unload = _truthy(facts, "claims_load_unload")
    caps["load_unload"] = DerivedCapability(
        key="load_unload",
        label="load / unload (claimed)",
        present=bool(load_unload),
        derivation="explicit" if load_unload else "explicit",
        derived_from=["claims_load_unload"],
        evidence=(load_unload or {}).get("evidence_span") if load_unload else None,
    )

    caps["classes"] = DerivedCapability(
        key="classes",
        label="product class",
        present=bool(classes),
        derivation="explicit",
        derived_from=["product_class"],
        value=sorted(classes),
        evidence=",".join(sorted(classes)) if classes else None,
    )
    return caps
