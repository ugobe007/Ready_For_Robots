"""
Phase 5 (M2) — job requirement satisfaction against frozen profiles.

States: MATCHED | UNMET | UNKNOWN | LIKELY
LIKELY only when a named derivation in LIKELY_DERIVATIONS applies.

No match percentage. No robot-type → family → jobs shortcut.

Ranking (among POSSIBLE_MATCH only — the requirements gate already ran):
1. No hard blocker / required capabilities satisfied (filter, not a score)
2. Greater distinctive-capability utilization (this robot's grounded work
   primitives the job actually uses — not generic mobility)
3. Fewer critical unknowns
4. Stronger job evidence (named site / gold spec)
This is relevance ranking, not a Digit rule and not a family quota.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from app.services import robot_ontology
from app.services.robot_capability_derive import DerivedCapability, derive_capabilities

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLD_PATH = REPO_ROOT / "app" / "data" / "robot_job_requirements_gold.json"
CORPUS_PATH = REPO_ROOT / "app" / "data" / "robot_job_match_corpus.json"

MATCHED = "MATCHED"
UNMET = "UNMET"
UNKNOWN = "UNKNOWN"
LIKELY = "LIKELY"

VERDICT_POSSIBLE = "POSSIBLE_MATCH"
VERDICT_NOT = "NOT_A_MATCH"
VERDICT_INSUFFICIENT = "INSUFFICIENT"

# Generic locomotion is a gate, not a differentiator. Sourced from the machine-
# readable capability ontology (ontology/capability_ontology.v1.json) so the
# matcher is driven by the ontology; fails open to the canonical baked-in sets.
GENERIC_CAPABILITIES = robot_ontology.generic_capabilities()
DISTINCTIVE_CAPABILITIES = robot_ontology.distinctive_capabilities()
# Requirement id → robot primitives exercised when MATCHED or LIKELY.
REQUIREMENT_EXERCISES = {
    "manipulate_physical_case": frozenset({"manipulate"}),
    "manipulate_part": frozenset({"manipulate"}),
    "acquire_case_from_conveyor": frozenset({"manipulate", "load_unload"}),
    "place_case_into_pallet": frozenset({"manipulate", "load_unload"}),
    "relocate_totes_or_carts": frozenset({"tote_transport", "transport"}),
    "serve_food_drink": frozenset({"transport"}),
    "deliver_items": frozenset({"transport"}),
    "prepare_food": frozenset({"food_prep"}),
    "prepare_beverage": frozenset({"beverage_prep"}),
    "clean_surfaces": frozenset({"surface_clean"}),
    "scan_shelves": frozenset({"shelf_scan"}),
    "move_pallets": frozenset({"pallet_move"}),
    "unload_trailer": frozenset({"trailer_unload"}),
    "pick_and_pack": frozenset({"pick_pack"}),
    "sort_parcels": frozenset({"sortation"}),
    "disinfect_surfaces": frozenset({"disinfect"}),
    "goods_to_person": frozenset({"goods_to_person"}),
    "agriculture_task": frozenset({"agriculture_task"}),
    "construction_task": frozenset({"construction_task"}),
    "mining_task": frozenset({"mining_task"}),
    "hard_floor_scrub": frozenset({"hard_floor_scrub"}),
    "inspect_route_mobility": frozenset({"inspect_route"}),
    "reach_envelope": frozenset({"reach"}),
    "mobility": frozenset({"mobile"}),
    "indoor_navigation": frozenset({"mobile"}),
}
# Manipulation work also uses the robot's dual-arm / reach / load-unload stack
# when those primitives are grounded. Tote-only work does not.
MANIPULATION_STACK = frozenset({"dual_arm", "reach", "load_unload"})

# Requirements satisfied simply by one grounded distinctive capability being
# present (rid -> (capability_key, unmet_reason)). Each is a distinct capability,
# so a robot only matches the family when it genuinely has that capability.
_SIMPLE_CAP_REQ = {
    "move_pallets": ("pallet_move", "no grounded pallet-handling capability"),
    "unload_trailer": ("trailer_unload", "no grounded trailer/container-unloading capability"),
    "pick_and_pack": ("pick_pack", "no grounded piece-picking / pack capability"),
    "sort_parcels": ("sortation", "no grounded sortation capability"),
    "disinfect_surfaces": ("disinfect", "no grounded disinfection capability"),
    "goods_to_person": ("goods_to_person", "no grounded ASRS goods-to-person capability"),
    "agriculture_task": ("agriculture_task", "no grounded agricultural capability"),
    "construction_task": ("construction_task", "no grounded construction capability"),
    "mining_task": ("mining_task", "no grounded mining capability"),
}

LIKELY_DERIVATIONS = {
    "fixed_cell_ok": "Job likely accepts a fixed cell; mobility is not required for this work.",
    "amr_indoor_nav": "AMR product class implies autonomous indoor mobility.",
    "scrubber_indoor_nav": "Autonomous scrubber class implies indoor cleaning-route mobility.",
    "humanoid_indoor_nav": "Humanoid with autonomous_navigation or warehouse deployment implies indoor mobility.",
    "mobile_manip_tote_carry": "Mobile manipulator can relocate objects; AMR tote interface is not grounded.",
    "inspect_from_quadruped": "Quadruped product class is the grounded inspection-route primitive in frozen profiles.",
    "reach_documented": "Robot working reach is documented; job cell geometry is not measured.",
}


@dataclass
class RequirementResult:
    id: str
    label: str
    necessity: str
    state: str
    reason: str
    derivation: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "necessity": self.necessity,
            "state": self.state,
            "reason": self.reason,
            "derivation": self.derivation,
        }


@dataclass
class JobMatchCard:
    job_key: str
    title: str
    company_name: Optional[str]
    locality: Optional[str]
    industry: str
    path: str
    tape_family: str
    verdict: str
    robot_name: str
    why: list[str] = field(default_factory=list)
    still_unknown: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    requirements: list[RequirementResult] = field(default_factory=list)
    source: str = "requirement_match"

    def to_api_job(self) -> dict[str, Any]:
        return {
            "job_key": self.job_key,
            "title": self.title,
            "industry": self.industry,
            "path": self.path,
            "company_name": self.company_name,
            "locality": self.locality,
            "tape_family": self.tape_family,
            "verdict": self.verdict,
            "why": list(self.why),
            "still_unknown": list(self.still_unknown),
            "blockers": list(self.blockers),
            "unknowns": list(self.still_unknown),
            "requirements": [r.to_dict() for r in self.requirements],
            "source": self.source,
        }


@lru_cache(maxsize=1)
def load_gold_jobs() -> dict[str, dict[str, Any]]:
    data = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    return {j["job_key"]: j for j in data.get("jobs") or []}


@lru_cache(maxsize=1)
def load_corpus() -> tuple[dict[str, Any], ...]:
    data = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    return tuple(data.get("jobs") or [])


def _cap(caps: dict[str, DerivedCapability], key: str) -> DerivedCapability:
    return caps.get(key) or DerivedCapability(key, key, False, "explicit")


def _classes(caps: dict[str, DerivedCapability]) -> set[str]:
    raw = _cap(caps, "classes").value or []
    return {str(x).lower() for x in raw}


def _eval_requirement(
    req: dict[str, Any],
    caps: dict[str, DerivedCapability],
) -> RequirementResult:
    rid = req["id"]
    label = req["label"]
    necessity = req.get("necessity") or "required"
    job_unknown = req.get("job_value") is None and req.get("unknown_reason")
    classes = _classes(caps)
    manip = _cap(caps, "manipulate")
    mobile = _cap(caps, "mobile")
    tote = _cap(caps, "tote_transport")
    transport = _cap(caps, "transport")
    food_prep = _cap(caps, "food_prep")
    beverage_prep = _cap(caps, "beverage_prep")
    surface_clean = _cap(caps, "surface_clean")
    shelf_scan = _cap(caps, "shelf_scan")
    scrub = _cap(caps, "hard_floor_scrub")
    inspect = _cap(caps, "inspect_route")
    reach = _cap(caps, "reach")

    # Distinct single-capability requirements (Tier 1–3 work families).
    simple = _SIMPLE_CAP_REQ.get(rid)
    if simple:
        cap = _cap(caps, simple[0])
        if cap.present:
            return RequirementResult(rid, label, necessity, MATCHED, cap.evidence or cap.label)
        return RequirementResult(rid, label, necessity, UNMET, simple[1])

    if rid == "manipulate_physical_case":
        if manip.present:
            return RequirementResult(
                rid, label, necessity, MATCHED,
                manip.evidence or manip.label,
            )
        return RequirementResult(
            rid, label, necessity, UNMET,
            "no grounded manipulation capability supports case handling",
        )

    if rid == "acquire_case_from_conveyor":
        if not manip.present:
            return RequirementResult(
                rid, label, necessity, UNMET,
                "case acquisition requires manipulation; none is grounded",
            )
        return RequirementResult(
            rid, label, necessity, UNKNOWN,
            "conveyor pickup geometry is not established",
        )

    if rid == "place_case_into_pallet":
        if not manip.present:
            return RequirementResult(
                rid, label, necessity, UNMET,
                "pallet placement requires manipulation; none is grounded",
            )
        return RequirementResult(
            rid, label, necessity, UNKNOWN,
            "pallet pattern and placement cycle are not established",
        )

    if rid == "payload_vs_object_weight":
        reason = req.get("unknown_reason") or "object weight is not established"
        if job_unknown:
            return RequirementResult(rid, label, necessity, UNKNOWN, reason)
        return RequirementResult(rid, label, necessity, UNKNOWN, reason)

    if rid == "reach_envelope":
        if job_unknown and reach.present:
            return RequirementResult(
                rid, label, necessity, LIKELY,
                reach.label,
                derivation="reach_documented",
            )
        if job_unknown:
            return RequirementResult(
                rid, label, necessity, UNKNOWN,
                req.get("unknown_reason") or "job work envelope is not measured",
            )
        if reach.present:
            return RequirementResult(rid, label, necessity, MATCHED, reach.label)
        return RequirementResult(rid, label, necessity, UNKNOWN, "reach is not grounded")

    if rid == "compatible_grasp":
        return RequirementResult(
            rid, label, necessity, UNKNOWN,
            req.get("unknown_reason") or "gripper suitability for this object is not established",
        )

    if rid == "throughput_vs_line_rate":
        return RequirementResult(
            rid, label, necessity, UNKNOWN,
            req.get("unknown_reason") or "required cycle time is not established",
        )

    if rid == "fixed_cell_ok":
        return RequirementResult(
            rid, label, necessity, LIKELY,
            LIKELY_DERIVATIONS["fixed_cell_ok"],
            derivation="fixed_cell_ok",
        )

    if rid == "mobility":
        if necessity == "not_required":
            if mobile.present:
                return RequirementResult(
                    rid, label, necessity, MATCHED,
                    mobile.evidence or mobile.label,
                )
            return RequirementResult(
                rid, label, necessity, UNKNOWN,
                "mobility is not required for this job",
            )
        if mobile.present:
            return RequirementResult(rid, label, necessity, MATCHED, mobile.evidence or mobile.label)
        return RequirementResult(
            rid, label, necessity, UNMET,
            "job requires mobility between work areas; none is grounded",
        )

    if rid == "relocate_totes_or_carts":
        if tote.present:
            return RequirementResult(rid, label, necessity, MATCHED, tote.evidence or tote.label)
        if transport.present:
            # A delivery/transport robot carries and relocates items and carts.
            return RequirementResult(rid, label, necessity, MATCHED, transport.evidence or transport.label)
        if mobile.present and manip.present:
            return RequirementResult(
                rid, label, necessity, LIKELY,
                LIKELY_DERIVATIONS["mobile_manip_tote_carry"],
                derivation="mobile_manip_tote_carry",
            )
        return RequirementResult(
            rid, label, necessity, UNMET,
            "no grounded tote/cart transport capability",
        )

    if rid == "indoor_navigation":
        nav_ok = mobile.present
        if nav_ok and "amr" in classes:
            return RequirementResult(
                rid, label, necessity, LIKELY if "autonomous_navigation" not in (mobile.derived_from or [])
                and "has_mobile_base" not in (mobile.derived_from or [])
                else MATCHED,
                mobile.evidence or LIKELY_DERIVATIONS["amr_indoor_nav"],
                derivation="amr_indoor_nav" if "amr" in classes and mobile.derivation == "inferred" else None,
            )
        if nav_ok:
            state = MATCHED if mobile.derivation == "explicit" else LIKELY
            deriv = None
            if "autonomous_scrubber" in classes and mobile.derivation == "inferred":
                deriv = "scrubber_indoor_nav"
            elif "humanoid" in classes and mobile.derivation == "inferred":
                deriv = "humanoid_indoor_nav"
            elif "amr" in classes and mobile.derivation == "inferred":
                deriv = "amr_indoor_nav"
            return RequirementResult(
                rid, label, necessity, state,
                mobile.evidence or mobile.label,
                derivation=deriv,
            )
        return RequirementResult(
            rid, label, necessity, UNMET,
            "no grounded indoor navigation / mobility",
        )

    if rid == "serve_food_drink":
        # Running food/drinks to tables is an item-delivery (transport) task.
        if transport.present:
            return RequirementResult(rid, label, necessity, MATCHED, transport.evidence or transport.label)
        if tote.present:
            return RequirementResult(rid, label, necessity, MATCHED, tote.evidence or tote.label)
        return RequirementResult(
            rid, label, necessity, UNMET,
            "no grounded item delivery/serving capability",
        )

    if rid == "deliver_items":
        # Point-to-point delivery of clinical/resident items — the robot's own
        # autonomous item-transport capability (not warehouse tote handling).
        if transport.present:
            return RequirementResult(rid, label, necessity, MATCHED, transport.evidence or transport.label)
        return RequirementResult(
            rid, label, necessity, UNMET,
            "no grounded autonomous item-delivery capability",
        )

    if rid == "prepare_food":
        if food_prep.present:
            return RequirementResult(rid, label, necessity, MATCHED, food_prep.evidence or food_prep.label)
        return RequirementResult(
            rid, label, necessity, UNMET,
            "no grounded food-preparation capability",
        )

    if rid == "prepare_beverage":
        if beverage_prep.present:
            return RequirementResult(rid, label, necessity, MATCHED, beverage_prep.evidence or beverage_prep.label)
        return RequirementResult(
            rid, label, necessity, UNMET,
            "no grounded beverage-preparation capability",
        )

    if rid == "clean_surfaces":
        if surface_clean.present:
            return RequirementResult(rid, label, necessity, MATCHED, surface_clean.evidence or surface_clean.label)
        return RequirementResult(
            rid, label, necessity, UNMET,
            "no grounded restroom/surface-cleaning capability",
        )

    if rid == "scan_shelves":
        if shelf_scan.present:
            return RequirementResult(rid, label, necessity, MATCHED, shelf_scan.evidence or shelf_scan.label)
        return RequirementResult(
            rid, label, necessity, UNMET,
            "no grounded shelf/inventory-scanning capability",
        )

    if rid == "hard_floor_scrub":
        if scrub.present:
            return RequirementResult(rid, label, necessity, MATCHED, scrub.evidence or scrub.label)
        return RequirementResult(
            rid, label, necessity, UNMET,
            "hard-floor scrubbing is not grounded on this profile",
        )

    if rid == "inspect_route_mobility":
        if inspect.present:
            return RequirementResult(
                rid, label, necessity, LIKELY if inspect.derivation == "inferred" else MATCHED,
                inspect.evidence or inspect.label,
                derivation="inspect_from_quadruped" if inspect.derivation == "inferred" else None,
            )
        return RequirementResult(
            rid, label, necessity, UNMET,
            "no grounded inspection-route capability",
        )

    if rid == "manipulate_part":
        if manip.present:
            return RequirementResult(rid, label, necessity, MATCHED, manip.evidence or manip.label)
        return RequirementResult(
            rid, label, necessity, UNMET,
            "no grounded manipulation capability supports part handling",
        )

    return RequirementResult(rid, label, necessity, UNKNOWN, "no evaluator for this requirement")


def _verdict(results: list[RequirementResult]) -> str:
    required = [r for r in results if r.necessity == "required"]
    if any(r.state == UNMET for r in required):
        return VERDICT_NOT
    if any(r.state == MATCHED for r in required):
        return VERDICT_POSSIBLE
    if any(r.state == LIKELY for r in required):
        return VERDICT_POSSIBLE
    return VERDICT_INSUFFICIENT


def _why_lines(
    results: list[RequirementResult],
    caps: dict[str, DerivedCapability],
    verdict: str,
) -> list[str]:
    """Grounded capabilities that satisfy this job — not a family affinity list."""
    if verdict != VERDICT_POSSIBLE:
        return []
    needed = {r.id for r in results if r.necessity in {"required", "likely_ok"} and r.state in {MATCHED, LIKELY}}
    lines: list[str] = []

    def add(text: str) -> None:
        if text and text not in lines:
            lines.append(text)

    if needed & {"manipulate_physical_case", "manipulate_part", "acquire_case_from_conveyor", "place_case_into_pallet"}:
        dual = _cap(caps, "dual_arm")
        manip = _cap(caps, "manipulate")
        add(dual.label if dual.present else manip.label)
        if _cap(caps, "mobile").present:
            add(_cap(caps, "mobile").label)
    if needed & {"relocate_totes_or_carts"}:
        tote = _cap(caps, "tote_transport")
        transport = _cap(caps, "transport")
        if tote.present:
            add(tote.label)
        elif transport.present:
            add(transport.label)
        else:
            add("can relocate objects")
    if needed & {"serve_food_drink", "deliver_items"}:
        t = _cap(caps, "transport")
        add(t.label if t.present else _cap(caps, "tote_transport").label)
        if _cap(caps, "mobile").present:
            add(_cap(caps, "mobile").label)
    if needed & {"prepare_food"}:
        add(_cap(caps, "food_prep").label)
    if needed & {"prepare_beverage"}:
        add(_cap(caps, "beverage_prep").label)
    if needed & {"clean_surfaces"}:
        add(_cap(caps, "surface_clean").label)
    if needed & {"scan_shelves"}:
        add(_cap(caps, "shelf_scan").label)
        if _cap(caps, "mobile").present:
            add(_cap(caps, "mobile").label)
    for _rid, _capkey in (
        ("move_pallets", "pallet_move"), ("unload_trailer", "trailer_unload"),
        ("pick_and_pack", "pick_pack"), ("sort_parcels", "sortation"),
        ("disinfect_surfaces", "disinfect"), ("goods_to_person", "goods_to_person"),
        ("agriculture_task", "agriculture_task"), ("construction_task", "construction_task"),
        ("mining_task", "mining_task"),
    ):
        if _rid in needed:
            add(_cap(caps, _capkey).label)
    if needed & {"hard_floor_scrub"}:
        add(_cap(caps, "hard_floor_scrub").label)
    if needed & {"inspect_route_mobility"}:
        add(_cap(caps, "inspect_route").label)
    if needed & {"mobility", "indoor_navigation"} and _cap(caps, "mobile").present:
        add(_cap(caps, "mobile").label)
    if needed & {"reach_envelope"} and _cap(caps, "reach").present:
        add(_cap(caps, "reach").label)
    return lines


def _unknown_lines(results: list[RequirementResult]) -> list[str]:
    out = []
    seen = set()
    for r in results:
        if r.necessity != "required":
            continue
        if r.state != UNKNOWN:
            continue
        text = r.reason or r.label
        key = text.lower().rstrip(".")
        if any(key in s or s in key for s in seen):
            continue
        seen.add(key)
        out.append(text)
    return out


def _blocker_lines(results: list[RequirementResult], job: dict[str, Any]) -> list[str]:
    unmet = [r for r in results if r.necessity == "required" and r.state == UNMET]
    if not unmet:
        return []
    physics = job.get("physics") or ""
    if physics == "case_palletize" or any(r.id.startswith("acquire_case") or r.id.startswith("place_case") or r.id == "manipulate_physical_case" for r in unmet):
        if any(r.id in {"manipulate_physical_case", "acquire_case_from_conveyor", "place_case_into_pallet"} for r in unmet):
            return [
                "job requires autonomous case acquisition and pallet placement",
                "no grounded manipulation capability supports that requirement",
            ]
    return [r.reason or r.label for r in unmet]


def evaluate_job(
    profile: dict[str, Any],
    job_spec: dict[str, Any],
    *,
    corpus_row: dict[str, Any] | None = None,
) -> JobMatchCard:
    caps = derive_capabilities(profile)
    product = (profile.get("selected_product") or {}).get("name") or "your robot"
    results = [_eval_requirement(req, caps) for req in job_spec.get("requirements") or []]
    verdict = _verdict(results)
    row = corpus_row or {}
    return JobMatchCard(
        job_key=job_spec.get("job_key") or row.get("job_key") or "",
        title=job_spec.get("title") or row.get("title") or "",
        company_name=job_spec.get("company_name") if job_spec.get("company_name") is not None else row.get("company_name"),
        locality=job_spec.get("locality") if job_spec.get("locality") is not None else row.get("locality"),
        industry=row.get("industry") or job_spec.get("locality") or job_spec.get("physics") or "",
        path=row.get("path") or "",
        tape_family=row.get("tape_family") or job_spec.get("physics") or "transport",
        verdict=verdict,
        robot_name=product,
        why=_why_lines(results, caps, verdict),
        still_unknown=_unknown_lines(results) if verdict != VERDICT_NOT else [],
        blockers=_blocker_lines(results, job_spec),
        requirements=results,
        source="requirement_match",
    )


# Work-physics templates for the rest of the corpus (not robot families).
_PALLETIZE_REQS = [
    {"id": "manipulate_physical_case", "label": "manipulate physical case", "necessity": "required"},
    {"id": "acquire_case_from_conveyor", "label": "acquire case from conveyor", "necessity": "required"},
    {"id": "place_case_into_pallet", "label": "place case into pallet pattern", "necessity": "required"},
    {"id": "payload_vs_object_weight", "label": "payload ≥ case weight", "necessity": "required", "job_value": None, "unknown_reason": "case weight"},
    {"id": "compatible_grasp", "label": "compatible grasp/end effector", "necessity": "required", "job_value": None, "unknown_reason": "gripper suitability"},
    {"id": "throughput_vs_line_rate", "label": "throughput ≥ line rate", "necessity": "required", "job_value": None, "unknown_reason": "required cycle time"},
    {"id": "fixed_cell_ok", "label": "fixed-cell operation acceptable", "necessity": "likely_ok"},
    {"id": "mobility", "label": "mobility", "necessity": "not_required"},
]
_GRIPPER_REQS = [
    {"id": "manipulate_part", "label": "manipulate physical part", "necessity": "required"},
    {"id": "payload_vs_object_weight", "label": "payload ≥ part weight", "necessity": "required", "job_value": None, "unknown_reason": "part weight"},
    {"id": "compatible_grasp", "label": "compatible grasp/end effector", "necessity": "required", "job_value": None, "unknown_reason": "gripper suitability"},
    {"id": "fixed_cell_ok", "label": "fixed-cell operation acceptable", "necessity": "likely_ok"},
    {"id": "mobility", "label": "mobility", "necessity": "not_required"},
    {"id": "hard_floor_scrub", "label": "hard-floor scrubbing", "necessity": "not_required"},
]
_TOTE_REQS = [
    {"id": "relocate_totes_or_carts", "label": "relocate totes or carts between areas", "necessity": "required"},
    {"id": "indoor_navigation", "label": "indoor warehouse navigation", "necessity": "required"},
    {"id": "mobility", "label": "mobility between work areas", "necessity": "required"},
    {"id": "payload_vs_object_weight", "label": "payload ≥ tote/cart weight", "necessity": "required", "job_value": None, "unknown_reason": "tote and cart weight"},
    {"id": "manipulate_physical_case", "label": "manipulate physical case", "necessity": "not_required"},
    {"id": "hard_floor_scrub", "label": "hard-floor scrubbing", "necessity": "not_required"},
]
_SCRUB_REQS = [
    {"id": "hard_floor_scrub", "label": "autonomous hard-floor scrubbing", "necessity": "required"},
    {"id": "indoor_navigation", "label": "indoor cleaning-route navigation", "necessity": "required"},
    {"id": "mobility", "label": "mobility along cleaning routes", "necessity": "required"},
    {"id": "manipulate_physical_case", "label": "manipulate physical case", "necessity": "not_required"},
    {"id": "relocate_totes_or_carts", "label": "relocate totes or carts", "necessity": "not_required"},
]
_INSPECT_REQS = [
    {"id": "inspect_route_mobility", "label": "mobile inspection route", "necessity": "required"},
    {"id": "indoor_navigation", "label": "traverse facility routes", "necessity": "required"},
    {"id": "manipulate_physical_case", "label": "manipulate physical case", "necessity": "not_required"},
    {"id": "relocate_totes_or_carts", "label": "relocate totes or carts", "necessity": "not_required"},
    {"id": "hard_floor_scrub", "label": "hard-floor scrubbing", "necessity": "not_required"},
]
# Hospitality work — a cross-cutting domain (serving, food prep, beverages,
# restroom cleaning) that overlaps transport, manipulation and cleaning.
_SERVE_REQS = [
    {"id": "serve_food_drink", "label": "run food/drinks to tables", "necessity": "required"},
    {"id": "indoor_navigation", "label": "navigate the dining floor", "necessity": "required"},
    {"id": "mobility", "label": "mobility between tables", "necessity": "required"},
    {"id": "payload_vs_object_weight", "label": "payload \u2265 tray/load weight", "necessity": "required", "job_value": None, "unknown_reason": "tray/load weight"},
    {"id": "manipulate_physical_case", "label": "manipulate physical case", "necessity": "not_required"},
]
_FOOD_PREP_REQS = [
    {"id": "prepare_food", "label": "prepare/cook food at station", "necessity": "required"},
    {"id": "throughput_vs_line_rate", "label": "throughput \u2265 station rate", "necessity": "required", "job_value": None, "unknown_reason": "required station rate"},
    {"id": "fixed_cell_ok", "label": "fixed station acceptable", "necessity": "likely_ok"},
    {"id": "mobility", "label": "mobility", "necessity": "not_required"},
]
_BEVERAGE_REQS = [
    {"id": "prepare_beverage", "label": "prepare/serve drinks", "necessity": "required"},
    {"id": "throughput_vs_line_rate", "label": "throughput \u2265 order rate", "necessity": "required", "job_value": None, "unknown_reason": "required order rate"},
    {"id": "fixed_cell_ok", "label": "fixed bar/station acceptable", "necessity": "likely_ok"},
    {"id": "mobility", "label": "mobility", "necessity": "not_required"},
]
_RESTROOM_REQS = [
    {"id": "clean_surfaces", "label": "clean restroom fixtures and floors", "necessity": "required"},
    {"id": "indoor_navigation", "label": "navigate facility to restrooms", "necessity": "required"},
    {"id": "mobility", "label": "mobility between restrooms", "necessity": "required"},
    {"id": "hard_floor_scrub", "label": "hard-floor scrubbing", "necessity": "not_required"},
]
# Tier 1 — warehouse: pallet handling, trailer unloading, piece pick/pack, sortation.
_PALLET_MOVE_REQS = [
    {"id": "move_pallets", "label": "move / handle pallets", "necessity": "required"},
    {"id": "indoor_navigation", "label": "navigate the warehouse", "necessity": "required"},
    {"id": "mobility", "label": "mobility between dock and storage", "necessity": "required"},
    {"id": "payload_vs_object_weight", "label": "payload \u2265 pallet weight", "necessity": "required", "job_value": None, "unknown_reason": "pallet weight"},
]
_TRAILER_UNLOAD_REQS = [
    {"id": "unload_trailer", "label": "unload cases from trailers/containers", "necessity": "required"},
    {"id": "payload_vs_object_weight", "label": "payload \u2265 case weight", "necessity": "required", "job_value": None, "unknown_reason": "case weight"},
    {"id": "throughput_vs_line_rate", "label": "throughput \u2265 unload rate", "necessity": "required", "job_value": None, "unknown_reason": "unload rate"},
    {"id": "fixed_cell_ok", "label": "dock-fixed or mobile acceptable", "necessity": "likely_ok"},
]
_PICK_PACK_REQS = [
    {"id": "pick_and_pack", "label": "piece/each picking and packing", "necessity": "required"},
    {"id": "throughput_vs_line_rate", "label": "throughput \u2265 pick rate", "necessity": "required", "job_value": None, "unknown_reason": "pick rate"},
    {"id": "compatible_grasp", "label": "compatible grasp/end effector", "necessity": "required", "job_value": None, "unknown_reason": "gripper suitability"},
    {"id": "fixed_cell_ok", "label": "fixed pick cell acceptable", "necessity": "likely_ok"},
]
_SORTATION_REQS = [
    {"id": "sort_parcels", "label": "sort parcels/packages to destinations", "necessity": "required"},
    {"id": "throughput_vs_line_rate", "label": "throughput \u2265 sort rate", "necessity": "required", "job_value": None, "unknown_reason": "sort rate"},
    {"id": "fixed_cell_ok", "label": "fixed sortation cell acceptable", "necessity": "likely_ok"},
]
# Tier 2 — disinfection + ASRS goods-to-person.
_DISINFECT_REQS = [
    {"id": "disinfect_surfaces", "label": "disinfect rooms / surfaces", "necessity": "required"},
    {"id": "indoor_navigation", "label": "navigate the facility", "necessity": "required"},
    {"id": "mobility", "label": "mobility between rooms", "necessity": "required"},
]
_ASRS_REQS = [
    {"id": "goods_to_person", "label": "store and retrieve goods to a picker", "necessity": "required"},
    {"id": "throughput_vs_line_rate", "label": "throughput \u2265 order rate", "necessity": "required", "job_value": None, "unknown_reason": "order rate"},
]
# Tier 3 — construction / mining / agriculture (recognized verticals, now matchable).
_AGRICULTURE_REQS = [
    {"id": "agriculture_task", "label": "field task (weed/harvest/spray/seed)", "necessity": "required"},
    {"id": "mobility", "label": "mobility across the field", "necessity": "required"},
]
_CONSTRUCTION_REQS = [
    {"id": "construction_task", "label": "jobsite task (layout/drywall/rebar/earthmoving)", "necessity": "required"},
    {"id": "mobility", "label": "mobility across the jobsite", "necessity": "required"},
]
_MINING_REQS = [
    {"id": "mining_task", "label": "mining task (haulage/drilling/loading)", "necessity": "required"},
    {"id": "mobility", "label": "mobility across the site", "necessity": "required"},
]

# Retail — autonomous shelf / inventory scanning (Simbe Tally-class).
_SHELF_SCAN_REQS = [
    {"id": "scan_shelves", "label": "scan shelves for inventory / out-of-stocks / planogram", "necessity": "required"},
    {"id": "indoor_navigation", "label": "navigate store aisles", "necessity": "required"},
    {"id": "mobility", "label": "mobility along aisles", "necessity": "required"},
]
# Healthcare — hospital clinical delivery (meds, specimens, supplies, meals, linens).
_CLINICAL_REQS = [
    {"id": "deliver_items", "label": "deliver clinical items (meds/specimens/supplies)", "necessity": "required"},
    {"id": "indoor_navigation", "label": "navigate the hospital (elevators, secure doors)", "necessity": "required"},
    {"id": "mobility", "label": "mobility between departments", "necessity": "required"},
    {"id": "payload_vs_object_weight", "label": "payload \u2265 load weight", "necessity": "required", "job_value": None, "unknown_reason": "load weight"},
]
# Eldercare — resident services (meals, linens, amenities, supplies to rooms).
_RESIDENT_REQS = [
    {"id": "deliver_items", "label": "deliver resident items (meals/linens/amenities)", "necessity": "required"},
    {"id": "indoor_navigation", "label": "navigate the community", "necessity": "required"},
    {"id": "mobility", "label": "mobility between resident rooms", "necessity": "required"},
    {"id": "payload_vs_object_weight", "label": "payload \u2265 load weight", "necessity": "required", "job_value": None, "unknown_reason": "load weight"},
]


def requirements_for_corpus_job(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Work-physics requirements. tape_family here is the job's work, not a robot family."""
    gold = load_gold_jobs().get(row.get("job_key") or "")
    if gold:
        return list(gold["requirements"])
    tape = (row.get("tape_family") or "").lower()
    actions = [str(a).lower() for a in (row.get("actions") or [])]
    if tape == "pallet" or "palletizing" in actions:
        return list(_PALLETIZE_REQS)
    if tape == "gripper":
        return list(_GRIPPER_REQS)
    if tape == "scrub":
        return list(_SCRUB_REQS)
    if tape == "inspect":
        return list(_INSPECT_REQS)
    if tape == "serve":
        return list(_SERVE_REQS)
    if tape == "food_prep":
        return list(_FOOD_PREP_REQS)
    if tape == "beverage":
        return list(_BEVERAGE_REQS)
    if tape == "shelf_scan":
        return list(_SHELF_SCAN_REQS)
    if tape == "pallet_move":
        return list(_PALLET_MOVE_REQS)
    if tape == "trailer_unload":
        return list(_TRAILER_UNLOAD_REQS)
    if tape == "pick_pack":
        return list(_PICK_PACK_REQS)
    if tape == "sortation":
        return list(_SORTATION_REQS)
    if tape == "disinfection":
        return list(_DISINFECT_REQS)
    if tape == "asrs":
        return list(_ASRS_REQS)
    if tape == "agriculture":
        return list(_AGRICULTURE_REQS)
    if tape == "construction":
        return list(_CONSTRUCTION_REQS)
    if tape == "mining":
        return list(_MINING_REQS)
    if tape == "clinical_delivery":
        return list(_CLINICAL_REQS)
    if tape == "resident_services":
        return list(_RESIDENT_REQS)
    if tape == "restroom":
        return list(_RESTROOM_REQS)
    if tape in {"transport", "cart"}:
        return list(_TOTE_REQS)
    # Unknown work physics — do not guess a family.
    return [
        {"id": "indoor_navigation", "label": "work physics not modeled", "necessity": "required"},
    ]


def match_job_spec(profile: dict[str, Any], job_key: str) -> JobMatchCard:
    gold = load_gold_jobs()[job_key]
    row = next((j for j in load_corpus() if j.get("job_key") == job_key), None)
    return evaluate_job(profile, gold, corpus_row=row)


def _present_distinctive_capabilities(caps: dict[str, DerivedCapability]) -> set[str]:
    return {
        key
        for key, cap in caps.items()
        if cap.present and key in DISTINCTIVE_CAPABILITIES
    }


def distinctive_utilization(
    caps: dict[str, DerivedCapability],
    card: JobMatchCard,
) -> int:
    """How many of this robot's distinctive grounded primitives the job uses.

    Count is internal ranking only — never a match percentage in the API.
    """
    robot_distinctive = _present_distinctive_capabilities(caps)
    exercised: set[str] = set()
    for req in card.requirements:
        if req.necessity not in {"required", "likely_ok"}:
            continue
        if req.state not in {MATCHED, LIKELY}:
            continue
        exercised |= REQUIREMENT_EXERCISES.get(req.id, frozenset())
    if "manipulate" in exercised:
        exercised |= MANIPULATION_STACK
    exercised -= GENERIC_CAPABILITIES
    return len(exercised & robot_distinctive)


def _critical_unknown_count(card: JobMatchCard) -> int:
    return sum(
        1
        for r in card.requirements
        if r.necessity == "required" and r.state == UNKNOWN
    )


def _evidence_rank(card: JobMatchCard, gold_keys: set[str]) -> tuple[int, int]:
    gold = 0 if card.job_key in gold_keys else 1
    named = 0 if (card.company_name and card.locality) else 1
    return gold, named


def match_jobs_from_profile(
    profile: dict[str, Any],
    *,
    limit: int = 12,
    include_rejections: bool = False,
) -> dict[str, Any]:
    product = (profile.get("selected_product") or {}).get("name")
    company = (profile.get("company") or {}).get("name")
    robot_name = product or company or "your robot"
    if not (profile.get("facts") or []):
        return {
            "state": "could_not_understand",
            "robot_name": robot_name,
            "capabilities": [],
            "families": [],
            "jobs": [],
            "job_count": 0,
            "matcher": "requirement_v1",
        }

    caps = derive_capabilities(profile)
    cards: list[JobMatchCard] = []
    gold = load_gold_jobs()
    for row in load_corpus():
        spec = gold.get(row.get("job_key") or "")
        if spec is None:
            spec = {
                "job_key": row.get("job_key"),
                "title": row.get("title"),
                "company_name": row.get("company_name"),
                "locality": row.get("locality"),
                "physics": row.get("tape_family"),
                "requirements": requirements_for_corpus_job(row),
            }
        cards.append(evaluate_job(profile, spec, corpus_row=row))

    possible = [c for c in cards if c.verdict == VERDICT_POSSIBLE]
    gold_keys = set(load_gold_jobs())

    def rank_key(c: JobMatchCard) -> tuple:
        return (
            -distinctive_utilization(caps, c),
            _critical_unknown_count(c),
            *_evidence_rank(c, gold_keys),
            c.job_key,
        )

    possible.sort(key=rank_key)
    top = possible[:limit]
    jobs_out = [c.to_api_job() for c in top]
    if include_rejections:
        jobs_out.extend(c.to_api_job() for c in cards if c.verdict == VERDICT_NOT)

    cap_out = []
    for key in ("dual_arm", "manipulate", "mobile", "reach", "tote_transport", "transport",
                "food_prep", "beverage_prep", "surface_clean", "shelf_scan", "pallet_move",
                "trailer_unload", "pick_pack", "sortation", "disinfect", "goods_to_person",
                "agriculture_task", "construction_task", "mining_task",
                "hard_floor_scrub", "inspect_route"):
        c = caps.get(key)
        if c and c.present:
            cap_out.append(
                {
                    "key": c.key,
                    "label": c.label,
                    "confidence": 0.9 if c.derivation == "explicit" else 0.7,
                    "excerpt": c.evidence,
                    "truth_state": "confirmed" if c.derivation == "explicit" else "inferred",
                }
            )

    state = "matches" if top else "thin_corpus"
    return {
        "state": state,
        "robot_name": robot_name,
        "capabilities": cap_out,
        "families": [],
        "jobs": jobs_out,
        "job_count": len(possible),
        "matcher": "requirement_v1",
        "company_name": company,
        "products": [profile.get("selected_product")] if profile.get("selected_product") else [],
        "needs_product_choice": bool(profile.get("needs_product_choice")),
        "research_stages": profile.get("research_stages") or [],
        "robot_class": (profile.get("selected_product") or {}).get("display_class"),
        "source_url": profile.get("submitted_url"),
    }
