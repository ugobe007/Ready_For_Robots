"""Tests for the five data-quality improvements (public filter, rescore, shapes, classify)."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.headline_name_shape import passes_headline_name_shape
from app.services.lead_filter import classify_lead
from app.services.lead_rescore import queue_or_inline_rescore, rescore_companies_in_process


@pytest.mark.parametrize(
    "name",
    [
        "Steering",
        "Prior Lake OKs",
        "Hyundai plant",
        "shares",
        "Leveraging",
    ],
)
def test_headline_fragment_singles_rejected(name: str):
    ok, reason = passes_headline_name_shape(name)
    assert not ok, reason


@pytest.mark.parametrize(
    "name",
    [
        "Sysco Corporation",
        "Marriott International",
        "Lineage Logistics",
    ],
)
def test_real_company_names_pass_shape_gate(name: str):
    ok, reason = passes_headline_name_shape(name)
    assert ok, reason


def test_classify_lead_skips_quarantined():
    company = SimpleNamespace(name="Acme Corp", is_internal=False)
    junk, reason, priority = classify_lead(company, None, [])
    assert junk is True
    assert "quarantined" in reason.lower()
    assert priority.tier == "COLD"


def test_public_leads_only_excludes_quarantined():
    from app.api.leads import _public_leads_only

    base = MagicMock()
    _public_leads_only(base)
    base.filter.assert_called_once()
    criterion = base.filter.call_args[0][0]
    assert "is_internal" in str(criterion)


def test_queue_or_inline_rescore_prefers_inline_when_skip_celery(monkeypatch):
    monkeypatch.setenv("SKIP_CELERY", "1")
    db = MagicMock()
    with patch(
        "app.services.lead_rescore.rescore_companies_in_process",
        return_value=2,
    ) as inline:
        result = queue_or_inline_rescore(db, [1, 2])
    inline.assert_called_once_with(db, [1, 2])
    assert result == {"mode": "inline", "updated": 2}


def test_rescore_companies_in_process_updates_scores():
    db = MagicMock()
    company = SimpleNamespace(id=7, name="Acme")
    signal = SimpleNamespace(company_id=7)
    score = SimpleNamespace(
        company_id=7,
        overall_intent_score=0,
        automation_score=0,
        labor_pain_score=0,
        expansion_score=0,
        robotics_fit_score=0,
    )

    db.query.return_value.filter.return_value.first.side_effect = [
        company,
        score,
    ]
    db.query.return_value.filter.return_value.all.return_value = [signal]

    with patch(
        "app.services.lead_rescore.compute_scores",
        return_value={
            "overall_intent_score": 42,
            "automation_score": 10,
            "labor_pain_score": 5,
            "expansion_score": 3,
            "robotics_fit_score": 8,
        },
    ):
        updated = rescore_companies_in_process(db, [7])

    assert updated == 1
    assert score.overall_intent_score == 42
    db.commit.assert_called_once()
