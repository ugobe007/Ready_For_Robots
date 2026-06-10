"""Tests for secondary assessment (five pillars + opportunity rank)."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.lead_secondary_assessment import (
    PILLAR_QUALITY,
    PILLAR_RANK,
    build_secondary_assessment,
)


def _company():
    return SimpleNamespace(
        id=10,
        name="Acme Logistics",
        industry="Logistics",
        website="https://acme.example",
        employee_estimate=5000,
        is_internal=True,
        scores=[SimpleNamespace(overall_intent_score=82.0)],
        signals=[],
        crm_metadata={
            "enrichment_ledger": {"rectification": {"status": "passed"}},
            "lead_inference": {"specific_problem": "Labor gap", "robot_categories": ["amr"]},
        },
    )


def test_build_secondary_assessment_ranks_opportunity():
    company = _company()
    signals = [
        SimpleNamespace(
            signal_type="expansion",
            signal_text="Acme plans $4M warehouse automation rollout Q3.",
            created_at=None,
        )
    ]
    contacts = [SimpleNamespace(email="ops@acme.example", title="VP Ops")]

    with patch("app.services.lead_secondary_assessment.classify_lead") as mock_cl:
        mock_cl.return_value = (False, "", SimpleNamespace(tier="HOT", reasons=["Strong signals"]))
        assessment = build_secondary_assessment(
            company,
            signals,
            contacts,
            fields_filled=["contact"],
        )

    assert assessment["pillars"][PILLAR_QUALITY]["is_sales_lead"] is True
    rank = assessment["pillars"][PILLAR_RANK]
    assert rank["sales_opportunity_rank"] > 0
    assert rank["lead_value_score"] >= 0
    assert "data_dimension_scores" in rank
