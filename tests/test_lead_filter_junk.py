"""Junk company-name detection — generic sector phrases are not leads."""
from types import SimpleNamespace

import pytest

from app.services.lead_filter import (
    _company_name_not_corroborated_by_signals,
    classify_lead,
    is_junk,
)


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


def test_peak_season_exact_is_junk():
    assert is_junk("Peak Season")[0] is True


def test_ubs_ticker_headline_rejected_by_logic_engine_not_only_is_junk():
    from app.services.company_validator import is_valid_lead

    assert is_junk("UBS CGNX NASDAQ")[0] is False
    ok, reason = is_valid_lead("UBS CGNX NASDAQ", skip_junk_check=False)
    assert ok is False
    assert "structural" in reason.lower() or "inference" in reason.lower()


def test_scraped_article_title_too_long_is_junk():
    long_headline = (
        "Top robotics and automation companies ranked by financial performance in Q4"
    )
    assert is_junk(long_headline)[0] is True


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
        "Future Proofing. Power Couple ????",
        "Future Proofing and Your Supply Chain",
        "This Power Couple Is Betting on AMRs",
        "Will It Work????",
    ],
)
def test_magazine_style_headline_phrases_are_junk(name):
    assert is_junk(name)[0] is True


@pytest.mark.parametrize(
    "name",
    [
        "Meet Betty Bot",
        "Meet the Team Behind the Robot",
        "New MIT Mecalux",
        "New Stanford Robotics Lab Spinout",
    ],
)
def test_meet_and_new_university_deck_lines_are_junk(name):
    assert is_junk(name)[0] is True


def test_real_brand_without_meet_or_new_univ_prefix_not_junk():
    assert is_junk("Mecalux")[0] is False
    assert is_junk("Mecalux North America")[0] is False


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


@pytest.mark.parametrize(
    "name",
    [
        "Exclusive EQT Bets",
        "Google Cloud Team Up",
        "Distribution Center Jobs While Increasing",
        "Blue Jay Takes Flight Amazon",
        "Kenco GreyOrange",
        "San Jos",
        "Domino Effect",
        "Warehouse DC Operations Survey Tech",
        "Your Warehouse",
        "Melonee Wise",
        "Flexkeeping Rollout Following",
        "Kentucky distribution center",
    ],
)
def test_user_reported_scraper_headline_junk_apr_2026(name):
    junk, reason = is_junk(name)
    assert junk is True, reason


def test_classify_lead_treats_logic_engine_reject_as_junk():
    """API / spotlight use classify_lead — must hide non-company strings from HOT."""
    c = SimpleNamespace(name="Share Insights", industry="Retail", employee_estimate=None)
    junk, reason, pri = classify_lead(c, None, [])
    assert junk is True
    assert pri.tier == "COLD"
    assert any(
        tok in reason.lower()
        for tok in ("junk", "logic", "structural", "inference", "distinctive", "filter")
    )


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


def test_mis_attributed_company_name_not_in_signal_text():
    """Headline fragment as company.name with unrelated article bullets."""
    sigs = [
        SimpleNamespace(signal_text="Fetch Robotics raises funding."),
        SimpleNamespace(signal_text="Starship expands fleet."),
    ]
    assert _company_name_not_corroborated_by_signals("HeadlineFragmentXy", sigs) is True
    assert _company_name_not_corroborated_by_signals("Fetch Robotics", sigs) is False
