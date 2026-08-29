"""
Research checklists for Phase 3 profile completeness.

These are descriptive research slots — NOT job-matching ontology.
Purpose: Have we researched this robot enough to describe it professionally?
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.services.robot_understanding_v1.models import RobotFact

Morphology = Literal[
    "humanoid",
    "mobile_manipulator",
    "amr",
    "agv",
    "autonomous_scrubber",
    "cleaning_robot",
    "cobot_arm",
    "quadruped",
    "drone",
    "construction_robot",
    "service_robot",
    "autonomous_forklift",
    "agricultural_robot",
    "mining_robot",
    "marine_robot",
    "aviation_robot",
    "aerospace_robot",
    "healthcare",
    "generic",
]

CoverageLevel = Literal["high", "medium", "low"]
SourceQualityLevel = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class ChecklistSlot:
    """One research question for a morphology family."""

    id: str
    label: str
    predicates: tuple[str, ...]  # any known fact with these predicates fills the slot


# Morphology → minimal descriptive fact set (research checklist only)
_CHECKLISTS: dict[Morphology, tuple[ChecklistSlot, ...]] = {
    "humanoid": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("payload", "Payload / carry capacity", ("carrying_capacity",)),
        ChecklistSlot("runtime", "Runtime / power", ("battery_runtime",)),
        ChecklistSlot("environment", "Operating environment", ("warehouse_or_factory_deployment",)),
        ChecklistSlot("workflows", "Demonstrated workflows", ("supports_tote_handling", "claims_load_unload", "claims_warehouse_transport")),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("end_effector", "End effector / hands", ("end_effector", "has_dexterous_hands")),
        ChecklistSlot("reach", "Reach / work envelope", ("reach_or_workspace",)),
    ),
    "mobile_manipulator": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("arm_count", "Arm count", ("arm_count",)),
        ChecklistSlot("payload", "Payload / carry capacity", ("carrying_capacity",)),
        ChecklistSlot("reach", "Reach / work envelope", ("reach_or_workspace",)),
        ChecklistSlot("end_effector", "End effector / hands", ("end_effector", "has_dexterous_hands")),
        ChecklistSlot("runtime", "Runtime / power", ("battery_runtime",)),
        ChecklistSlot("environment", "Operating environment", ("warehouse_or_factory_deployment", "operating_environment")),
        ChecklistSlot("autonomy", "Autonomy / control", ("autonomy_or_control", "autonomous_navigation")),
        ChecklistSlot("workflows", "Demonstrated workflows", ("supports_tote_handling", "claims_load_unload", "claims_warehouse_transport")),
    ),
    "amr": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("payload", "Payload / carry capacity", ("carrying_capacity",)),
        ChecklistSlot("runtime", "Runtime / power", ("battery_runtime",)),
        ChecklistSlot("environment", "Operating environment", ("warehouse_or_factory_deployment", "operating_environment")),
        ChecklistSlot("autonomy", "Autonomy / control", ("autonomy_or_control", "autonomous_navigation")),
        ChecklistSlot("workflows", "Demonstrated workflows", ("supports_tote_handling", "claims_warehouse_transport", "claims_load_unload")),
    ),
    "agv": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("payload", "Payload / carry capacity", ("carrying_capacity",)),
        ChecklistSlot("runtime", "Runtime / power", ("battery_runtime",)),
        ChecklistSlot("environment", "Operating environment", ("warehouse_or_factory_deployment", "operating_environment")),
        ChecklistSlot("workflows", "Demonstrated workflows", ("claims_warehouse_transport", "claims_load_unload")),
    ),
    "autonomous_scrubber": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("scrubbing", "Hard-floor scrubbing", ("supports_hard_floor_scrubbing",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("runtime", "Runtime / power", ("battery_runtime",)),
        ChecklistSlot("environment", "Operating environment", ("operating_environment", "warehouse_or_factory_deployment")),
        ChecklistSlot("autonomy", "Autonomy / control", ("autonomy_or_control", "autonomous_navigation")),
    ),
    "cobot_arm": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("payload", "Payload / carry capacity", ("carrying_capacity",)),
        ChecklistSlot("reach", "Reach / work envelope", ("reach_or_workspace",)),
        ChecklistSlot("dof", "Degrees of freedom", ("degrees_of_freedom", "arm_count")),
        ChecklistSlot("end_effector", "End effector / tooling", ("end_effector", "has_dexterous_hands")),
        ChecklistSlot("environment", "Operating environment", ("operating_environment", "warehouse_or_factory_deployment", "ingress_protection")),
    ),
    "quadruped": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("payload", "Payload / carry capacity", ("carrying_capacity",)),
        ChecklistSlot("runtime", "Runtime / power", ("battery_runtime",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture", "max_speed")),
        ChecklistSlot("environment", "Operating environment", ("operating_environment", "ingress_protection")),
        ChecklistSlot("autonomy", "Autonomy / control", ("autonomy_or_control", "autonomous_navigation")),
    ),
    "drone": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility / flight", ("autonomous_navigation", "mobility_architecture", "has_mobile_base")),
        ChecklistSlot("environment", "Operating environment", ("operating_environment", "ingress_protection")),
        ChecklistSlot("autonomy", "Autonomy / control", ("autonomy_or_control", "autonomous_navigation")),
        ChecklistSlot("runtime", "Runtime / power", ("battery_runtime",)),
    ),
    "cleaning_robot": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("runtime", "Runtime / power", ("battery_runtime",)),
        ChecklistSlot("environment", "Operating environment", ("operating_environment", "warehouse_or_factory_deployment")),
        ChecklistSlot("autonomy", "Autonomy / control", ("autonomy_or_control", "autonomous_navigation")),
    ),
    "construction_robot": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("environment", "Operating environment", ("operating_environment",)),
        ChecklistSlot("reach", "Reach / work envelope", ("reach_or_workspace",)),
        ChecklistSlot("payload", "Payload / carry capacity", ("carrying_capacity",)),
    ),
    "service_robot": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("payload", "Payload / carry capacity", ("carrying_capacity",)),
        ChecklistSlot("runtime", "Runtime / power", ("battery_runtime",)),
        ChecklistSlot("environment", "Operating environment", ("operating_environment",)),
    ),
    "autonomous_forklift": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("payload", "Payload / lift capacity", ("carrying_capacity",)),
        ChecklistSlot("workflows", "Demonstrated workflows", ("claims_pallet_handling", "claims_load_unload", "claims_warehouse_transport")),
        ChecklistSlot("runtime", "Runtime / power", ("battery_runtime",)),
        ChecklistSlot("environment", "Operating environment", ("warehouse_or_factory_deployment", "operating_environment")),
    ),
    "agricultural_robot": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("workflows", "Demonstrated workflows", ("claims_agriculture",)),
        ChecklistSlot("environment", "Operating environment", ("operating_environment",)),
        ChecklistSlot("runtime", "Runtime / power", ("battery_runtime",)),
        ChecklistSlot("autonomy", "Autonomy / control", ("autonomy_or_control", "autonomous_navigation")),
    ),
    "marine_robot": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("workflows", "Demonstrated workflows", ("claims_marine",)),
        ChecklistSlot("environment", "Operating environment", ("operating_environment",)),
        ChecklistSlot("autonomy", "Autonomy / control", ("autonomy_or_control", "autonomous_navigation")),
    ),
    "aviation_robot": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("workflows", "Demonstrated workflows", ("claims_avionics",)),
        ChecklistSlot("environment", "Operating environment", ("operating_environment",)),
        ChecklistSlot("autonomy", "Autonomy / control", ("autonomy_or_control", "autonomous_navigation")),
    ),
    "aerospace_robot": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("workflows", "Demonstrated workflows", ("claims_aerospace",)),
        ChecklistSlot("environment", "Operating environment", ("operating_environment",)),
        ChecklistSlot("autonomy", "Autonomy / control", ("autonomy_or_control", "autonomous_navigation")),
    ),
    "healthcare": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("workflows", "Demonstrated workflows", ("claims_healthcare", "claims_item_delivery")),
        ChecklistSlot("environment", "Operating environment", ("operating_environment",)),
        ChecklistSlot("payload", "Payload / carry capacity", ("carrying_capacity",)),
        ChecklistSlot("autonomy", "Autonomy / control", ("autonomy_or_control", "autonomous_navigation")),
    ),
    "mining_robot": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("workflows", "Demonstrated workflows", ("claims_mining",)),
        ChecklistSlot("environment", "Operating environment", ("operating_environment", "ingress_protection")),
        ChecklistSlot("payload", "Payload / haul capacity", ("carrying_capacity",)),
        ChecklistSlot("autonomy", "Autonomy / control", ("autonomy_or_control", "autonomous_navigation")),
    ),
    "generic": (
        ChecklistSlot("product_class", "Robot class / morphology", ("product_class",)),
        ChecklistSlot("payload", "Payload / carry capacity", ("carrying_capacity",)),
        ChecklistSlot("runtime", "Runtime / power", ("battery_runtime",)),
        ChecklistSlot("mobility", "Mobility architecture", ("has_mobile_base", "autonomous_navigation", "mobility_architecture")),
        ChecklistSlot("environment", "Operating environment", ("warehouse_or_factory_deployment", "operating_environment")),
        ChecklistSlot("workflows", "Demonstrated workflows", ("supports_tote_handling", "claims_load_unload", "claims_warehouse_transport", "supports_hard_floor_scrubbing")),
    ),
}


_DISPLAY_CLASS_ALIASES: dict[str, Morphology] = {
    "agriculture": "agricultural_robot",
    "agricultural_robot": "agricultural_robot",
    "farm_robot": "agricultural_robot",
    "construction": "construction_robot",
    "construction_robot": "construction_robot",
    "marine": "marine_robot",
    "marine_robot": "marine_robot",
    "avionics": "aviation_robot",
    "aviation": "aviation_robot",
    "aviation_robot": "aviation_robot",
    "drone": "drone",
    "evtol": "aviation_robot",
    "aerospace": "aerospace_robot",
    "aerospace_robot": "aerospace_robot",
    "healthcare": "healthcare",
    "healthcare_robot": "healthcare",
    "medical": "healthcare",
    "medical_robot": "healthcare",
    "clinical": "healthcare",
    "clinical_robot": "healthcare",
    "hospital": "healthcare",
    "hospital_robot": "healthcare",
}


def infer_morphology(facts: list[RobotFact], display_class: str | None = None) -> Morphology:
    mapped = _DISPLAY_CLASS_ALIASES.get((display_class or "").strip().lower())
    if mapped:
        return mapped
    if display_class in _CHECKLISTS:
        return display_class  # type: ignore[return-value]
    classes = [
        _DISPLAY_CLASS_ALIASES.get(str(f.value).lower(), str(f.value).lower())
        for f in facts
        if f.predicate == "product_class" and f.epistemic not in ("unknown",)
    ]
    for key in (
        "healthcare",
        "agricultural_robot",
        "construction_robot",
        "marine_robot",
        "aviation_robot",
        "aerospace_robot",
        "humanoid",
        "quadruped",
        "drone",
        "cobot_arm",
        "mobile_manipulator",
        "autonomous_scrubber",
        "cleaning_robot",
        "mining_robot",
        "autonomous_forklift",
        "service_robot",
        "amr",
        "agv",
    ):
        if key in classes:
            return key  # type: ignore[return-value]
    # Heuristic from other facts (still morphology, not jobs)
    preds = {f.predicate for f in facts if f.epistemic not in ("unknown",)}
    if "supports_hard_floor_scrubbing" in preds:
        return "autonomous_scrubber"
    if "arm_count" in preds or "has_dexterous_hands" in preds:
        if "has_mobile_base" in preds or "mobility_architecture" in preds:
            return "mobile_manipulator"
        return "cobot_arm"
    if "claims_warehouse_transport" in preds or "supports_tote_handling" in preds:
        return "amr"
    # IP rating + payload is common on humanoids, AMRs, and outdoor platforms.
    # It is not evidence of a quadruped.
    return "generic"


def checklist_for(morphology: Morphology) -> tuple[ChecklistSlot, ...]:
    return _CHECKLISTS.get(morphology, _CHECKLISTS["generic"])


def material_facts(facts: list[RobotFact]) -> list[RobotFact]:
    """Facts that make claims (exclude UNKNOWN placeholders)."""
    return [f for f in facts if f.epistemic != "unknown"]


def apply_research_gaps(
    facts: list[RobotFact],
    *,
    subject: str,
    display_class: str | None = None,
) -> tuple[list[RobotFact], Morphology, float, CoverageLevel]:
    """
    Emit UNKNOWN facts for empty checklist slots; CONFLICTED already on facts.

    Returns (facts_with_unknowns, morphology, coverage_rate, coverage_level).
    """
    morph = infer_morphology(facts, display_class)
    slots = checklist_for(morph)
    known_preds = {
        f.predicate
        for f in facts
        if f.epistemic not in ("unknown",) and f.value not in (None, "", "UNKNOWN")
    }
    conflicted_preds = {f.predicate for f in facts if f.epistemic == "contradicted"}

    out = list(facts)
    filled = 0
    for slot in slots:
        if any(p in known_preds for p in slot.predicates):
            filled += 1
            continue
        # Prefer showing CONFLICTED label via existing contradicted facts;
        # if somehow empty but conflicted elsewhere, still count unfilled.
        if any(p in conflicted_preds for p in slot.predicates):
            filled += 1
            continue
        out.append(
            RobotFact.create(
                subject=subject,
                predicate=slot.id,
                value="UNKNOWN",
                source_id="research_checklist",
                epistemic="unknown",
                confidence=0.0,
                evidence_span=f"No manufacturer evidence found for: {slot.label}",
            )
        )

    rate = filled / len(slots) if slots else 0.0
    if rate >= 0.7:
        level: CoverageLevel = "high"
    elif rate >= 0.4:
        level = "medium"
    else:
        level = "low"
    return out, morph, rate, level


def score_source_quality(source_types: set[str], avg_auth_confidence: float) -> tuple[float, SourceQualityLevel]:
    """
    Authoritative pack: product / specifications / documentation / solutions / case_study.
    A single manufacturer product page is already medium — not junk.
    """
    auth = {"product", "specifications", "documentation", "solutions", "case_study", "support"}
    auth_hit = source_types & auth
    weak_only = bool(source_types) and not auth_hit

    score = 0.0
    score += 0.12 * min(len(auth_hit), 4)
    if "specifications" in source_types:
        score += 0.28
    if "product" in source_types:
        score += 0.28
    if "solutions" in source_types:
        score += 0.14
    if "documentation" in source_types:
        score += 0.1
    if "case_study" in source_types:
        score += 0.1
    score += 0.12 * max(0.0, min(1.0, avg_auth_confidence))
    if weak_only:
        score = min(score, 0.25)
    if source_types <= {"homepage", "press_release", "other"}:
        score = min(score, 0.28)

    score = max(0.0, min(1.0, score))
    if score >= 0.7:
        level: SourceQualityLevel = "high"
    elif score >= 0.4:
        level = "medium"
    else:
        level = "low"
    return score, level


def derive_profile_tier(
    *,
    has_product: bool,
    grounding: float,
    coverage: float,
    source_quality: float,
) -> str:
    """
    Tier from Grounding × Coverage × Source quality — not grounding alone.
    """
    if not has_product:
        return "C"
    if grounding < 0.99:
        return "C"
    # One perfectly sourced fact must not become A/B
    if coverage < 0.35 or source_quality < 0.35:
        return "C"
    if coverage >= 0.65 and source_quality >= 0.65 and grounding >= 0.99:
        return "A"
    if coverage >= 0.4 and source_quality >= 0.45:
        return "B"
    return "C"
