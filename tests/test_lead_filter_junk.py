"""Junk company-name detection — generic sector phrases are not leads."""
from types import SimpleNamespace

import pytest

from app.services.lead_filter import classify_lead, is_junk


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


@pytest.mark.parametrize(
    "name",
    [
        "Swedish sport airline?",
        "Swedish sports retailer...?",
        "Inside Alaska Airlines....",
        "Inside Delta Operations",
        "Norwegian sports carrier",
        "Why is this not a company???",
    ],
)
def test_editorial_headline_fragments_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, f"expected junk for {name!r}, got: {reason!r}"


@pytest.mark.parametrize(
    "name",
    [
        "Swedish sports retailer Stadium",
        "Swedish Sports Retailer Stadium AB",
    ],
)
def test_descriptor_plus_real_brand_not_junk(name):
    """Nationality + role + actual company name (e.g. Stadium) must not be junk."""
    assert is_junk(name)[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "Ideas Ahead....?",
        "DHL Warehouse Supply Chain Drive...?",
    ],
)
def test_truncated_listicle_logistics_headlines_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, f"expected junk for {name!r}, got: {reason!r}"


@pytest.mark.parametrize(
    "name",
    [
        "Unlock the ROI",
        "Airport",
        "Development",
        "Major DFW Hub in Industry First",
        "Chaos to Consistency: The 2026 Guide",
        "Three supply chain automation leaders",
    ],
)
def test_intelligence_scraper_headline_stubs_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, f"expected junk for {name!r}, got: {reason!r}"


@pytest.mark.parametrize(
    "name",
    [
        "Denver International Airport Authority",
        "Software Development Inc",
        "Airport Retail Group LLC",
    ],
)
def test_names_containing_airport_or_development_tokens_not_junk(name):
    assert is_junk(name)[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "Equipment",
        "EVERSANA Strengthens Position",
        "Acme Corp Strengthens Presence in APAC",
        "GlobalCo Strengthens Leadership Team",
    ],
)
def test_equipment_stub_and_strengthens_headline_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, reason


@pytest.mark.parametrize(
    "name",
    [
        "Eversana",
        "EVERSANA",
        "Medical Equipment Leasing LLC",
    ],
)
def test_real_brand_or_equipment_in_phrase_not_junk(name):
    assert is_junk(name)[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "Share Insights",
        "Using Flexible Robotics",
        "EBRD Grants RON",
    ],
)
def test_headline_fragments_user_reported_feb_2026(name):
    assert is_junk(name)[0] is True


def test_classify_lead_treats_logic_engine_reject_as_junk():
    """API / spotlight use classify_lead — must hide non-company strings from HOT."""
    c = SimpleNamespace(name="Share Insights", industry="Retail", employee_estimate=None)
    junk, reason, pri = classify_lead(c, None, [])
    assert junk is True
    assert pri.tier == "COLD"
    assert "junk" in reason.lower() or "logic engine" in reason.lower()


def test_classify_lead_allows_real_company():
    c = SimpleNamespace(name="Acme Logistics LLC", industry="Logistics", employee_estimate=500)
    junk, reason, pri = classify_lead(c, None, [])
    assert junk is False
    assert reason == ""


def test_short_ticker_brands_not_junk_lg_bp():
    """Cleanup uses is_junk only; must match logic-engine allowlist (see known_brands)."""
    assert is_junk("LG")[0] is False
    assert is_junk("BP")[0] is False
    assert is_junk("3M")[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "Technology Banking Coverage with Veteran Banker",
        "AI agents",
        "These Robotics Companies",
        "Amazon hopes robots can replace 600K future",
        "UF's RoboPI lab",
    ],
)
def test_quality_log_headline_fragments_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, reason
