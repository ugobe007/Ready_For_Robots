"""Unknown-industry ontology rescue and headline-stub quarantine."""
import pytest
from types import SimpleNamespace

from app.services.unknown_industry_rescue import (
    is_unknown_industry_headline_stub,
    unknown_industry_rescue_action,
)


def test_headline_stub_detected():
    ok, _ = is_unknown_industry_headline_stub("Moving Beyond")
    assert ok
    ok, _ = is_unknown_industry_headline_stub("Shanghai")
    assert ok


def test_wendys_maps_to_food_service():
    action, value, reason = unknown_industry_rescue_action(
        "Wendy's",
        "Unknown",
        [SimpleNamespace(signal_text="Wendy's opens new location", signal_type="news")],
    )
    assert action == "apply"
    assert value == "Food Service"


def test_novartis_maps_to_medical():
    action, value, _ = unknown_industry_rescue_action(
        "Novartis",
        "Unknown",
        [SimpleNamespace(signal_text="Novartis manufacturing expansion", signal_type="news")],
    )
    assert action == "apply"
    assert value == "Medical Technology"


def test_moving_beyond_quarantined():
    action, _, reason = unknown_industry_rescue_action(
        "Moving Beyond",
        "Unknown",
        [SimpleNamespace(signal_text="Moving Beyond pilot programs", signal_type="news")],
    )
    assert action == "quarantine"
