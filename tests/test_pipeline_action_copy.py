"""Industry-specific pipeline action copy."""
import pytest

from app.services.pipeline_action_copy import (
    industry_automation_context,
    pipeline_action_for_lead,
)


def test_hospitality_action():
    action = pipeline_action_for_lead("Hospitality", tier="HOT")
    assert "housekeeping" in action.lower() or "cleaning" in action.lower()
    assert action.startswith("Priority:")


def test_logistics_automation_context():
    auto, pain = industry_automation_context("Logistics")
    assert "amr" in auto.lower() or "warehouse" in auto.lower()
    assert "labor" in pain.lower() or "throughput" in pain.lower()


def test_casinos_gaming_alias():
    auto, _ = industry_automation_context("Casinos & Gaming")
    assert "clean" in auto.lower() or "delivery" in auto.lower()


def test_cruise_lines_action():
    action = pipeline_action_for_lead("Cruise Lines", tier="WARM")
    assert "crew" in action.lower() or "galley" in action.lower() or "cabin" in action.lower()


def test_labor_signal_prefix():
    action = pipeline_action_for_lead(
        "Healthcare",
        tier="WARM",
        signal_types=["labor_shortage"],
    )
    assert "Staffing pressure" in action


def test_fmt_pipeline_card_includes_pipeline_action():
    from types import SimpleNamespace

    from app.api.leads import _fmt_pipeline_card

    company = SimpleNamespace(
        id=1,
        name="Accor Hotels",
        industry="Hospitality",
        location_city="Paris",
        location_state="",
        employee_estimate=None,
        crm_metadata=None,
        signals=[
            SimpleNamespace(
                signal_type="expansion",
                signal_text="Accor expands robot pilot at flagship hotels in France.",
                signal_strength=0.9,
            )
        ],
        scores=[SimpleNamespace(overall_intent_score=88.0)],
    )
    pri = SimpleNamespace(tier="HOT", score=88.0)
    card = _fmt_pipeline_card(company, False, "", pri, fast=False)
    assert card.get("pipeline_action")
    assert "Hospitality" in card.get("industry", "") or card.get("share_summary")


def test_fmt_pipeline_card_includes_robot_types_needed():
    from types import SimpleNamespace

    from app.api.leads import _fmt_pipeline_card

    company = SimpleNamespace(
        id=2,
        name="FedEx Supply Chain",
        industry="Logistics",
        location_city="Memphis",
        location_state="TN",
        employee_estimate=5000,
        crm_metadata=None,
        automation_profile=None,
        signals=[
            SimpleNamespace(
                signal_type="expansion",
                signal_text="FedEx deploys AMR warehouse automation pilot.",
                signal_strength=0.85,
            )
        ],
        scores=[SimpleNamespace(overall_intent_score=82.0)],
    )
    pri = SimpleNamespace(tier="HOT", score=82.0)
    card = _fmt_pipeline_card(company, False, "", pri, fast=False)
    robots = card.get("robot_types_needed") or []
    assert isinstance(robots, list)
    assert len(robots) >= 1
