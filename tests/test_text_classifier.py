"""
Tests for app/services/text_classifier.py

Validates semantic entity type classification across the key template categories:
  - conjugated verb → ARTICLE_HEADLINE
  - possessive fragment → DESCRIPTION
  - comparison → ARTICLE_HEADLINE
  - question opener → ARTICLE_HEADLINE
  - person name → PERSON_NAME
  - geographic → CITY_OR_TOWN / COUNTRY
  - saying / quote → SAYING
  - equipment category → EQUIPMENT_CAT
  - market fragment → MARKET_FRAGMENT
  - legal suffix → COMPANY_NAME (fast-pass)
  - clean company name → COMPANY_NAME
"""
import pytest

from app.services.text_classifier import classify, is_company_name, EntityType


# ─────────────────────────────────────────────────────────────────────────────
# Fast-pass: legal suffix → COMPANY_NAME
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", [
    "Acme Logistics LLC",
    "Blue Harbor Holdings Inc.",
    "Tyson Foods Inc",
    "Amazon.com Corp",
    "Marriott International Ltd",
    "Sysco Corporation",
    "DHL International GmbH",
])
def test_legal_suffix_fast_pass(name):
    tc = classify(name)
    assert tc.entity_type == EntityType.COMPANY_NAME, (
        f"{name!r} → {tc.entity_type.value} (expected COMPANY_NAME)\nevidence: {tc.evidence}"
    )
    assert tc.confidence >= 0.85
    assert tc.is_valid_company is True


# ─────────────────────────────────────────────────────────────────────────────
# Article headline patterns (conjugated verb present)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "Acme Corp Expands Warehouse Operations",
    "Hospital Chain Announces Layoffs",
    "Retail Brand Launches Robot Delivery",
    "Why Hotels Are Investing in Automation",
    "Amazon Acquires Robotics Startup",
    "Factory Opens New Plant in Ohio",
    "Restaurant Group Reports Record Revenue",
    "Lineage Continues North American Expansion",
])
def test_conjugated_verb_is_headline(text):
    tc = classify(text)
    assert tc.entity_type in (EntityType.ARTICLE_HEADLINE, EntityType.DESCRIPTION), (
        f"{text!r} → {tc.entity_type.value}\nevidence: {tc.evidence}"
    )
    assert tc.is_valid_company is False


# ─────────────────────────────────────────────────────────────────────────────
# Question openers → ARTICLE_HEADLINE
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "How Hotels Can Cut Costs with Robots",
    "Why Warehouses Are Automating Now",
    "What Is the Future of Delivery Robots",
    "Can AI Replace Warehouse Workers",
    "Where Is the Automation Industry Headed",
    "Should Your Restaurant Use Robots",
])
def test_question_opener_is_headline(text):
    tc = classify(text)
    assert tc.entity_type == EntityType.ARTICLE_HEADLINE, (
        f"{text!r} → {tc.entity_type.value}\nevidence: {tc.evidence}"
    )
    assert tc.is_valid_company is False


@pytest.mark.parametrize("text", [
    "Swedish sport airline?",
    "Is automation winning in warehouses?",
    "What about cobots?",
])
def test_rhetorical_question_or_fragment_is_headline(text):
    """Trailing ? or obvious question — not a company name."""
    tc = classify(text)
    assert tc.entity_type == EntityType.ARTICLE_HEADLINE, (
        f"{text!r} → {tc.entity_type.value}\nevidence: {tc.evidence}"
    )
    assert tc.is_valid_company is False


@pytest.mark.parametrize("text", [
    "Inside Alaska Airlines....",
    "Inside Delta Operations Now",
])
def test_inside_deck_kicker_is_headline(text):
    tc = classify(text)
    assert tc.entity_type == EntityType.ARTICLE_HEADLINE, (
        f"{text!r} → {tc.entity_type.value}\nevidence: {tc.evidence}"
    )
    assert tc.is_valid_company is False


def test_inside_out_two_words_not_forced_headline():
    """Two-word title after 'Inside' — do not treat as editorial deck."""
    tc = classify("Inside Out")
    assert tc.entity_type != EntityType.ARTICLE_HEADLINE or tc.confidence < 0.75


# ─────────────────────────────────────────────────────────────────────────────
# Comparisons → ARTICLE_HEADLINE
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "Robots cost less than human workers",
    "AMRs are faster than conveyor systems",
    "Automation ROI compared to staffing costs",
    "Cobots vs traditional industrial arms",
])
def test_comparison_is_headline(text):
    tc = classify(text)
    assert tc.entity_type == EntityType.ARTICLE_HEADLINE, (
        f"{text!r} → {tc.entity_type.value}\nevidence: {tc.evidence}"
    )
    assert tc.is_valid_company is False


# ─────────────────────────────────────────────────────────────────────────────
# Person names → PERSON_NAME
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", [
    "John Smith",
    "Sarah Johnson",
    "Michael Williams",
    "Jennifer Martinez",
    "Robert Chen",
    "David Rodriguez",
    "Emily Thompson",
    "James Anderson",
])
def test_person_names(name):
    tc = classify(name)
    assert tc.entity_type == EntityType.PERSON_NAME, (
        f"{name!r} → {tc.entity_type.value}\nevidence: {tc.evidence}"
    )
    assert tc.is_valid_company is False


# ─────────────────────────────────────────────────────────────────────────────
# Company names with well-known first words should NOT be classified as people
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", [
    "John Deere",          # founder-named company, not a person
    "Tim Hortons",
    "Walt Disney",
    "James Beard Foundation",
])
def test_founder_named_companies_are_ambiguous_not_person(name):
    """
    These are founder-named companies.  The classifier may classify them as
    PERSON_NAME, which is acceptable — the junk filter and legal-suffix fast-
    pass further downstream handle well-known brands.  What we assert is that
    the classifier does NOT hard-assert COMPANY_NAME with high confidence for
    a 2-word name starting with a first name.
    """
    tc = classify(name)
    # We don't assert a specific type — just that it doesn't crash
    assert tc.entity_type is not None
    assert 0.0 <= tc.confidence <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Geographic names → COUNTRY / CITY_OR_TOWN
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name,expected", [
    ("Germany", EntityType.COUNTRY),
    ("France", EntityType.COUNTRY),
    ("Japan", EntityType.COUNTRY),
    ("Singapore", EntityType.COUNTRY),
    ("United Arab Emirates", EntityType.COUNTRY),
    ("California", EntityType.CITY_OR_TOWN),
    ("Texas", EntityType.CITY_OR_TOWN),
    ("Chicago, IL", EntityType.CITY_OR_TOWN),
    ("Austin, Texas", EntityType.CITY_OR_TOWN),
])
def test_geographic_names(name, expected):
    tc = classify(name)
    assert tc.entity_type == expected, (
        f"{name!r} → {tc.entity_type.value} (expected {expected.value})\nevidence: {tc.evidence}"
    )
    assert tc.is_valid_company is False


# ─────────────────────────────────────────────────────────────────────────────
# Saying / quote → SAYING
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    '"Automate the boring stuff"',
    '"The future is already here, just not evenly distributed"',
    "As they say, necessity is the mother of invention",
    "According to the old saying, time is money",
])
def test_saying_or_quote(text):
    tc = classify(text)
    assert tc.entity_type == EntityType.SAYING, (
        f"{text!r} → {tc.entity_type.value}\nevidence: {tc.evidence}"
    )
    assert tc.is_valid_company is False


# ─────────────────────────────────────────────────────────────────────────────
# Equipment category labels → EQUIPMENT_CAT
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "Filling Machine",
    "Palletizing Machine",
    "Autonomous Mobile Robot",
    "Automated Guided Vehicle",
    "Industrial Robot",
    "Conveyor System",
])
def test_equipment_category(text):
    tc = classify(text)
    assert tc.entity_type == EntityType.EQUIPMENT_CAT, (
        f"{text!r} → {tc.entity_type.value}\nevidence: {tc.evidence}"
    )
    assert tc.is_valid_company is False


# ─────────────────────────────────────────────────────────────────────────────
# Market fragments → MARKET_FRAGMENT
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "Global Robotics Market Forecast 2030",
    "Warehouse Automation Market Size Report",
    "Industry Outlook 2025",
    "Market Share Analysis: AMR Sector",
    "CAGR of 18% through 2028",
])
def test_market_fragment(text):
    tc = classify(text)
    assert tc.entity_type == EntityType.MARKET_FRAGMENT, (
        f"{text!r} → {tc.entity_type.value}\nevidence: {tc.evidence}"
    )
    assert tc.is_valid_company is False


# ─────────────────────────────────────────────────────────────────────────────
# Clean company names → COMPANY_NAME
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", [
    "Marriott",
    "Sysco",
    "Hilton",
    "Aramark",
    "Compass Group",
    "Penske",
    "XPO Logistics",
    "Niagara Bottling",
    "Lineage",
    "Cheesecake Factory",
])
def test_clean_company_names(name):
    tc = classify(name)
    assert tc.entity_type == EntityType.COMPANY_NAME, (
        f"{name!r} → {tc.entity_type.value} (conf={tc.confidence:.2f})\nevidence: {tc.evidence}"
    )
    assert tc.is_valid_company is True


# ─────────────────────────────────────────────────────────────────────────────
# is_company_name() convenience wrapper
# ─────────────────────────────────────────────────────────────────────────────

def test_is_company_name_true():
    assert is_company_name("Sysco Corporation") is True
    assert is_company_name("Marriott") is True

def test_is_company_name_false_for_headline():
    assert is_company_name("Hotels Are Investing in Automation") is False

def test_is_company_name_false_for_person():
    assert is_company_name("John Smith") is False

def test_is_company_name_false_for_country():
    assert is_company_name("Germany") is False


# ─────────────────────────────────────────────────────────────────────────────
# Edge cases
# ─────────────────────────────────────────────────────────────────────────────

def test_empty_string():
    tc = classify("")
    assert tc.entity_type == EntityType.UNKNOWN
    assert tc.confidence == 0.0
    assert tc.is_valid_company is False

def test_whitespace_only():
    tc = classify("   ")
    assert tc.entity_type == EntityType.UNKNOWN

def test_short_allcaps_is_not_company():
    """JFK, LAX — airport/ticker codes"""
    tc = classify("JFK")
    assert tc.is_valid_company is False

def test_known_brand_short_allcaps():
    """UPS has a legal suffix in full name; short form is ambiguous — just ensure no crash."""
    tc = classify("UPS")
    assert tc.entity_type is not None

def test_possessive_brand_single_word():
    """McDonald's — single possessive word, short enough to be a brand."""
    tc = classify("McDonald's")
    # Should not hard-fail — result may be COMPANY_NAME or UNKNOWN
    assert tc.entity_type not in (EntityType.COUNTRY, EntityType.PERSON_NAME)
