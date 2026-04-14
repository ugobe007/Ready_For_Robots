"""
Tests for app/services/crm_extractor.py

Exercises budget, timing, automation requirements, and decision-maker
extraction.  The private extraction functions accept List[tuple[str, str]]
(text, source_url) — we call them directly for unit-level coverage.
"""
import pytest

from app.services.crm_extractor import (
    _extract_budget,
    _extract_timing,
    _extract_automation_requirements,
    _extract_decision_makers,
    BudgetSignal,
    TimingSignal,
    DecisionMaker,
    CRMDescriptors,
)


# ─────────────────────────────────────────────────────────────────────────────
# Budget signals
# ─────────────────────────────────────────────────────────────────────────────

def _budget(text: str):
    return _extract_budget([(text, "")])


@pytest.mark.parametrize("text,expected_min", [
    ("The company plans to invest $2.3 million in new robotics.", 1),
    ("A capex of $500 million has been approved for automation.", 1),
    ("Budget of $4.5M approved for warehouse expansion.", 1),
    ("allocating $12 million for AMR fleet deployment", 1),
    ("No specific dollar amount was mentioned in the announcement.", 0),
])
def test_budget_extraction(text, expected_min):
    signals = _budget(text)
    assert len(signals) >= expected_min, (
        f"Expected >= {expected_min} budget signals in: {text!r}\nGot: {signals}"
    )


def test_budget_amount_str_present():
    signals = _budget("Investing $12.5 million in AMR fleet")
    assert signals
    # amount_str should be a normalized string like "$12.5M"
    assert signals[0].amount_str


def test_budget_amount_usd_is_numeric():
    signals = _budget("A $3 million budget has been allocated for cold storage automation.")
    assert signals
    assert signals[0].amount_usd == pytest.approx(3_000_000, rel=0.1)


def test_budget_context_captured():
    text = "A $3M budget has been allocated for cold storage automation."
    signals = _budget(text)
    assert signals
    # context should contain surrounding sentence text
    assert signals[0].context


def test_budget_deduplication():
    """Two mentions of the ~same amount should produce just one signal."""
    text1 = "Investing $5 million in new robots."
    text2 = "The $5 million investment was confirmed."
    signals = _extract_budget([(text1, ""), (text2, "")])
    assert len(signals) == 1


def test_budget_sorted_by_amount_descending():
    signals = _extract_budget([
        ("Investing $1 million in cobots.", ""),
        ("A $20 million warehouse upgrade approved.", ""),
    ])
    assert len(signals) == 2
    assert signals[0].amount_usd > signals[1].amount_usd


# ─────────────────────────────────────────────────────────────────────────────
# Timing signals
# ─────────────────────────────────────────────────────────────────────────────

def _timing(text: str):
    return _extract_timing([(text, "")])


@pytest.mark.parametrize("text,expected_min", [
    ("The project will be complete by Q3 2026.", 1),
    ("Rollout is expected in early 2027.", 1),
    ("Deployment scheduled for end of fiscal year 2025.", 1),
    ("The system will go live within 6 months.", 1),
    ("No timeline was given for the project.", 0),
])
def test_timing_extraction(text, expected_min):
    signals = _timing(text)
    assert len(signals) >= expected_min, (
        f"Expected >= {expected_min} timing signals in: {text!r}\nGot: {signals}"
    )


def test_timing_label_captured():
    signals = _timing("Automation goes live by end of Q2 2026.")
    assert signals
    label = signals[0].label.upper()
    assert "Q2" in label or "2026" in label


def test_timing_confidence_in_range():
    signals = _timing("The rollout is planned for Q1 2027.")
    assert signals
    assert 0.0 <= signals[0].confidence <= 1.0


def test_timing_deduplication():
    """Same quarter mentioned twice should only appear once."""
    signals = _extract_timing([
        ("Deploy by Q3 2026.", ""),
        ("Target: Q3 2026 for full rollout.", ""),
    ])
    labels = [s.label for s in signals]
    assert labels.count("Q3 2026") <= 1


# ─────────────────────────────────────────────────────────────────────────────
# Automation requirements
# ─────────────────────────────────────────────────────────────────────────────

def _reqs(text: str):
    return _extract_automation_requirements([(text, "")])


@pytest.mark.parametrize("text,expected_terms", [
    ("The facility needs palletizing and cold storage automation.", {"palletiz", "cold storage"}),
    ("Company is deploying AMRs for picking and sortation.", {"amr"}),
    ("Looking for conveyor integration with ERP systems.", set()),  # "conveyor" alone not matched
    ("No specific automation mentioned in this article.", set()),
])
def test_automation_requirements(text, expected_terms):
    reqs = _reqs(text)
    reqs_lower = " ".join(reqs).lower()
    for term in expected_terms:
        assert term in reqs_lower, (
            f"Expected term {term!r} not found in requirements.\nText: {text!r}\nReqs: {reqs}"
        )


def test_automation_deduplication():
    """Same requirement mentioned twice should appear only once."""
    texts = [
        ("The company is investing in AMR technology.", ""),
        ("AMR deployment is planned for next quarter.", ""),
    ]
    reqs = _extract_automation_requirements(texts)
    amr_count = sum(1 for r in reqs if "amr" in r.lower())
    assert amr_count == 1


def test_cobot_requirement():
    reqs = _reqs("The factory is evaluating cobots for assembly work.")
    assert any("cobot" in r.lower() or "collaborative" in r.lower() for r in reqs)


def test_cold_storage_requirement():
    reqs = _reqs("Cold storage automation is required for the new DC.")
    assert any("cold storage" in r.lower() for r in reqs)


# ─────────────────────────────────────────────────────────────────────────────
# Decision maker extraction
# ─────────────────────────────────────────────────────────────────────────────

def _dms(text: str):
    return _extract_decision_makers([(text, "")])


@pytest.mark.parametrize("text,expected_first,expected_last", [
    ("John Smith, VP of Operations, announced the expansion.", "John", "Smith"),
    ("The project is led by Sarah Johnson, Director of Supply Chain.", "Sarah", "Johnson"),
    ("CEO Michael Brown said the company is accelerating automation.", "Michael", "Brown"),
    ("CFO Lisa Chen confirmed the budget has been approved.", "Lisa", "Chen"),
])
def test_decision_maker_detection(text, expected_first, expected_last):
    dms = _dms(text)
    found = any(
        dm.first_name == expected_first and dm.last_name == expected_last
        for dm in dms
    )
    assert found, (
        f"Expected {expected_first} {expected_last} in decision makers.\n"
        f"Text: {text!r}\nFound: {[(dm.first_name, dm.last_name) for dm in dms]}"
    )


def test_decision_maker_title_captured():
    dms = _dms("James Carter, SVP of Automation, announced the deal.")
    assert dms
    assert dms[0].title  # title should be non-empty


def test_no_false_positive_decision_maker():
    """Generic mentions without named individuals should not match."""
    texts = [
        ("The company is growing rapidly.", ""),
        ("Staff at the facility are being retrained.", ""),
    ]
    dms = _extract_decision_makers(texts)
    assert len(dms) == 0, f"Unexpected decision makers: {dms}"


def test_duplicate_decision_makers_deduped():
    texts = [
        ("CEO John Smith announced the deal.", ""),
        ("John Smith, CEO, confirmed the partnership.", ""),
    ]
    dms = _extract_decision_makers(texts)
    matches = [dm for dm in dms if dm.first_name == "John" and dm.last_name == "Smith"]
    assert len(matches) == 1


def test_decision_maker_confidence_in_range():
    dms = _dms("Director Sarah Johnson confirmed the automation roadmap.")
    assert dms
    assert 0.0 <= dms[0].confidence <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# CRMDescriptors computed properties
# ─────────────────────────────────────────────────────────────────────────────

def test_crm_descriptors_has_budget_false_when_empty():
    d = CRMDescriptors()
    assert d.has_budget is False
    assert d.top_budget is None


def test_crm_descriptors_has_timing_false_when_empty():
    d = CRMDescriptors()
    assert d.has_timing is False
    assert d.top_timing is None
