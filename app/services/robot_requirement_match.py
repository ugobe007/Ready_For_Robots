"""
Phase 5 (M2) — job requirement satisfaction against frozen profiles.

States: MATCHED | UNMET | UNKNOWN | LIKELY
LIKELY only when a named derivation in LIKELY_DERIVATIONS applies.

No match percentage. No robot-type → family → jobs shortcut.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

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
    scrub = _cap(caps, "hard_floor_scrub")
    inspect = _cap(caps, "inspect_route")
    reach = _cap(caps, "reach")

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
        add(_cap(caps, "tote_transport").label if _cap(caps, "tote_transport").present else "can relocate objects")
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
    distinctive = {
        "manipulate_physical_case",
        "manipulate_part",
        "acquire_case_from_conveyor",
        "place_case_into_pallet",
        "relocate_totes_or_carts",
        "hard_floor_scrub",
        "inspect_route_mobility",
    }

    gold_keys = set(load_gold_jobs())

    def rank_key(c: JobMatchCard) -> tuple:
        reqs = [r for r in c.requirements if r.necessity == "required"]
        dist_matched = sum(1 for r in reqs if r.id in distinctive and r.state == MATCHED)
        dist_likely = sum(1 for r in reqs if r.id in distinctive and r.state == LIKELY)
        dist_unknown = sum(1 for r in reqs if r.id in distinctive and r.state == UNKNOWN)
        gold_rank = 0 if c.job_key in gold_keys else 1
        return (-dist_matched, -dist_likely, dist_unknown, gold_rank, c.job_key)

    possible.sort(key=rank_key)
    top = possible[:limit]
    jobs_out = [c.to_api_job() for c in top]
    if include_rejections:
        jobs_out.extend(c.to_api_job() for c in cards if c.verdict == VERDICT_NOT)

    cap_out = []
    for key in ("dual_arm", "manipulate", "mobile", "reach", "tote_transport", "hard_floor_scrub", "inspect_route"):
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
