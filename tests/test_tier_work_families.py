"""Tier 1–3 work families: each requires its own distinct capability.

Verifies that a robot with a given distinct capability matches only its family,
and that the frozen canonical robots never leak into any of the new families
(they lack the new capabilities).
"""
from __future__ import annotations

import json
from pathlib import Path

from app.services.robot_capability_derive import derive_capabilities
from app.services.robot_requirement_match import match_jobs_from_profile

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "m2_profiles"

NEW_FAMILIES = {
    "shelf_scan", "pallet_move", "trailer_unload", "pick_pack", "sortation",
    "disinfection", "asrs", "agriculture", "construction", "mining",
}

# family -> the grounding claim predicate(s) for its distinct capability
FAMILY_CLAIM = {
    "pallet_move": ["claims_pallet_handling"],
    "trailer_unload": ["claims_trailer_unload"],
    "pick_pack": ["claims_piece_pick"],
    "sortation": ["claims_sortation"],
    "disinfection": ["claims_disinfection"],
    "asrs": ["claims_goods_to_person"],
    "agriculture": ["claims_agriculture"],
    "construction": ["claims_construction"],
    "mining": ["claims_mining"],
    "shelf_scan": ["claims_shelf_scan", "has_mobile_base"],
}


def _profile(*preds):
    facts = []
    for p in preds:
        val = 500 if p == "carrying_capacity" else True
        units = "kg" if p == "carrying_capacity" else None
        facts.append({"predicate": p, "value": val, "units": units, "epistemic": "explicit",
                      "confidence": 0.9, "evidence_span": p, "source_id": "s0"})
    return {"selected_product": {"name": "R"}, "company": {"name": "R"}, "facts": facts}


def _fams(profile):
    return {j["tape_family"] for j in match_jobs_from_profile(profile, limit=80)["jobs"]}


def test_each_new_capability_matches_only_its_family():
    for family, preds in FAMILY_CLAIM.items():
        prof = _profile(*preds, "carrying_capacity")
        fams = _fams(prof)
        assert family in fams, f"{family} did not match (caps={[k for k,c in derive_capabilities(prof).items() if c.present]})"
        # Must not leak into unrelated NEW families.
        assert fams & NEW_FAMILIES == {family}, f"{family} leaked into {fams & NEW_FAMILIES}"


def _fx(name):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def test_frozen_robots_do_not_leak_into_any_new_family():
    for name in ("vega", "digit", "origin", "neo", "spot"):
        fams = _fams(_fx(name))
        assert fams.isdisjoint(NEW_FAMILIES), (name, fams & NEW_FAMILIES)
