"""FIND Food prep class is QSR make-line work, not hotel hospitality.

Full CI (requirements.txt). Chipotle-style copy must not classify as hotel.
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
HOTEL = (
    "Hotel delivery robot for guest-room amenities and luggage. "
    "Bellhop room service on guest floors. Hospitality housekeeping cart."
)
MOXI = (
    "Moxi is a hospital robot assistant for clinical staff. "
    "Pharmacy delivery, nursing units, patient-care floors."
)


def _blob(out: dict) -> str:
    parts = []
    for j in out.get("jobs") or []:
        parts.append(str(j.get("title") or ""))
        parts.append(str(j.get("company_name") or ""))
        parts.append(str(j.get("tape_family") or ""))
    return " ".join(parts).lower()


def test_food_prep_is_its_own_find_tile():
    ids = [row["id"] for row in public_class_options()]
    assert "food_prep" in FIND_TILE_CLASSES
    assert "food_prep" in ids
    assert ids[-1] == "food_prep"
    assert normalize_class_id("food_prep") == "food_prep"
    assert normalize_class_id("qsr") == "food_prep"
    assert normalize_class_id("hotel") == "hospitality"
    assert normalize_class_id("food_prep") != "hospitality"
    by_id = {row["id"]: row for row in public_class_options()}
    assert by_id["food_prep"]["label"] == "Food prep"
    assert "make-line" in by_id["food_prep"]["hint"].lower() or "bowl" in by_id[
        "food_prep"
    ]["hint"].lower()
    assert "food prep" not in by_id["hospitality"]["hint"].lower()


def test_chipotle_style_copy_is_food_prep_not_hotel():
    assert find_class_from_work_language(CHIPOTLE_QSR) == "food_prep"
    assert find_class_from_work_language(CHIPOTLE_QSR) != "hospitality"
    assert find_class_from_work_language(HOTEL) == "hospitality"
    assert find_class_from_work_language(HOTEL) != "food_prep"


def test_diligent_copy_stays_healthcare():
    assert find_class_from_work_language(MOXI) == "healthcare"
    assert find_class_from_work_language(CHIPOTLE_QSR) != "healthcare"


def test_thin_food_prep_returns_kitchen_jobs_not_hilton():
    profile = thin_class_profile("Miso Robotics", "food_prep")
    caps = derive_capabilities(profile)
    assert caps["food_prep"].present is True
    assert caps["hospitality_task"].present is False
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
