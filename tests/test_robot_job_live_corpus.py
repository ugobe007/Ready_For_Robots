"""Live robot_jobs overlay onto FIND match corpus — named employer + work only."""
from types import SimpleNamespace

from app.services.robot_job_live_corpus import (
    corpus_row_from_robot_job,
    merge_live_jobs,
    tape_family_for_live_job,
)
from app.services.robot_requirement_match import match_jobs_from_profile


def test_live_row_maps_named_harvest_job_to_agriculture():
    row = SimpleNamespace(
        job_key="abc123harvest",
        company_name="Sunrise Orchards",
        locality="Yakima, WA",
        action="harvest",
        robot_compatible_task="Harvest Worker",
        requirements={"job_function": "harvest", "unknowns": ["compensation"]},
        unknowns=["compensation"],
    )
    mapped = corpus_row_from_robot_job(row)
    assert mapped is not None
    assert mapped["company_name"] == "Sunrise Orchards"
    assert mapped["tape_family"] == "agriculture"
    assert mapped["source"] == "live_scrape"
    assert mapped["job_key"].startswith("live_")


def test_board_name_and_title_as_company_are_not_corpus_rows():
    indeed = SimpleNamespace(
        job_key="indeed1",
        company_name="Indeed",
        locality="Memphis, TN",
        action="picking",
        robot_compatible_task="Order Picker",
        requirements={"job_function": "picking"},
        unknowns=[],
    )
    title = SimpleNamespace(
        job_key="title1",
        company_name="Warehouse Associate",
        locality="Memphis, TN",
        action="material_handling",
        robot_compatible_task="Warehouse Associate",
        requirements={"job_function": "material_handling"},
        unknowns=[],
    )
    assert corpus_row_from_robot_job(indeed) is None
    assert corpus_row_from_robot_job(title) is None


def test_unnamed_workplace_is_not_a_robot_job_card():
    row = SimpleNamespace(
        job_key="noloc",
        company_name="Chipotle",
        locality="",
        action="food_prep",
        robot_compatible_task="Line Cook",
        requirements={"job_function": "food_prep"},
        unknowns=[],
    )
    assert corpus_row_from_robot_job(row) is None


def test_work_language_maps_evs_title_when_function_unknown():
    tape = tape_family_for_live_job(
        job_function="work",
        title="EVS Technician",
        extra_text="Hospital environmental services patient floors",
    )
    assert tape == "disinfection"
    transport = tape_family_for_live_job(
        job_function="work",
        title="Patient Transporter",
        extra_text="Hospital pharmacy linen unit-delivery",
    )
    assert transport == "clinical_delivery"


def test_live_overlay_reaches_requirement_matcher(monkeypatch):
    live = (
        {
            "job_key": "live_chipotle_cook",
            "title": "Line Cook",
            "industry": "Restaurant",
            "path": "food prep",
            "company_name": "Taqueria Luna LLC",
            "locality": "Austin, TX",
            "families": ["manipulator"],
            "actions": ["food_prep"],
            "text": "Line Cook food_prep Taqueria Luna LLC Austin, TX food_prep",
            "source": "live_scrape",
            "tape_family": "food_prep",
            "unknowns": [],
        },
    )
    monkeypatch.setattr(
        "app.services.robot_job_live_corpus.load_live_named_jobs",
        lambda limit=48: live,
    )
    monkeypatch.setattr(
        "app.services.robot_requirement_match.load_corpus",
        lambda: (),
    )
    bundled = ({"job_key": "bundled_only", "title": "x", "company_name": "A", "locality": "B"},)
    merged = merge_live_jobs(bundled)
    assert any(j["job_key"] == "live_chipotle_cook" for j in merged)

    profile = {
        "selected_product": {"name": "Flippy", "display_class": "food_prep"},
        "company": {"name": "Miso Robotics"},
        "facts": [
            {
                "predicate": "claims_food_prep",
                "value": True,
                "epistemic": "explicit",
                "confidence": 0.9,
                "evidence_span": "fry station",
                "source_id": "s0",
            }
        ],
    }
    out = match_jobs_from_profile(profile, limit=12)
    employers = {j.get("company_name") for j in out.get("jobs") or []}
    assert "Taqueria Luna LLC" in employers