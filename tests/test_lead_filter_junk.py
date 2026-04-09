"""Junk company-name detection — generic sector phrases are not leads."""
import pytest

from app.services.lead_filter import is_junk


@pytest.mark.parametrize(
    "name",
    [
        "Global Outlook.",
        "Global Outlook",
        "Retail Outlook",
        "Supply Chain",
        "supply chain",
        "Supply-Chain",
        "The Supply Chain",
        "Global Supply Chain",
        "Supply Chain Management",
        "VALUE CHAIN",
        "Logistics",
        "Digital Transformation",
    ],
)
def test_sector_phrases_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True
    assert reason


@pytest.mark.parametrize(
    "name",
    [
        "Acme Logistics LLC",
        "Blue Supply Chain Partners Inc",
        "Target Corporation",
        "Faraday Future",
    ],
)
def test_real_company_names_not_junk(name):
    assert is_junk(name)[0] is False
