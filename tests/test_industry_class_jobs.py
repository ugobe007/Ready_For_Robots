"""FIND tiles for mining / warehouse / logistics / factory / hospitality.

Full CI (requirements.txt). Do not list this file in pstack-release /
agent-verify pytest — those jobs install pytest only and facts.py
imports requests via fetch.py.
"""
from __future__ import annotations

from app.services.robot_capability_derive import derive_capabilities
from app.services.robot_class_qualify import (
    FIND_TILE_CLASSES,
    apply_asserted_class,
    normalize_class_id,
    public_class_options,
    thin_class_profile,
)
from app.services.robot_requirement_match import match_jobs_from_profile


def _families(class_id: str) -> set[str]:
    profile = thin_class_profile("example OEM", class_id)
    out = match_jobs_from_profile(profile)
    return {j.get("tape_family") for j in out.get("jobs") or []}


def test_picker_adds_industry_tiles_not_food_prep_or_hotel():
    ids = [row["id"] for row in public_class_options()]
    assert ids[-1] == "hospitality"
    assert len(ids) == 17
    for tile in ("mining", "warehouse", "logistics", "factory", "hospitality"):
        assert tile in FIND_TILE_CLASSES
        assert tile in ids
    assert "food_prep" not in ids
    assert "serving" not in ids
    assert "hotel" not in ids
    assert "medical" not in ids
    assert normalize_class_id("hotel") == "hospitality"
    assert normalize_class_id("food_prep") == "hospitality"
    assert normalize_class_id("3pl") == "logistics"


def test_thin_mining_class_returns_named_employer_jobs():
    profile = thin_class_profile("Caterpillar", "mining")
    caps = derive_capabilities(profile)
    assert caps["mining_task"].present is True
    assert caps["manipulate"].present is False
    out = match_jobs_from_profile(profile)
    assert out["state"] == "matches"
    assert out["job_count"] > 0
    families = {j.get("tape_family") for j in out["jobs"]}
    assert families <= {"mining"}
    assert all(str(j.get("company_name") or "").strip() for j in out["jobs"])
    assert all(str(j.get("locality") or "").strip() for j in out["jobs"])


def test_thin_warehouse_class_returns_named_dc_jobs_not_cnc():
    profile = apply_asserted_class(
        {
            "company": {"name": "Locus Robotics"},
            "selected_product": {"name": "Origin"},
            "facts": [],
            "coverage_level": "low",
        },
        "warehouse",
    )
    caps = derive_capabilities(profile)
    assert caps["warehouse_task"].present is True
    out = match_jobs_from_profile(profile)
    assert out["state"] == "matches"
    assert out["job_count"] > 0
    families = {j.get("tape_family") for j in out["jobs"]}
    assert families <= {"warehouse"}
    assert "gripper" not in families
    assert "pallet" not in families
    assert all(str(j.get("company_name") or "").strip() for j in out["jobs"])


def test_thin_logistics_factory_hospitality_return_named_jobs():
    for class_id, family in (
        ("logistics", "logistics"),
        ("factory", "factory"),
        ("hospitality", "hospitality"),
    ):
        profile = thin_class_profile("example OEM", class_id)
        caps = derive_capabilities(profile)
        assert caps[f"{family}_task"].present is True
        out = match_jobs_from_profile(profile)
        assert out["state"] == "matches", class_id
        assert out["job_count"] > 0, class_id
        families = {j.get("tape_family") for j in out["jobs"]}
        assert families <= {family}, (class_id, families)
        assert "gripper" not in families
        assert "clinical_delivery" not in families
        assert all(str(j.get("company_name") or "").strip() for j in out["jobs"])


def test_hospitality_tile_is_not_humanoid_and_not_healthcare():
    profile = thin_class_profile("Relay Robotics", "hospitality")
    caps = derive_capabilities(profile)
    assert caps["hospitality_task"].present is True
    assert caps["healthcare_task"].present is False
    assert caps["manipulate"].present is False
    families = _families("hospitality")
    assert families <= {"hospitality"}
    assert "clinical_delivery" not in families


def test_hotel_alias_matches_hospitality_jobs():
    profile = thin_class_profile("Savioke", "hotel")
    out = match_jobs_from_profile(profile)
    assert out["state"] == "matches"
    assert {j.get("tape_family") for j in out["jobs"]} <= {"hospitality"}


def _extract_classes(text: str, *, subject: str, url: str, title: str):
    from app.services.robot_understanding_v1 import facts as F
    from app.services.robot_understanding_v1.coverage import infer_morphology
    from app.services.robot_understanding_v1.models import RobotSource

    src = RobotSource(
        id="s",
        url=url,
        source_type="product",
        fetched_at="t",
        title=title,
        confidence=0.85,
    )
    fs = F._extract_from_page(src, text, subject=subject, page_url=url, page_title=title)
    known = [f for f in fs if f.epistemic != "unknown"]
    classes = {
        str(f.value).lower()
        for f in known
        if f.predicate == "product_class" and f.epistemic not in ("unknown", "contradicted")
    }
    return known, classes, infer_morphology(known)


def test_hotel_delivery_torso_is_hospitality_not_humanoid():
    text = (
        "Our robot uses a social torso, a face, and an arm on a rolling base. "
        "It does hotel guest delivery: room service to guest floors, luggage "
        "as a bellhop, and housekeeping amenities to the guest room."
    )
    known, classes, morph = _extract_classes(
        text,
        subject="Relay",
        url="https://www.example-hotel-robot.com/product",
        title="Hotel guest delivery",
    )
    assert "hospitality" in classes
    assert "humanoid" not in classes
    assert morph == "hospitality"
    claims = {f.predicate for f in known if f.value in (True, "true")}
    assert "claims_hospitality" in claims


def test_figure_warehouse_language_stays_humanoid():
    text = (
        "Figure 02 is a commercially deployed bipedal humanoid robot with two "
        "arms, dexterous hands, and a torso. Built for warehouse palletizing "
        "and case pick on the factory floor."
    )
    _, classes, morph = _extract_classes(
        text,
        subject="Figure 02",
        url="https://www.figure.ai/",
        title="Figure 02",
    )
    assert "humanoid" in classes
    assert "warehouse" not in classes
    assert "factory" not in classes
    assert "hospitality" not in classes
    assert morph == "humanoid"
