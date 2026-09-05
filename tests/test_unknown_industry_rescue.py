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


def test_market_report_name_quarantined():
    action, _, reason = unknown_industry_rescue_action(
        "UVC Disinfection Product Market",
        "Unknown",
        [SimpleNamespace(signal_text="market size forecast to 2035", signal_type="news")],
    )
    assert action == "quarantine"
    assert "stub" in reason.lower() or "market" in reason.lower()


def test_flippy_vendor_quarantined():
    action, _, reason = unknown_industry_rescue_action(
        "Flippy",
        "Unknown",
        [SimpleNamespace(signal_text="Miso Robotics Flippy 2 kitchen robot", signal_type="news")],
    )
    assert action == "quarantine"
    assert "vendor" in reason.lower() or "OEM" in reason


def test_tracegains_maps_to_food_processing():
    action, value, _ = unknown_industry_rescue_action(
        "TraceGains",
        "Unknown",
        [SimpleNamespace(signal_text="TraceGains supply chain software", signal_type="news")],
    )
    assert action == "apply"
    assert value == "Food Processing & Manufacturing"


def test_invivoscribe_not_quarantined():
    """Invivoscribe is a real medical diagnostics company (invivoscribe.com)."""
    ok, _ = is_unknown_industry_headline_stub("Invivoscribe")
    assert not ok
    action, value, _ = unknown_industry_rescue_action(
        "Invivoscribe",
        "Unknown",
        [SimpleNamespace(signal_text="Invivoscribe molecular diagnostics expansion", signal_type="news")],
    )
    assert action == "apply"
    assert value == "Medical Technology"


def test_market_research_signals_quarantined():
    action, _, reason = unknown_industry_rescue_action(
        "Industrial Monorails Sector",
        "Unknown",
        [
            SimpleNamespace(
                signal_text="Global market analysis forecast size USD by 2034 indexbox",
                signal_type="news",
            )
        ],
    )
    assert action == "quarantine"
