"""
Phase 4 (M2) — derive capabilities from frozen Understanding facts.

Extractors stay closed. This module only reads grounded facts already on a
Robot Profile and names primitives the matcher can inspect.

Forbidden: robot type → family → jobs. A product_class fact may support a
named derivation (documented below); it does not select a job family.
"""
from __future__ import annotations

import re
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
AGRICULTURE_CLASSES = frozenset({"agriculture", "agricultural_robot", "farm_robot"})
MARINE_CLASSES = frozenset({"marine", "marine_robot"})
AVIONICS_CLASSES = frozenset(
    {"avionics", "aviation_robot", "drone", "evtol", "uav", "autonomous_aircraft"}
)
# Configuration splits inside avionics. Generic avionics/aviation_robot (FIND
# tile) is the flying-work union. A named SKU class is not that union:
# eVTOL is air-taxi flight, not Spot-like ramp walking.
EVTOL_CLASSES = frozenset({"evtol"})
DRONE_CLASSES = frozenset({"drone", "uav"})
AUTONOMOUS_AIRCRAFT_CLASSES = frozenset({"autonomous_aircraft"})
GENERIC_AVIONICS_CLASSES = frozenset({"avionics", "aviation_robot"})
AEROSPACE_CLASSES = frozenset({"aerospace", "aerospace_robot"})
CONSTRUCTION_CLASSES = frozenset({"construction", "construction_robot"})
HEALTHCARE_CLASSES = frozenset(
    {
        "healthcare",
        "healthcare_robot",
        "medical_robot",
        "clinical_robot",
        "hospital_robot",
    }
)
# FIND-tile unions. Named SKUs use agricultural_robot / construction_robot plus
# a work-kind claim — never company → category → jobs.
GENERIC_AGRICULTURE_CLASSES = frozenset({"agriculture"})
GENERIC_CONSTRUCTION_CLASSES = frozenset({"construction"})
DOMAIN_WORK_CLASSES = (
    AGRICULTURE_CLASSES
    | MARINE_CLASSES
    | AVIONICS_CLASSES
    | AEROSPACE_CLASSES
    | CONSTRUCTION_CLASSES
    | HEALTHCARE_CLASSES
)
# Hospital / clinical assistant work — ontology work language, not a torso class.
# SKU names are not the source; hospital/clinical terms live in the ontology.
GRASP_EFFECTORS = frozenset({"dexterous_hand", "gripper", "vacuum", "suction"})

# Named weeding SKUs (LaserWeeder, FarmDroid). Identity is the configuration,
# not a company → category dump and not a cobot because the page said "laser".
_WEEDING_IDENTITY = re.compile(
    r"laserweeder|laser\s+weeder|laser[- ]weed|farmdroid",
    re.I,
)


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


def weeding_configuration_identity(profile: dict[str, Any]) -> bool:
    """True when this configuration is crop-weeding work.

    LaserWeeder / FarmDroid must ground weeding even if Understanding missed
    product_class. Incidental gripper/arm language must not open CNC.
    """
    facts = _grounded_facts(profile)
    if _truthy(facts, "claims_weeding"):
        return True
    company = ((profile.get("company") or {}).get("name") or "")
    product = ((profile.get("selected_product") or {}).get("name") or "")
    url = str(profile.get("submitted_url") or profile.get("source_url") or "")
    blob = f"{company} {product} {url}"
    return bool(_WEEDING_IDENTITY.search(blob))


def healthcare_work_identity(profile: dict[str, Any]) -> bool:
    """True when this configuration is hospital / clinical assistant work.

    Moxi is not a humanoid because it has a torso. Identity is the clinical
    work (meds, specimens, linen, nursing assist), not morphology. Vocabulary
    comes from ontology industry work language (R33), not a SKU deny list.
    """
    from app.services.robot_ontology import match_work_language

    facts = _grounded_facts(profile)
    if _truthy(facts, "claims_healthcare"):
        return True
    if _classes(facts) & HEALTHCARE_CLASSES:
        return True
    env = {
        str(f.get("value") or "").lower()
        for f in _values(facts, "operating_environment")
    }
    if env & {"healthcare", "eldercare"}:
        return True
    company = ((profile.get("company") or {}).get("name") or "")
    product = ((profile.get("selected_product") or {}).get("name") or "")
    url = str(profile.get("submitted_url") or profile.get("source_url") or "")
    spans = " ".join(
        str(f.get("evidence_span") or "")
        for f in facts
        if f.get("predicate")
        in {"claims_item_delivery", "operating_environment", "product_class"}
    )
    blob = f"{company} {product} {url} {spans}"
    hit = match_work_language(blob)
    return bool(hit and hit.industry_id == "healthcare")


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
    weeding_identity = weeding_configuration_identity(profile)
    clinical_identity = healthcare_work_identity(profile)
    # Domain configurations (eVTOL, drone, combine, Vulcan, LaserWeeder, …)
    # are not factory cobots. Incidental "arm"/"gripper"/"laser" language on
    # an OEM page must not ground manipulate and open the CNC/pack corpus.
    if (
        (classes & DOMAIN_WORK_CLASSES or weeding_identity or clinical_identity)
        and not (classes & MANIP_CLASSES)
    ):
        manipulate = False
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
    mobile_class = bool(
        classes
        & (
            TRANSPORT_CLASSES
            | INSPECT_CLASSES
            | SCRUB_CLASSES
            | DOMAIN_WORK_CLASSES
            | {"mobile_manipulator", "humanoid", "autonomous_forklift"}
        )
    )
    # These Tier 1–3 domain functions are inherently mobile — a forklift, field,
    # jobsite, mining, room-disinfection, or ASRS robot traverses its worksite.
    # (Only the NEW capabilities — never in frozen fixtures — so boards are safe.)
    domain_mobile = any(
        _truthy(facts, p)
        for p in (
            "claims_pallet_handling", "claims_agriculture", "claims_healthcare",
            "claims_construction",
            "claims_mining", "claims_marine", "claims_avionics", "claims_aerospace",
            "claims_disinfection", "claims_goods_to_person",
        )
    )
    mobile = bool(
        mobile_base or nav or mobility_arch or mobile_class or domain_mobile
        or weeding_identity or clinical_identity
    )
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
    elif classes & TRANSPORT_CLASSES:
        # Named derivation: product_class=amr → transport work primitive.
        # Does not select a job family; the matcher still inspects requirements.
        caps["transport"] = DerivedCapability(
            key="transport",
            label="autonomous item transport / delivery",
            present=True,
            derivation="inferred",
            derived_from=["product_class"],
            evidence="amr class",
        )
    else:
        caps["transport"] = DerivedCapability(
            key="transport",
            label="autonomous item transport / delivery",
            present=False,
            derivation="explicit",
            derived_from=["claims_item_delivery", "product_class"],
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

    # Tier 1–3 distinct capabilities (each grounded from its own claim, never
    # generic manipulate — keeps a forklift/sorter/UV robot out of unrelated work).
    for _key, _pred, _label, _cls in (
        ("pallet_move", "claims_pallet_handling", "pallet handling / forklift", frozenset()),
        ("trailer_unload", "claims_trailer_unload", "trailer / container unloading", frozenset()),
        ("pick_pack", "claims_piece_pick", "piece picking / pack", frozenset()),
        ("sortation", "claims_sortation", "parcel sortation", frozenset()),
        ("disinfect", "claims_disinfection", "UV / surface disinfection", frozenset()),
        ("goods_to_person", "claims_goods_to_person", "ASRS goods-to-person", frozenset()),
        ("agriculture_task", "claims_agriculture", "agricultural field work", AGRICULTURE_CLASSES),
        ("healthcare_task", "claims_healthcare", "hospital / clinical assistant work", HEALTHCARE_CLASSES),
        ("construction_task", "claims_construction", "construction site work", CONSTRUCTION_CLASSES),
        ("mining_task", "claims_mining", "mining / haulage", frozenset()),
        ("marine_task", "claims_marine", "hull / port / underwater work", MARINE_CLASSES),
        ("avionics_task", "claims_avionics", "drone / eVTOL / autonomous aircraft work", AVIONICS_CLASSES),
        ("aerospace_task", "claims_aerospace", "satellite / orbital / space-robot work", AEROSPACE_CLASSES),
    ):
        _fact = _truthy(facts, _pred)
        _class_hit = next((c for c in classes if c in _cls), None)
        if _fact:
            caps[_key] = DerivedCapability(
                key=_key,
                label=_label,
                present=True,
                derivation="explicit",
                derived_from=[_pred],
                evidence=_fact.get("evidence_span"),
            )
        elif _class_hit:
            caps[_key] = DerivedCapability(
                key=_key,
                label=_label,
                present=True,
                derivation="inferred",
                derived_from=["product_class"],
                evidence=f"{_class_hit} class",
            )
        else:
            caps[_key] = DerivedCapability(
                key=_key,
                label=_label,
                present=False,
                derivation="explicit",
                derived_from=[_pred, "product_class"],
            )

    # R28: avionics configurations — eVTOL flight ≠ drone inspect ≠ airplane
    # flight ≠ hangar/airside walking. claims_avionics without a subclass is
    # the FIND-tile union of flying work, not a dump onto every SKU.
    specific_avionics = classes & (EVTOL_CLASSES | DRONE_CLASSES | AUTONOMOUS_AIRCRAFT_CLASSES)
    avionics_claim = _truthy(facts, "claims_avionics")
    generic_avionics = bool(classes & GENERIC_AVIONICS_CLASSES) or (
        bool(avionics_claim) and not specific_avionics
    )
    for _key, _label, _cls, _evidence in (
        (
            "evtol_flight",
            "eVTOL passenger/cargo flight",
            EVTOL_CLASSES,
            "evtol class — air taxi / flying-car flight, not ramp walking",
        ),
        (
            "drone_task",
            "drone inspect / delivery flight",
            DRONE_CLASSES,
            "drone / UAV class — aerial inspect or delivery",
        ),
        (
            "autonomous_flight",
            "autonomous airplane-like flight",
            AUTONOMOUS_AIRCRAFT_CLASSES,
            "autonomous_aircraft class — airplane-like IFR flight",
        ),
    ):
        _hit = next((c for c in classes if c in _cls), None)
        if _hit or generic_avionics:
            if _hit:
                caps[_key] = DerivedCapability(
                    key=_key,
                    label=_label,
                    present=True,
                    derivation="inferred",
                    derived_from=["product_class"],
                    evidence=_evidence,
                )
            elif classes & GENERIC_AVIONICS_CLASSES:
                caps[_key] = DerivedCapability(
                    key=_key,
                    label=_label,
                    present=True,
                    derivation="inferred",
                    derived_from=["product_class"],
                    evidence="avionics class — flying-vehicle configuration union",
                )
            else:
                caps[_key] = DerivedCapability(
                    key=_key,
                    label=_label,
                    present=True,
                    derivation="explicit",
                    derived_from=["claims_avionics"],
                    evidence=(avionics_claim or {}).get("evidence_span") or "claims_avionics",
                )
        else:
            caps[_key] = DerivedCapability(
                key=_key,
                label=_label,
                present=False,
                derivation="explicit",
                derived_from=["product_class"],
            )

    # R27: implement on a tractor/combine is a configuration, not a class.
    if not caps.get("agriculture_task") or not caps["agriculture_task"].present:
        kind = next((str(f.get("value") or "").lower() for f in _values(facts, "configuration_kind")), "")
        host = next((str(f.get("value") or "").lower() for f in _values(facts, "host_platform")), "")
        if kind == "implement_on_host" and host in {"tractor", "combine"}:
            caps["agriculture_task"] = DerivedCapability(
                key="agriculture_task",
                label="agricultural field work",
                present=True,
                derivation="inferred",
                derived_from=["configuration_kind", "host_platform"],
                evidence=f"implement on {host}",
            )
            if not caps.get("mobile") or not caps["mobile"].present:
                caps["mobile"] = DerivedCapability(
                    key="mobile",
                    label="mobile platform",
                    present=True,
                    derivation="inferred",
                    derived_from=["host_platform"],
                    evidence=f"{host} host",
                )
        elif weeding_identity:
            caps["agriculture_task"] = DerivedCapability(
                key="agriculture_task",
                label="agricultural field work",
                present=True,
                derivation="inferred",
                derived_from=["selected_product"],
                evidence="named weeding SKU",
            )

    if (not caps.get("healthcare_task") or not caps["healthcare_task"].present) and clinical_identity:
        caps["healthcare_task"] = DerivedCapability(
            key="healthcare_task",
            label="hospital / clinical assistant work",
            present=True,
            derivation="inferred",
            derived_from=["claims_item_delivery", "operating_environment"],
            evidence="hospital / clinical delivery work — not a humanoid torso class",
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

    # R30: SKU work-kind inside agriculture / construction. FIND tile
    # (product_class=agriculture|construction) is the union. A named SKU only
    # grounds the work its listed_class/task claims — LaserWeeder is weeding,
    # not combine harvest; Vulcan is 3D-print home, not block-lay.
    generic_ag = bool(classes & GENERIC_AGRICULTURE_CLASSES)
    generic_con = bool(classes & GENERIC_CONSTRUCTION_CLASSES)
    for _key, _pred, _label, _union in (
        ("agriculture_weed", "claims_weeding", "crop weeding", generic_ag and not weeding_identity),
        ("agriculture_combine", "claims_combine_harvest", "combine grain harvest", generic_ag and not weeding_identity),
        ("agriculture_spray", "claims_precision_spray", "precision crop spray", generic_ag and not weeding_identity),
        ("agriculture_tractor", "claims_tractor_work", "autonomous tractor field work", generic_ag and not weeding_identity),
        ("construction_print", "claims_construction_print", "3D-print home / building walls", generic_con),
        ("construction_block", "claims_construction_block", "block / brick laying", generic_con),
        ("construction_layout", "claims_construction_layout", "jobsite floor layout print", generic_con),
    ):
        _fact = _truthy(facts, _pred)
        if _fact:
            caps[_key] = DerivedCapability(
                key=_key,
                label=_label,
                present=True,
                derivation="explicit",
                derived_from=[_pred],
                evidence=_fact.get("evidence_span") or _pred,
            )
        elif _key == "agriculture_weed" and weeding_identity:
            caps[_key] = DerivedCapability(
                key=_key,
                label=_label,
                present=True,
                derivation="inferred",
                derived_from=["selected_product"],
                evidence="named weeding SKU — not a cutting-laser cell",
            )
        elif _union:
            caps[_key] = DerivedCapability(
                key=_key,
                label=_label,
                present=True,
                derivation="inferred",
                derived_from=["product_class"],
                evidence="FIND-tile work union — not a SKU dump",
            )
        else:
            caps[_key] = DerivedCapability(
                key=_key,
                label=_label,
                present=False,
                derivation="explicit",
                derived_from=[_pred, "product_class"],
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
