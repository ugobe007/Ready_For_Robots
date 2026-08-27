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
    "marine", "avionics", "aerospace",
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
    "marine": ["claims_marine"],
    "avionics": ["claims_avionics"],
    "aerospace": ["claims_aerospace"],
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


def _extract(text: str) -> set[str]:
    from app.services.robot_understanding_v1 import facts as F
    from app.services.robot_understanding_v1.models import RobotSource
    src = RobotSource(id="s", url="https://x.ai/robot", source_type="product",
                      fetched_at="t", title="R", confidence=0.85)
    facts = F._extract_from_page(src, text, subject="", page_url="https://x.ai/robot", page_title="R")
    return {f.predicate for f in facts if f.epistemic != "unknown"}


def test_sortation_requires_robot_or_parcel_context():
    # Bare "sortation" as a warehouse function (Locus) must not ground it.
    assert "claims_sortation" not in _extract(
        "Our AMR supports goods-to-person picking, replenishment, and sortation workflows in the warehouse."
    )
    # A real sortation robot does ground it.
    assert "claims_sortation" in _extract("This robotic sortation system sorts parcels to destination chutes.")


def test_disinfection_requires_uv_or_clinical_room():
    # "surface disinfection" as a floor-scrubber cleaning benefit (Avidbots) must not ground it.
    assert "claims_disinfection" not in _extract(
        "The autonomous floor scrubber cleans and provides surface disinfection across hard floors."
    )
    # A UV disinfection robot does ground it.
    assert "claims_disinfection" in _extract("This UV-C disinfection robot disinfects patient rooms between occupancies.")


def _product_class_and_morph(text: str):
    from app.services.robot_understanding_v1 import facts as F
    from app.services.robot_understanding_v1.models import RobotSource
    from app.services.robot_understanding_v1.coverage import infer_morphology
    src = RobotSource(id="s", url="https://x.ai/robot", source_type="product",
                      fetched_at="t", title="R", confidence=0.85)
    fs = F._extract_from_page(src, text, subject="", page_url="https://x.ai/robot", page_title="R")
    known = [f for f in fs if f.epistemic != "unknown"]
    pcs = {str(f.value) for f in known if f.predicate == "product_class"}
    return pcs, infer_morphology(known)


def test_new_product_classes_and_morphology():
    for text, cls in (
        ("The LaserWeeder is an autonomous agricultural robot that weeds crops in fields.", "agricultural_robot"),
        ("Our autonomous haul truck operates as a mining robot in underground mining sites.", "mining_robot"),
        ("This autonomous forklift moves pallets across the warehouse.", "autonomous_forklift"),
    ):
        pcs, morph = _product_class_and_morph(text)
        assert cls in pcs, (cls, pcs)
        assert morph == cls, (cls, morph)


def test_ip_and_payload_are_not_quadruped():
    from app.services.robot_understanding_v1.coverage import infer_morphology
    from app.services.robot_understanding_v1.models import RobotFact

    facts = [
        RobotFact.create(
            "Neo", "carrying_capacity", 18, source_id="s0", units="lb",
            evidence_span="Payload 18 lb",
        ),
        RobotFact.create(
            "Neo", "ingress_protection", "IP68", source_id="s0",
            evidence_span="IP68",
        ),
    ]
    assert infer_morphology(facts) == "generic"


def test_humanoid_product_class_derives_manipulate():
    from app.services.robot_capability_derive import derive_capabilities

    profile = {
        "selected_product": {"name": "Neo"},
        "company": {"name": "1X"},
        "facts": [
            {
                "predicate": "product_class",
                "value": "humanoid",
                "epistemic": "explicit",
                "confidence": 0.9,
                "evidence_span": "fully electronic humanoid robot",
                "source_id": "s0",
            }
        ],
    }
    caps = derive_capabilities(profile)
    assert caps["manipulate"].present is True
