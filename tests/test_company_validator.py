"""company_validator.is_valid_lead — logic engine gates."""
import pytest

from app.services.company_validator import is_valid_lead


@pytest.mark.parametrize(
    "name",
    [
        "EVERSANA Strengthens Position",
        "Acme Strengthens Presence in EMEA",
        "GlobalCo Strengthens Leadership Team",
    ],
)
def test_pr_strengthens_headlines_rejected(name):
    ok, reason = is_valid_lead(name)
    assert ok is False
    assert "structural" in reason.lower() or "junk" in reason.lower()


@pytest.mark.parametrize(
    "name",
    [
        "Eversana",
        "EVERSANA",
        "EquipmentShare Inc",
    ],
)
def test_strengthens_pattern_does_not_reject_legitimate_names(name):
    ok, _ = is_valid_lead(name)
    assert ok is True


def test_equipment_alone_rejected_via_junk_filter():
    ok, reason = is_valid_lead("Equipment")
    assert ok is False
    assert "junk" in reason.lower()
