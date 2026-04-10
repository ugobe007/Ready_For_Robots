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


def test_buyer_name_containing_robotics_vendor_token_not_auto_junk():
    """Prefix-only vendor match: do not block arbitrary names ending with a vendor phrase."""
    assert is_junk("Acme Bear Robotics Partnership")[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "Why Automation Is",
        "Why Automation Is the Ally of Hotel Staff",
        "Five Success Factors",
        "Five Success Factors for Human–Robot Collaboration",
        "Florida Restaurant Implements Robot Workers",
        "East Coast Warehouse & Distribution",
    ],
)
def test_article_headlines_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, f"expected junk: {reason!r}"


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


@pytest.mark.parametrize(
    "name",
    [
        "Warehouse Automation",
        "Warehouse Management Top",
        "warehouse management top",
        "WAREHOUSE AUTOMATION",
    ],
)
def test_warehouse_topic_titles_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, reason


@pytest.mark.parametrize(
    "name",
    [
        "Bear Robotics",
        "Unbox Robotics",
        "bear robotics inc",
    ],
)
def test_robot_oems_are_junk_not_buyers(name):
    junk, reason = is_junk(name)
    assert junk is True, reason
    assert "vendor" in reason.lower() or "oem" in reason.lower() or "buyer" in reason.lower()
