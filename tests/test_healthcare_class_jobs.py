"""Healthcare FIND class + Diligent Moxi is not a humanoid torso tile.

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
from app.services.robot_job_search import compose_robot_job_search
from app.services.robot_profile_cache import clear_profile_cache_memory
from app.services.robot_requirement_match import match_jobs_from_profile
from app.services.vendor_robot_lookup import (
    catalog_claim_facts,
    index_robot_names,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
)


def test_picker_includes_healthcare_not_a_duplicate_medical_tile():
    rows = public_class_options()
    ids = [row["id"] for row in rows]
    assert ids.count("healthcare") == 1
    assert "medical" not in ids
    assert "healthcare" in FIND_TILE_CLASSES
    assert ids[-1] == "healthcare"
    by_id = {row["id"]: row for row in rows}
    assert by_id["healthcare"]["label"] == "Healthcare"
    assert "hospital" in by_id["healthcare"]["hint"].lower()


def test_normalize_maps_medical_clinical_hospital_aliases():
    assert normalize_class_id("healthcare") == "healthcare"
    assert normalize_class_id("medical") == "healthcare"
    assert normalize_class_id("medical_robot") == "healthcare"
    assert normalize_class_id("clinical") == "healthcare"
    assert normalize_class_id("hospital") == "healthcare"
    assert normalize_class_id("hospital_robot") == "healthcare"


def test_asserted_healthcare_matches_named_hospital_jobs_not_humanoid():
    profile = apply_asserted_class(
        {
            "company": {"name": "Diligent Robotics"},
            "selected_product": {"name": "Moxi"},
            "facts": [],
            "coverage_level": "low",
        },
        "healthcare",
    )
    caps = derive_capabilities(profile)
    assert caps["healthcare_task"].present is True
    assert caps["manipulate"].present is False
    out = match_jobs_from_profile(profile)
    assert out["state"] == "matches"
    assert out["job_count"] > 0
    families = {j.get("tape_family") for j in out["jobs"]}
    assert families <= {"clinical_delivery", "resident_services"}
    assert "pallet" not in families
    assert "gripper" not in families
    employers = {str(j.get("company_name") or "").strip() for j in out["jobs"]}
    assert all(employers)
    assert not any("humanoid" in (j.get("title") or "").lower() for j in out["jobs"])


def test_thin_healthcare_class_returns_named_employer_jobs():
    profile = thin_class_profile("Diligent Robotics", "healthcare")
    out = match_jobs_from_profile(profile)
    assert out["state"] == "matches"
    assert out["job_count"] > 0
    assert all(str(j.get("company_name") or "").strip() for j in out["jobs"])
    assert all(str(j.get("locality") or "").strip() for j in out["jobs"])


def test_diligent_catalog_is_healthcare_not_humanoid():
    reload_vendor_robots_index()
    vendor = lookup_vendor_by_url("https://www.diligentrobots.com/")
    assert vendor is not None
    assert vendor.get("vendor_name") == "Diligent Robotics"
    assert "Moxi" in index_robot_names(vendor)
    robot = next(r for r in vendor["robots"] if r.get("name") == "Moxi")
    facts = catalog_claim_facts(robot)
    by_pred = {f["predicate"]: f["value"] for f in facts}
    assert by_pred["product_class"] == "healthcare"
    assert by_pred.get("claims_healthcare") is True
    assert by_pred["product_class"] != "humanoid"


def test_find_diligentrobots_is_healthcare_jobs_not_humanoid_empty(monkeypatch):
    import app.services.robot_understanding_v1.pipeline as P
    from app.services.robot_profile_cache import clear_profile_cache_memory as _clear

    _clear()

    def boom(*_a, **_k):
        raise AssertionError("indexed Diligent must not crawl")

    monkeypatch.setattr(P, "fetch_page", boom)
    monkeypatch.setattr(P, "collect_source_pack", boom)
    out = compose_robot_job_search("https://www.diligentrobots.com/")
    assert out["needs_class_choice"] is False
    cls = str(out.get("robot_class") or "")
    assert "humanoid" not in cls.lower()
    assert cls in {"healthcare", "healthcare_robot", "medical_robot"}
    assert out["state"] == "matches"
    assert out["job_count"] > 0
    blob = " ".join(
        f"{j.get('title') or ''} {j.get('company_name') or ''}"
        for j in out.get("jobs") or []
    ).lower()
    assert "no humanoid jobs" not in blob
    assert all(str(j.get("company_name") or "").strip() for j in out["jobs"])
    families = {j.get("tape_family") for j in out["jobs"]}
    assert families <= {"clinical_delivery", "resident_services"}


def test_healthcare_class_search_posts_robot_type_grain():
    clear_profile_cache_memory()
    out = compose_robot_job_search(
        "https://www.diligentrobots.com/",
        asserted_class="healthcare",
        lookup_grain="robot_type",
    )
    assert out["needs_class_choice"] is False
    assert out["state"] != "qualify_robot"
    assert (out.get("job_count") or 0) > 0
    assert "humanoid" not in str(out.get("robot_class") or "").lower()


def test_moxi_page_text_is_healthcare_not_humanoid():
    from app.services.robot_understanding_v1 import facts as F
    from app.services.robot_understanding_v1.coverage import infer_morphology
    from app.services.robot_understanding_v1.models import RobotSource

    src = RobotSource(
        id="s",
        url="https://www.diligentrobots.com/",
        source_type="product",
        fetched_at="t",
        title="Moxi",
        confidence=0.85,
    )
    text = (
        "Moxi is a hospital robot and clinical assistant that delivers "
        "supplies, samples, PPE, and medications to nursing units."
    )
    fs = F._extract_from_page(
        src,
        text,
        subject="Moxi",
        page_url="https://www.diligentrobots.com/",
        page_title="Moxi",
    )
    known = [f for f in fs if f.epistemic != "unknown"]
    preds = {f.predicate: f.value for f in known}
    assert preds.get("product_class") == "healthcare"
    assert preds.get("claims_healthcare") is True
    assert infer_morphology(known) == "healthcare"
    classes = {
        str(f.value).lower()
        for f in known
        if f.predicate == "product_class"
    }
    assert "humanoid" not in classes


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


def test_hospital_delivery_without_moxi_is_healthcare():
    text = (
        "This wheeled clinical assistant delivers medications, lab samples, "
        "and linen to nursing units and the pharmacy. Hospital unit-delivery "
        "on med-surg floors and the operating room. A social torso and face "
        "help staff recognize the robot; one arm opens doors."
    )
    assert "moxi" not in text.lower()
    assert "diligent" not in text.lower()
    known, classes, morph = _extract_classes(
        text,
        subject="Unit Delivery Robot",
        url="https://www.example-hospital-robot.com/product",
        title="Hospital unit delivery",
    )
    assert "healthcare" in classes
    assert "humanoid" not in classes
    assert morph == "healthcare"
    claims = {f.predicate for f in known if f.value in (True, "true")}
    assert "claims_healthcare" in claims


def test_figure_style_humanoid_without_clinical_stays_humanoid():
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
    assert "healthcare" not in classes
    assert morph == "humanoid"


def test_agriculture_weeding_language_is_not_healthcare():
    text = (
        "LaserWeeder removes weeds in row crops with lasers. Agricultural "
        "weeding robot for vegetable fields, tractors, and combine rows."
    )
    _, classes, morph = _extract_classes(
        text,
        subject="LaserWeeder",
        url="https://carbonrobotics.com/laserweeder",
        title="LaserWeeder",
    )
    assert "healthcare" not in classes
    assert morph in {"agricultural_robot", "agriculture"}


def test_torso_face_arm_do_not_override_hospital_work():
    text = (
        "Our robot uses a social torso, a face, and an arm on a rolling base. "
        "It does hospital clinical delivery: pharmacy to nursing unit, linen "
        "to med-surg, specimens to the lab, and unit-delivery of PPE."
    )
    _, classes, _morph = _extract_classes(
        text,
        subject="Clinical Runner",
        url="https://example.com/clinical-runner",
        title="Clinical Runner",
    )
    assert "healthcare" in classes
    assert "humanoid" not in classes
