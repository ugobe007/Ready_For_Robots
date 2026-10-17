"""Budget confirmed signals become FIND rows only when they name the work."""
from __future__ import annotations

import json
from pathlib import Path

from app.services.buyer_opportunity.phase2_match import jobs_for_classification
from app.services.buyer_opportunity.signal_buyer_rows import (
    BUDGET_CONFIRMED,
    named_industry,
    named_work,
    partition_budget_companies,
    signal_rows_enabled,
)

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "budget_confirmed_headlines.json"


def _fact(value: str) -> dict:
    return {"value": value, "confidence": 0.9, "evidence": value}


def _product(name: str, *, function: str, industries: list[str], form: str = "amr_mobile_robot") -> dict:
    return {
        "product_name": name,
        "offering_type": _fact("robot_product"),
        "form": _fact(form),
        "primary_class": _fact("amr_logistics"),
        "primary_function": _fact(function),
        "industries": [_fact(industry) for industry in industries],
    }


def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("RFR_FIND_SIGNAL_ROWS", raising=False)
    assert signal_rows_enabled() is False
    monkeypatch.setenv("RFR_FIND_SIGNAL_ROWS", "1")
    assert signal_rows_enabled() is True


def test_phrases_do_not_treat_a_headline_verb_as_work():
    assert named_work("Chipotle expands drone pilot, accelerates equipment package deployment.") is None
    assert named_work("Launch Autonomous Robotics Pilot at Terminal B for Airport Guest Experience.") is None
    assert named_work("HPE chosen to deliver intelligent connectivity.") is None
    assert named_work("Wonder, Grubhub test NJ’s first drone food delivery pilot.")[0] == "delivery_transport"
    assert named_industry("Wonder, Grubhub test NJ’s first drone food delivery pilot.") is None
    work = named_work("Walmart to pilot Alphabot robotics for grocery pickup.")
    assert work[0] == "picking_packing_palletizing"
    assert named_industry("Walmart to pilot Alphabot robotics for grocery pickup.") == "grocery"


def test_one_of_39_budget_headlines_names_the_work():
    companies = json.loads(FIXTURE.read_text())
    assert len(companies) == 39
    result = partition_budget_companies(companies)
    assert len(result["rows"]) == 1
    row = result["rows"][0]
    assert row["company_name"] == "Walmart"
    assert row["workflow"] == "picking_packing_palletizing"
    assert row["industry"] == "grocery"
    assert row["readiness_label"] == BUDGET_CONFIRMED
    assert row["signal_expiry"] is None
    assert row["signal_date"]
    assert str(row["source_url"]).startswith("http")
    assert row["why_now"].startswith("Walmart to pilot Alphabot")
    assert len(result["skipped"]) == 38
    wonder = next(item for item in result["skipped"] if item["company_name"] == "Wonder Grubhub")
    assert wonder["reason"] == "no_taxonomy_industry"
    assert wonder["workflow"] == "delivery_transport"
    assert all(item["reason"] == "no_named_workflow" for item in result["skipped"] if item is not wonder)
    by_workflow: dict[str, int] = {}
    for item in result["rows"]:
        by_workflow[item["workflow"]] = by_workflow.get(item["workflow"], 0) + 1
    assert by_workflow == {"picking_packing_palletizing": 1}


def test_real_row_ranks_above_examples_and_joins_like_the_corpus():
    companies = json.loads(FIXTURE.read_text())
    rows = partition_budget_companies(companies)["rows"]
    grocery = _product("Aisle picker", function="picking_packing_palletizing", industries=["grocery"])
    jobs = jobs_for_classification(grocery, signal_rows=rows)
    assert jobs[0]["company_name"] == "Walmart"
    assert jobs[0]["is_example"] is False
    assert jobs[0]["readiness_label"] == BUDGET_CONFIRMED
    assert jobs[0]["for_robot"] == "Aisle picker"
    assert jobs[0]["why_now"].startswith("Walmart to pilot")
    assert all(job["is_example"] for job in jobs[1:])

    diligent = _product("Moxi", function="delivery_transport", industries=["hospital"])
    bot = _product("BOT#25", function="agricultural_task", industries=["agriculture"])
    built = _product("Pile driver", function="construction_task", industries=["construction"])
    quad = _product("Spot", function="inspection", industries=["warehouse_distribution"], form="quadruped")
    for product in (diligent, bot, built, quad):
        matched = jobs_for_classification(product, signal_rows=rows)
        assert all(job["company_name"] != "Walmart" for job in matched)


def test_flag_off_does_not_insert_signal_rows(monkeypatch):
    monkeypatch.delenv("RFR_FIND_SIGNAL_ROWS", raising=False)
    grocery = _product("Aisle picker", function="picking_packing_palletizing", industries=["grocery"])
    jobs = jobs_for_classification(grocery)
    assert all(job.get("readiness_label") is None for job in jobs)
    assert all(job["is_example"] for job in jobs)
