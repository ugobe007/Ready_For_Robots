"""Tests for boolean lead name pre-gate (before ontological inference)."""
import pytest

from app.services.lead_name_gate import (
    check_lead_name,
    filter_name_candidates,
    is_acceptable_lead_name,
)


@pytest.mark.parametrize(
    "name",
    [
        "Distribution Center Jobs While Increasing",
        "Google Cloud Team Up",
        "Your Warehouse",
        "Container Stacking Machine Market",
        "Chinese humanoids",
        "QSR Operators",
        "NJ restaurants",
        "Modern Mediterranean restaurant to",
        "7 Best Automatic Wet Cat Food Feeders",
        "Your Job",
        "Global Robotics Market",
        "Supply Chain Technology",
        "Distribution Centers",
        "War Crisis",
        "Melonee Wise",
    ],
)
def test_headline_junk_rejected(name):
    ok, reason = check_lead_name(name)
    assert ok is False, reason
    assert is_acceptable_lead_name(name) is False


@pytest.mark.parametrize(
    "name",
    [
        "Sysco Corporation",
        "Marriott International",
        "Acme Logistics LLC",
        "Lineage Logistics",
        "Mecalux",
        "Walmart",
    ],
)
def test_real_companies_accepted(name):
    ok, reason = check_lead_name(name)
    assert ok is True, reason
    assert is_acceptable_lead_name(name) is True


def test_filter_name_candidates_drops_junk_preserves_real():
    raw = [
        ("Distribution Centers Turn", 0.9),
        ("Sysco Corporation", 0.7),
        ("Your Job", 0.85),
        ("Marriott", 0.6),
    ]
    filtered = filter_name_candidates(raw)
    names = [n for n, _ in filtered]
    assert "Sysco Corporation" in names
    assert "Marriott" in names
    assert "Distribution Centers Turn" not in names
    assert "Your Job" not in names
    assert filtered[0][1] >= filtered[-1][1]
