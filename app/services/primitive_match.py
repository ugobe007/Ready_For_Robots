"""
Primitive-spine matching: WORK.required ∩ ROBOT.supported.

Powers both Robot→Job and Job→Robot without free-text marketplace logic.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


def _set(codes: Iterable[str] | None) -> Set[str]:
    return {str(c) for c in (codes or []) if c}


def primitive_coverage(
    required: Sequence[str] | None,
    supported: Sequence[str] | None,
) -> Dict[str, Any]:
    req = _set(required)
    sup = _set(supported)
    if not req:
        return {
            "coverage": None,
            "matched": [],
            "missing": [],
            "extra": sorted(sup),
            "score_status": "insufficient_evidence",
            "work_match": 0.0,
        }
    matched = sorted(req & sup)
    missing = sorted(req - sup)
    coverage = len(matched) / len(req)
    # Soft credit for supporting related transport when point_to_point missing but line_replenishment present? No — keep strict.
    work_match = round(100.0 * coverage, 1)
    return {
        "coverage": round(coverage, 3),
        "matched": matched,
        "missing": missing,
        "extra": sorted(sup - req),
        "score_status": "ok",
        "work_match": work_match,
    }


def hard_blockers(
    required: Sequence[str] | None,
    supported: Sequence[str] | None,
    *,
    workflow_family: Optional[str] = None,
) -> List[str]:
    """
    Machine-class mismatches that should kill or demote an opportunity.

    Example: tugger labor hired but autonomous forklift is the wrong machine.
    """
    req = _set(required)
    sup = _set(supported)
    blockers: List[str] = []
    family = (workflow_family or "").lower()

    needs_tow = "eng.tow_hitch" in req or family == "tugger_line_replenishment"
    has_tow = "eng.tow_hitch" in sup
    has_pallet_fork = "eng.acquire_pallet_floor" in sup and "man.lift_vertical" in sup
    needs_pallet_fork = (
        "eng.acquire_pallet_floor" in req
        and "man.lift_vertical" in req
        and family in {"strong_transport", "trailer_yard", ""}
    )

    if needs_tow and not has_tow and has_pallet_fork:
        blockers.append("WRONG_MACHINE_TUGGER")

    if needs_pallet_fork and not has_pallet_fork and has_tow and "eng.acquire_pallet_floor" not in sup:
        blockers.append("WRONG_MACHINE_FORKLIFT")

    # Heavy case/dexterity work vs forklift-only
    if family == "mixed_material_handler" and "man.case_pick" in req:
        if "man.case_pick" not in sup and has_pallet_fork and not has_tow:
            blockers.append("PARTIAL_ONLY_MANIPULATION")

    return blockers


def work_robot_match_score(
    *,
    required_primitives: Sequence[str] | None,
    supported_primitives: Sequence[str] | None,
    workflow_family: Optional[str] = None,
    industry_aligned: bool = False,
    buyer_tier: str = "",
    buyer_score: float = 0.0,
) -> Tuple[float, Dict[str, Any]]:
    """
    Composite 0–100 match used by market graph.

    Work Match (primitive coverage) dominates; industry/tier are secondary.
    Hard blockers cap the score.
    """
    cov = primitive_coverage(required_primitives, supported_primitives)
    blockers = hard_blockers(
        required_primitives, supported_primitives, workflow_family=workflow_family
    )
    if cov["score_status"] == "insufficient_evidence":
        # Fall back to weak industry/tier signal only
        base = min(1.0, max(0.0, float(buyer_score) / 100.0))
        tier = 1.0 if (buyer_tier or "").upper() == "HOT" else 0.55 if (buyer_tier or "").upper() == "WARM" else 0.25
        score = round(min(100.0, (base * 40.0) + (tier * 15.0) + (25.0 if industry_aligned else 0.0)), 1)
        return score, {
            **cov,
            "hard_blockers": blockers,
            "match_mode": "industry_fallback",
            "work_match": None,
        }

    work = float(cov["work_match"] or 0.0)
    tier_boost = 8.0 if (buyer_tier or "").upper() == "HOT" else 4.0 if (buyer_tier or "").upper() == "WARM" else 0.0
    industry_boost = 10.0 if industry_aligned else 0.0
    score = round(min(100.0, work * 0.82 + industry_boost + tier_boost), 1)

    if "WRONG_MACHINE_TUGGER" in blockers or "WRONG_MACHINE_FORKLIFT" in blockers:
        score = min(score, 28.0)
        cov = {**cov, "work_match_label": "poor"}
    elif "PARTIAL_ONLY_MANIPULATION" in blockers:
        score = min(score, 55.0)
        cov = {**cov, "work_match_label": "partial"}
    else:
        wm = cov["work_match"] or 0
        label = (
            "excellent"
            if wm >= 85
            else "good"
            if wm >= 70
            else "fair"
            if wm >= 50
            else "poor"
        )
        cov = {**cov, "work_match_label": label}

    return score, {
        **cov,
        "hard_blockers": blockers,
        "match_mode": "primitive_spine",
    }
