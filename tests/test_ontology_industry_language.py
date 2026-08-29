"""Industry work language in the ontology drives FIND class (R33).

Hospital / clinical copy is healthcare, not humanoid morphology.
SKU names (Moxi) are not required. True humanoids without clinical
work words stay humanoid. Agriculture weeding is not healthcare.
"""
from __future__ import annotations

from app.services.robot_class_qualify import infer_class_from_work_language, normalize_class_id
from app.services.robot_ontology import (
    find_class_from_work_language,
    healthcare_ontology_work_words,
    industry_work_language,
    industry_work_rows,
    match_work_language,
    work_language_outranks_morphology,
)
from app.services.robot_understanding_v1 import facts as F
from app.services.robot_understanding_v1.coverage import infer_morphology
from app.services.robot_understanding_v1.models import RobotSource


def _facts(text: str, *, subject: str, url: str = "https://example.com/robot", title: str = "Robot"):
    src = RobotSource(
        id="s",
        url=url,
        source_type="product",
        fetched_at="t",
        title=title,
        confidence=0.85,
    )
    return F._extract_from_page(src, text, subject=subject, page_url=url, page_title=title)


def _classes(fs) -> set[str]:
    return {
        str(f.value).lower()
        for f in fs
        if f.predicate == "product_class" and f.epistemic not in ("unknown", "contradicted")
    }


def test_ontology_encodes_healthcare_work_words_and_task_model():
    data = industry_work_language()
    assert data.get("rule_id") == "R33"
    assert data.get("inference_order") == ["hardware", "work_language_task_model", "morphology"]
    rows = {r["id"]: r for r in industry_work_rows()}
    hc = rows["healthcare"]
    words = healthcare_ontology_work_words()
    for term in (
        "hospital",
        "clinical",
        "pharmacy",
        "nursing",
        "patient",
        "med-surg",
        "linen",
        "unit-delivery",
    ):
        assert term in words, f"missing healthcare work word {term}"
    assert any("operating room" in w or w == "or" for w in words)
    assert "hospital_logistics_transport" in hc["task_model_ids"]
    assert hc["find_class"] == "healthcare"
    assert "humanoid" in {x.lower() for x in hc["outranks_morphology"]}


def test_every_claimed_industry_has_work_words_and_a_task_model():
    rows = {r["id"]: r for r in industry_work_rows()}
    for industry_id in (
        "healthcare",
        "agriculture",
        "construction",
        "mining",
        "warehouse",
        "logistics",
        "factory",
        "hospitality",
        "food_prep",
        "serving",
        "hotel",
    ):
        row = rows[industry_id]
        assert row.get("class_signals") or row.get("work_words"), industry_id
        assert row.get("task_model_ids"), industry_id


def test_moxi_page_language_is_healthcare_not_humanoid():
    text = (
        "Moxi is a hospital robot and clinical assistant that delivers "
        "supplies, samples, PPE, and medications to nursing units. "
        "It has a social torso, a face, and one arm on a wheeled base."
    )
    fs = _facts(text, subject="Moxi", url="https://www.diligentrobots.com/", title="Moxi")
    known = [f for f in fs if f.epistemic != "unknown"]
    classes = _classes(known)
    assert "healthcare" in classes
    assert "humanoid" not in classes
    assert infer_morphology(known) == "healthcare"
    assert infer_class_from_work_language(text) == "healthcare"
    assert work_language_outranks_morphology(text, "humanoid") is True


def test_hospital_delivery_without_moxi_is_healthcare():
    text = (
        "This wheeled clinical assistant delivers medications, lab samples, "
        "and linen to nursing units and the pharmacy. Hospital unit-delivery "
        "on med-surg floors and the operating room. A social torso and face "
        "help staff recognize the robot; one arm opens doors."
    )
    assert "moxi" not in text.lower()
    assert "diligent" not in text.lower()
    fs = _facts(
        text,
        subject="Unit Delivery Robot",
        url="https://www.example-hospital-robot.com/product",
        title="Hospital unit delivery",
    )
    known = [f for f in fs if f.epistemic != "unknown"]
    classes = _classes(known)
    assert "healthcare" in classes
    assert "humanoid" not in classes
    assert infer_morphology(known) == "healthcare"
    assert find_class_from_work_language(text) == "healthcare"
    claims = {f.predicate for f in known if f.value in (True, "true")}
    assert "claims_healthcare" in claims


def test_figure_style_humanoid_without_clinical_stays_humanoid():
    text = (
        "Figure 02 is a commercially deployed bipedal humanoid robot with two "
        "arms, dexterous hands, and a torso. Built for warehouse palletizing "
        "and case pick on the factory floor."
    )
    fs = _facts(
        text,
        subject="Figure 02",
        url="https://www.figure.ai/",
        title="Figure 02",
    )
    known = [f for f in fs if f.epistemic != "unknown"]
    classes = _classes(known)
    assert "humanoid" in classes
    assert "healthcare" not in classes
    assert infer_morphology(known) == "humanoid"
    assert find_class_from_work_language(text) != "healthcare"
    assert work_language_outranks_morphology(text, "humanoid") is False


def test_agriculture_weeding_language_is_not_healthcare():
    text = (
        "LaserWeeder removes weeds in row crops with lasers. Agricultural "
        "weeding robot for vegetable fields, tractors, and combine rows."
    )
    fs = _facts(
        text,
        subject="LaserWeeder",
        url="https://carbonrobotics.com/laserweeder",
        title="LaserWeeder",
    )
    known = [f for f in fs if f.epistemic != "unknown"]
    classes = _classes(known)
    assert "healthcare" not in classes
    assert infer_class_from_work_language(text) == "agriculture"
    morph = infer_morphology(known)
    assert morph in {"agricultural_robot", "agriculture"}
    assert work_language_outranks_morphology(text, "humanoid") is True
    hit = match_work_language(text)
    assert hit is not None
    assert hit.industry_id == "agriculture"


def test_torso_face_arm_do_not_override_hospital_work():
    text = (
        "Our robot uses a social torso, a face, and an arm on a rolling base. "
        "It does hospital clinical delivery: pharmacy to nursing unit, linen "
        "to med-surg, specimens to the lab, and unit-delivery of PPE."
    )
    assert infer_class_from_work_language(text) == "healthcare"
    fs = _facts(text, subject="Clinical Runner", title="Clinical Runner")
    classes = _classes([f for f in fs if f.epistemic != "unknown"])
    assert "healthcare" in classes
    assert "humanoid" not in classes


def test_qualify_reads_ontology_healthcare_aliases():
    assert normalize_class_id("clinical") == "healthcare"
    assert normalize_class_id("hospital_robot") == "healthcare"
    assert normalize_class_id("medical") == "healthcare"
