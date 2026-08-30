"""Source-only Critic: industry work language outranks morphology (R33).

Agent-verify / pstack-release install pytest only. Do not import
robot_understanding_v1.facts (pulls requests via fetch.py). Extractor
proofs live in test_healthcare_class_jobs.py (full CI).
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

HOSPITAL = (
    "Hospital delivery robot for clinical and pharmacy transport. "
    "Nursing unit patient delivery. Operating room supply. "
    "Med-surg linen cart."
)
MOXI = (
    "Moxi is a hospital robot assistant for clinical staff. "
    "Pharmacy delivery, nursing units, patient-care floors."
)
HOTEL = (
    "Hotel delivery robot for guest-room amenities and luggage. "
    "Bellhop room service on guest floors. Hospitality housekeeping cart."
)
FIGURE = (
    "Figure 02 is a commercially deployed bipedal humanoid robot with two "
    "arms, dexterous hands, and a torso. Built for warehouse palletizing "
    "and case pick on the factory floor."
)
WAREHOUSE_HUMANOID = FIGURE
WEEDING = (
    "LaserWeeder removes weeds in row crops with lasers. Agricultural "
    "weeding robot for vegetable fields, tractors, and combine rows."
)
TORSO_HOSPITAL = (
    "Our robot uses a social torso, a face, and an arm on a rolling base. "
    "It does hospital clinical delivery: pharmacy to nursing unit, linen "
    "to med-surg, specimens to the lab, and unit-delivery of PPE."
)


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
        "cleaning",
    ):
        row = rows[industry_id]
        assert row.get("class_signals") or row.get("work_words"), industry_id
        assert row.get("task_model_ids"), industry_id
    assert rows["mining"]["find_class"] == "mining"
    assert rows["warehouse"]["find_class"] == "warehouse"
    assert rows["hospitality"]["find_class"] == "hospitality"
    assert rows["hotel"]["find_class"] == "hospitality"
    assert rows["serving"]["find_class"] == "serving"
    assert rows["food_prep"]["find_class"] == "food_prep"
    assert rows["cleaning"]["find_class"] == "cleaning"


def test_hospital_work_words_are_healthcare_not_humanoid():
    hit = match_work_language(HOSPITAL)
    assert hit is not None
    assert hit.industry_id == "healthcare"
    assert find_class_from_work_language(HOSPITAL) == "healthcare"
    assert infer_class_from_work_language(HOSPITAL) == "healthcare"
    assert work_language_outranks_morphology(HOSPITAL, "humanoid") is True
    assert normalize_class_id("healthcare") == "healthcare"


def test_moxi_page_language_is_healthcare_not_humanoid():
    assert find_class_from_work_language(MOXI) == "healthcare"
    assert infer_class_from_work_language(MOXI) == "healthcare"
    assert work_language_outranks_morphology(MOXI, "humanoid") is True


def test_figure_style_humanoid_without_clinical_stays_unset():
    assert find_class_from_work_language(FIGURE) is None
    assert infer_class_from_work_language(FIGURE) is None
    assert find_class_from_work_language(FIGURE) != "healthcare"
    assert find_class_from_work_language(FIGURE) != "warehouse"
    assert find_class_from_work_language(FIGURE) != "factory"
    assert work_language_outranks_morphology(FIGURE, "humanoid") is False


def test_hotel_work_outranks_torso_and_is_hospitality():
    hit = match_work_language(HOTEL)
    assert hit is not None
    assert hit.industry_id in {"hotel", "hospitality"}
    assert find_class_from_work_language(HOTEL) == "hospitality"
    assert infer_class_from_work_language(HOTEL) == "hospitality"
    assert work_language_outranks_morphology(HOTEL, "humanoid") is True
    assert normalize_class_id("hotel") == "hospitality"
    assert normalize_class_id("food_prep") == "food_prep"
    assert normalize_class_id("mining") == "mining"


def test_warehouse_and_factory_do_not_outrank_humanoid():
    rows = {r["id"]: r for r in industry_work_rows()}
    assert rows["warehouse"]["find_class"] == "warehouse"
    assert rows["factory"]["find_class"] == "factory"
    assert rows["logistics"]["find_class"] == "logistics"
    assert not rows["warehouse"].get("outranks_morphology")
    assert not rows["factory"].get("outranks_morphology")
    assert not rows["logistics"].get("outranks_morphology")
    assert work_language_outranks_morphology(WAREHOUSE_HUMANOID, "humanoid") is False
    assert find_class_from_work_language(WAREHOUSE_HUMANOID) is None


def test_agriculture_weeding_is_not_healthcare():
    hit = match_work_language(WEEDING)
    assert hit is not None
    assert hit.industry_id == "agriculture"
    assert find_class_from_work_language(WEEDING) == "agriculture"
    assert infer_class_from_work_language(WEEDING) == "agriculture"
    assert work_language_outranks_morphology(WEEDING, "humanoid") is True


def test_hospital_work_outranks_torso_face_arm_words():
    assert find_class_from_work_language(TORSO_HOSPITAL) == "healthcare"
    assert infer_class_from_work_language(TORSO_HOSPITAL) == "healthcare"
    assert work_language_outranks_morphology(TORSO_HOSPITAL, "humanoid") is True


def test_conjunction_or_alone_is_not_operating_room():
    text = "Pick this or that SKU from the shelf."
    assert find_class_from_work_language(text) is None
    assert infer_class_from_work_language(text) is None


def test_qualify_reads_ontology_healthcare_aliases():
    assert normalize_class_id("clinical") == "healthcare"
    assert normalize_class_id("hospital_robot") == "healthcare"
    assert normalize_class_id("medical") == "healthcare"


def test_scraped_job_titles_map_to_find_classes():
    """Same class of miss as Diligent: real industry words on job text."""
    from app.services.robot_ontology import healthcare_ontology_work_words

    words = healthcare_ontology_work_words()
    for term in ("evs", "environmental services", "patient transport", "dietary aide"):
        assert term in words, term
    evs = (
        "Hospital EVS technician. Environmental services on patient floors. "
        "Sterile processing and dietary aide support."
    )
    assert find_class_from_work_language(evs) == "healthcare"
    harvest = (
        "Farm worker harvest worker in the orchard. Agricultural tractor operator "
        "for vegetable row crops."
    )
    assert find_class_from_work_language(harvest) == "agriculture"
    haul = (
        "Haul truck operator on the mining bench. Underground mining haulage "
        "from the pit to the crusher."
    )
    assert find_class_from_work_language(haul) == "mining"


CHIPOTLE_QSR = (
    "QSR make-line robot for bowl assembly and grill. Fast casual kitchen "
    "automation with ingredient dosing and tortilla prep on the assembly "
    "line kitchen. Prep cook food prep station."
)


def test_chipotle_style_qsr_copy_is_food_prep_not_hotel():
    hit = match_work_language(CHIPOTLE_QSR)
    assert hit is not None
    assert hit.industry_id == "food_prep"
    assert find_class_from_work_language(CHIPOTLE_QSR) == "food_prep"
    assert infer_class_from_work_language(CHIPOTLE_QSR) == "food_prep"
    assert find_class_from_work_language(CHIPOTLE_QSR) != "hospitality"
    assert work_language_outranks_morphology(CHIPOTLE_QSR, "humanoid") is True
    assert normalize_class_id("food_prep") == "food_prep"
    assert normalize_class_id("qsr") == "food_prep"
    assert normalize_class_id("hotel") == "hospitality"


def test_food_prep_ontology_keeps_qsr_work_words():
    rows = {r["id"]: r for r in industry_work_rows()}
    fp = rows["food_prep"]
    blob = " ".join(
        str(x).lower()
        for x in list(fp.get("work_words") or []) + list(fp.get("class_signals") or [])
    )
    for term in (
        "make line",
        "bowl assembly",
        "grill",
        "prep cook",
        "qsr",
        "fast casual",
        "kitchen automation",
        "ingredient dosing",
        "tortilla",
        "assembly line kitchen",
        "hotel kitchen",
        "casino kitchen",
        "airport kitchen",
    ):
        assert term in blob, term
    assert fp["find_class"] == "food_prep"
    hospitality_aliases = {
        str(a).lower().replace(" ", "_") for a in (rows["hospitality"].get("aliases") or [])
    }
    assert "food_prep" not in hospitality_aliases
    assert "serving" not in hospitality_aliases
    assert "food prep" not in {str(a).lower() for a in (rows["hospitality"].get("aliases") or [])}


def test_diligent_hospital_copy_stays_healthcare():
    assert find_class_from_work_language(MOXI) == "healthcare"
    assert infer_class_from_work_language(MOXI) == "healthcare"
    assert find_class_from_work_language(HOSPITAL) == "healthcare"
    assert find_class_from_work_language(CHIPOTLE_QSR) != "healthcare"
    assert find_class_from_work_language(HOTEL) != "food_prep"
    assert find_class_from_work_language(HOTEL) != "serving"
    assert find_class_from_work_language(HOTEL) != "cleaning"


HOTEL_KITCHEN = (
    "Hotel kitchen prep cook on the banquet commissary line. Casino kitchen "
    "and airport kitchen culinary. Food preparation at the kitchen station."
)
SERVING = (
    "Table service food runner and busser. Cocktail server in hotel dining. "
    "Banquet server waitstaff. Mall food court dining room and airport restaurant."
)
CLEANING = (
    "Hotel janitor and restroom attendant. Data center custodian. "
    "Office building vacuum. Shopping mall floor cleaning. Restaurant janitor."
)


def test_hotel_casino_airport_kitchens_are_food_prep():
    assert find_class_from_work_language(HOTEL_KITCHEN) == "food_prep"
    assert infer_class_from_work_language(HOTEL_KITCHEN) == "food_prep"
    assert find_class_from_work_language(HOTEL_KITCHEN) != "hospitality"


def test_serving_and_cleaning_work_language_are_own_find_classes():
    assert find_class_from_work_language(SERVING) == "serving"
    assert infer_class_from_work_language(SERVING) == "serving"
    assert find_class_from_work_language(CLEANING) == "cleaning"
    assert infer_class_from_work_language(CLEANING) == "cleaning"
    assert find_class_from_work_language(SERVING) != "hospitality"
    assert find_class_from_work_language(CLEANING) != "healthcare"
