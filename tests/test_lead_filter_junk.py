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


@pytest.mark.parametrize(
    "name",
    [
        "Read More — Hotel Tech Weekly",
        "Acme Corp (Press Release)",
        "contact@acme.com",  # email scrape
        "Source: Hospitality Net",
        "NASDAQ: RBT",
        "Hotel Brand Stock Rises 12% on Earnings",
        "Yahoo Finance",
        "PR Newswire",
        "Research and Markets Report Title",
    ],
)
def test_extended_junk_patterns(name):
    junk, reason = is_junk(name)
    assert junk is True, reason
