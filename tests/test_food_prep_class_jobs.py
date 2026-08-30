"""FIND Food prep / Serving / Cleaning — venue kitchens, not hotel housekeeping.

Food prep is hotel / casino / airport kitchens AND QSR make-line — not QSR-only.
Serving is table / drink / bussing (ADAM, Matradee, Servi), not housekeeping.
Cleaning is floor / vacuum / restroom including data centers, not hospital EVS.

Diligent stays healthcare. Do not invent a Chipotle employer here — corpus
seeds are existing grounded jobs; live overlay only with a named posting.
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
from app.services.robot_job_live_corpus import tape_family_for_live_job
from app.services.robot_ontology import find_class_from_work_language
from app.services.robot_requirement_match import match_jobs_from_profile


CHIPOTLE_QSR = (
    "QSR make-line robot for bowl assembly and grill. Fast casual kitchen "
    "automation with ingredient dosing and tortilla prep on the assembly "
    "line kitchen. Prep cook food prep station."
)
HOTEL_KITCHEN = (
    "Hotel kitchen prep cook on the banquet commissary line. Casino kitchen "
    "and airport kitchen culinary. Food preparation at the kitchen station."
)
HOTEL = (
    "Hotel delivery robot for guest-room amenities and luggage. "
    "Bellhop room service on guest floors. Hospitality housekeeping cart."
)
SERVING = (
    "Table service food runner and busser. Cocktail server in hotel dining. "
    "Banquet server waitstaff. Mall food court dining room and airport restaurant."
)
CLEANING = (
    "Hotel janitor and restroom attendant. Data center custodian. "
    "Office building vacuum. Shopping mall floor cleaning. Restaurant janitor."
)
MOXI = (
    "Moxi is a hospital robot assistant for clinical staff. "
    "Pharmacy delivery, nursing units, patient-care floors."
)
HOSPITAL_EVS = (
    "Hospital EVS technician. Environmental services on patient floors. "
    "Sterile processing and dietary aide support."
)


def _blob(out: dict) -> str:
    parts = []
    for j in out.get("jobs") or []:
        parts.append(str(j.get("title") or ""))
        parts.append(str(j.get("company_name") or ""))
        parts.append(str(j.get("tape_family") or ""))
    return " ".join(parts).lower()


def test_food_prep_serving_cleaning_are_find_tiles():
    ids = [row["id"] for row in public_class_options()]
    assert "food_prep" in FIND_TILE_CLASSES
    assert "serving" in FIND_TILE_CLASSES
    assert "cleaning" in FIND_TILE_CLASSES
    assert "food_prep" in ids
    assert "serving" in ids
    assert "cleaning" in ids
    assert ids[-1] == "cleaning"
    assert normalize_class_id("food_prep") == "food_prep"
    assert normalize_class_id("qsr") == "food_prep"
    assert normalize_class_id("hotel_kitchen") == "food_prep"
    assert normalize_class_id("casino_kitchen") == "food_prep"
    assert normalize_class_id("airport_kitchen") == "food_prep"
    assert normalize_class_id("hotel") == "hospitality"
    assert normalize_class_id("food_prep") != "hospitality"
    assert normalize_class_id("serving") == "serving"
    assert normalize_class_id("table_service") == "serving"
    assert normalize_class_id("cleaning") == "cleaning"
    assert normalize_class_id("janitorial") == "cleaning"
    by_id = {row["id"]: row for row in public_class_options()}
    assert by_id["food_prep"]["label"] == "Food prep"
    hint = by_id["food_prep"]["hint"].lower()
    assert "hotel" in hint or "casino" in hint or "airport" in hint
    assert "make-line" in hint or "bowl" in hint or "kitchen" in hint
    assert "food prep" not in by_id["hospitality"]["hint"].lower()
    assert by_id["serving"]["label"] == "Serving"
    assert "housekeep" not in by_id["serving"]["hint"].lower()
    assert by_id["cleaning"]["label"] == "Cleaning"
    assert "data center" in by_id["cleaning"]["hint"].lower()


def test_chipotle_style_copy_is_food_prep_not_hotel():
    assert find_class_from_work_language(CHIPOTLE_QSR) == "food_prep"
    assert find_class_from_work_language(CHIPOTLE_QSR) != "hospitality"
    assert find_class_from_work_language(HOTEL) == "hospitality"
    assert find_class_from_work_language(HOTEL) != "food_prep"
    assert find_class_from_work_language(HOTEL) != "serving"
    assert find_class_from_work_language(HOTEL) != "cleaning"


def test_hotel_casino_airport_kitchens_are_food_prep_not_housekeeping():
    assert find_class_from_work_language(HOTEL_KITCHEN) == "food_prep"
    assert find_class_from_work_language(HOTEL_KITCHEN) != "hospitality"
    assert find_class_from_work_language(HOTEL_KITCHEN) != "serving"


def test_serving_copy_is_not_housekeeping_or_qsr_only():
    assert find_class_from_work_language(SERVING) == "serving"
    assert find_class_from_work_language(SERVING) != "hospitality"
    assert find_class_from_work_language(SERVING) != "food_prep"
    assert find_class_from_work_language(SERVING) != "cleaning"


def test_cleaning_copy_includes_data_centers_not_hospital_evs():
    assert find_class_from_work_language(CLEANING) == "cleaning"
    assert find_class_from_work_language(CLEANING) != "hospitality"
    assert find_class_from_work_language(HOSPITAL_EVS) == "healthcare"
    assert find_class_from_work_language(HOSPITAL_EVS) != "cleaning"


def test_diligent_copy_stays_healthcare():
    assert find_class_from_work_language(MOXI) == "healthcare"
    assert find_class_from_work_language(CHIPOTLE_QSR) != "healthcare"
    assert find_class_from_work_language(SERVING) != "healthcare"
    assert find_class_from_work_language(CLEANING) != "healthcare"


def test_thin_food_prep_returns_kitchen_jobs_not_hilton():
    profile = thin_class_profile("Miso Robotics", "food_prep")
    caps = derive_capabilities(profile)
    assert caps["food_prep"].present is True
    assert caps["hospitality_task"].present is False
    assert caps["serving_task"].present is False
    out = match_jobs_from_profile(profile)
    blob = _blob(out)
    assert "hilton" not in blob
    assert "four seasons" not in blob
    assert "guest luggage" not in blob
    families = {j.get("tape_family") for j in out.get("jobs") or []}
    if out.get("job_count"):
        assert out["state"] == "matches"
        assert families <= {"food_prep"}
        assert all(str(j.get("company_name") or "").strip() for j in out["jobs"])
        assert all(str(j.get("locality") or "").strip() for j in out["jobs"])
    else:
        assert out["state"] in {"matches", "thin_corpus", "could_not_understand"} or (
            out.get("job_count") == 0
        )


def test_thin_serving_is_table_service_not_housekeeping_or_warehouse():
    profile = thin_class_profile("Bear Robotics", "serving")
    caps = derive_capabilities(profile)
    assert caps["serving_task"].present is True
    assert caps["hospitality_task"].present is False
    assert caps["warehouse_task"].present is False
    out = match_jobs_from_profile(profile)
    blob = _blob(out)
    assert "housekeeper" not in blob
    assert "room attendant" not in blob
    families = {j.get("tape_family") for j in out.get("jobs") or []}
    if out.get("job_count"):
        assert families <= {"serve"}
        assert all(str(j.get("company_name") or "").strip() for j in out["jobs"])
    else:
        assert out.get("job_count") == 0 or out["state"] in {
            "matches",
            "thin_corpus",
            "could_not_understand",
        }


def test_thin_cleaning_is_not_hospital_evs_or_housekeeping():
    profile = thin_class_profile("Avidbots", "cleaning")
    caps = derive_capabilities(profile)
    assert caps["surface_clean"].present is True
    assert caps["hard_floor_scrub"].present is True
    assert caps["healthcare_task"].present is False
    assert caps["hospitality_task"].present is False
    out = match_jobs_from_profile(profile)
    families = {j.get("tape_family") for j in out.get("jobs") or []}
    if out.get("job_count"):
        assert families <= {"scrub", "restroom"}
        assert "disinfection" not in families
        assert "clinical_delivery" not in families
        assert "hospitality" not in families
        assert all(str(j.get("company_name") or "").strip() for j in out["jobs"])
    else:
        assert out.get("job_count") == 0 or out["state"] in {
            "matches",
            "thin_corpus",
            "could_not_understand",
        }


def test_floor_scrubber_form_factor_is_not_the_cleaning_domain_tile():
    profile = thin_class_profile("Avidbots", "autonomous_scrubber")
    caps = derive_capabilities(profile)
    assert caps["hard_floor_scrub"].present is True
    assert caps["surface_clean"].present is False


def test_hospitality_tile_still_hotel_not_qsr():
    out = match_jobs_from_profile(thin_class_profile("Relay Robotics", "hospitality"))
    blob = _blob(out)
    assert "chipotle" not in blob
    assert "bowl assembly" not in blob
    assert {j.get("tape_family") for j in out["jobs"]} <= {"hospitality"}


def test_asserted_food_prep_does_not_stamp_hospitality():
    profile = apply_asserted_class(
        {
            "company": {"name": "Miso Robotics"},
            "selected_product": {"name": "Flippy"},
            "facts": [],
            "coverage_level": "low",
        },
        "food_prep",
    )
    classes = {
        str(f.get("value")).lower()
        for f in profile["facts"]
        if f.get("predicate") == "product_class"
    }
    assert "food_prep" in classes
    assert "hospitality" not in classes


def test_live_line_cook_maps_to_food_prep_tape():
    tape = tape_family_for_live_job(
        job_function="food_prep",
        title="Line Cook make line",
        extra_text="QSR bowl assembly grill",
    )
    assert tape == "food_prep"
    from_words = tape_family_for_live_job(
        job_function="work",
        title="Prep cook",
        extra_text=CHIPOTLE_QSR,
    )
    assert from_words == "food_prep"
    hotel_kitchen = tape_family_for_live_job(
        job_function="work",
        title="Banquet cook",
        extra_text=HOTEL_KITCHEN,
    )
    assert hotel_kitchen == "food_prep"


def test_live_busser_and_janitor_map_to_serving_and_cleaning_tapes():
    assert (
        tape_family_for_live_job(
            job_function="serving",
            title="Food runner / busser",
            extra_text="Hotel dining room",
        )
        == "serve"
    )
    assert (
        tape_family_for_live_job(
            job_function="cleaning",
            title="Office Janitor",
            extra_text="Vacuum lobby",
        )
        == "scrub"
    )
    assert (
        tape_family_for_live_job(
            job_function="cleaning",
            title="Restroom attendant",
            extra_text="Airport restroom",
        )
        == "restroom"
    )
    assert (
        tape_family_for_live_job(
            job_function="cleaning",
            title="Data Center Custodian",
            extra_text="Data center floor",
        )
        == "scrub"
    )
