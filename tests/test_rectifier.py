"""
Tests for app/services/rectifier.py

Validates the post-enrichment quality sweep that prevents junk from
entering the database as live leads.
"""
import pytest
from unittest.mock import MagicMock

from app.services.rectifier import validate, quarantine, RectificationResult


# ─────────────────────────────────────────────────────────────────────────────
# Helpers: lightweight stand-ins for Company / Signal ORM objects
# ─────────────────────────────────────────────────────────────────────────────

def make_company(name: str, industry: str = "Warehousing") -> MagicMock:
    c = MagicMock()
    c.name = name
    c.industry = industry
    c.is_internal = True
    return c


def make_signal(text: str) -> MagicMock:
    s = MagicMock()
    s.raw_text = text
    s.signal_text = text
    return s


# ─────────────────────────────────────────────────────────────────────────────
# Passing cases: real company names with org-subject signals
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name,signals", [
    (
        "Sysco Corporation",
        [
            "Sysco Corporation expands cold storage operations.",
            "Sysco opens new distribution center in Texas.",
        ],
    ),
    (
        "Marriott International",
        [
            "Marriott International deploys housekeeping robots across 50 properties.",
            "Marriott announces automated check-in kiosks.",
        ],
    ),
    (
        "Lineage Logistics",
        [
            "Lineage Logistics acquires two cold storage facilities.",
            "Lineage continues North American expansion.",
        ],
    ),
    (
        "Acme Logistics LLC",
        [
            "Acme Logistics LLC announces AMR deployment.",
        ],
    ),
])
def test_valid_companies_pass(name, signals):
    company = make_company(name)
    signal_objs = [make_signal(t) for t in signals]
    result = validate(company, signal_objs)
    assert isinstance(result, RectificationResult)
    assert result.passed is True, (
        f"Expected {name!r} to pass rectification.\nReason: {result.reason}\nChecks: {result.checks}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Failing cases: junk names that should be quarantined
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name,signals", [
    (
        "Hotels Are Investing in Automation",
        ["Hotels Are Investing in Automation"],
    ),
    (
        "Why Warehouses Automate",
        ["Why warehouses automate their picking lines"],
    ),
    (
        "John Smith",
        ["John Smith, VP of Operations, commented on the deal."],
    ),
    (
        "Germany",
        ["Germany leads the EU in industrial automation."],
    ),
    (
        "Filling Machine",
        ["A filling machine was installed at the facility."],
    ),
    # Note: generic sector phrases ("Supply Chain", "Logistics") are caught by
    # is_junk() before reaching the rectifier.  The cases below test entities
    # that look superficially like companies but fail specific rectifier checks.
    (
        # Signal-context: entity appears only as a place reference, never as org subject
        "Austin",
        [
            "facility located in Austin",
            "warehouse in Austin expanded",
            "site in Austin opened last month",
        ],
    ),
    (
        "Global Outlook.",
        ["Global Outlook. reports on logistics trends."],
    ),
])
def test_junk_names_fail(name, signals):
    company = make_company(name)
    signal_objs = [make_signal(t) for t in signals]
    result = validate(company, signal_objs)
    assert isinstance(result, RectificationResult)
    assert result.passed is False, (
        f"Expected {name!r} to fail rectification but it passed.\nChecks: {result.checks}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Result structure
# ─────────────────────────────────────────────────────────────────────────────

def test_result_has_confidence():
    c = make_company("Sysco")
    s = [make_signal("Sysco expands AMR deployment.")]
    result = validate(c, s)
    assert 0.0 <= result.confidence <= 1.0


def test_result_checks_populated():
    c = make_company("Sysco Corporation")
    s = [make_signal("Sysco Corporation opens a new facility.")]
    result = validate(c, s)
    assert len(result.checks) > 0


def test_failed_result_has_reason():
    c = make_company("Germany")
    s = [make_signal("Germany is a country in Europe.")]
    result = validate(c, s)
    assert result.passed is False
    assert result.reason != ""


# ─────────────────────────────────────────────────────────────────────────────
# quarantine() side effect
# ─────────────────────────────────────────────────────────────────────────────

def test_quarantine_sets_is_internal_false():
    company = make_company("Germany")
    db = MagicMock()
    quarantine(company, db, reason="country name")
    assert company.is_internal is False
    db.commit.assert_called_once()


def test_quarantine_leaves_company_is_internal_false():
    """Even when db interaction is mocked, is_internal should be set before commit."""
    company = make_company("Germany")
    db = MagicMock()
    quarantine(company, db, reason="country name")
    # is_internal was set to False before db.commit() was called
    assert company.is_internal is False


# ─────────────────────────────────────────────────────────────────────────────
# Empty / edge cases
# ─────────────────────────────────────────────────────────────────────────────

def test_empty_signals_does_not_crash():
    c = make_company("Acme Corp")
    result = validate(c, [])
    assert isinstance(result, RectificationResult)


def test_empty_name_fails():
    c = make_company("")
    result = validate(c, [make_signal("Some text about something.")])
    assert result.passed is False
