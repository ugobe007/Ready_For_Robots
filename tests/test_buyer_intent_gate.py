"""Buyer-intent gate assessment and triage routing."""
from types import SimpleNamespace

import pytest

from app.services.buyer_intent_gate import assess_buyer_intent_gate, stamp_buyer_intent_gate
from app.services.lead_filter import classify_lead


def test_known_brand_passes_without_signal_evidence():
    result = assess_buyer_intent_gate(
        company_name="Marriott",
        signals=[
            SimpleNamespace(
                signal_type="news",
                signal_text="Industry roundup mentions several hotel chains.",
            )
        ],
    )
    assert result.passed is True
    assert result.known_brand is True
    assert result.route == "pass"


def test_no_intent_routes_to_quarantine():
    result = assess_buyer_intent_gate(
        company_name="Random Regional Operator",
        signals=[
            SimpleNamespace(
                signal_type="news",
                signal_text="Company mentioned in a general industry newsletter.",
            )
        ],
    )
    assert result.passed is False
    assert result.disposition == "no_intent"
    assert result.route == "quarantine"


def test_seller_story_routes_to_quarantine():
    result = assess_buyer_intent_gate(
        company_name="Morphle Labs",
        signals=[
            SimpleNamespace(
                signal_type="funding_round",
                signal_text="Deeptech startup Morphle Labs raises $5M Series A for healthtech automation platform.",
            )
        ],
    )
    assert result.passed is False
    assert result.disposition == "seller_story"
    assert result.route == "quarantine"


def test_deployment_text_passes_gate():
    result = assess_buyer_intent_gate(
        company_name="Acme Logistics",
        signals=[
            SimpleNamespace(
                signal_type="automation_interest",
                signal_text="Acme Logistics pilots autonomous AMRs to address labor shortages in fulfillment.",
            )
        ],
    )
    assert result.passed is True
    assert result.disposition == "pass"


def test_stamp_writes_crm_metadata():
    company = SimpleNamespace(crm_metadata=None, name="Acme Logistics")
    result = assess_buyer_intent_gate(
        company_name="Acme Logistics",
        signals=[
            SimpleNamespace(
                signal_type="labor_shortage",
                signal_text="Warehouse staffing vacancies remain above 30%.",
            )
        ],
    )
    stamp_buyer_intent_gate(company, result)
    assert company.crm_metadata["buyer_intent_gate"]["passed"] is True
    assert "assessed_at" in company.crm_metadata["buyer_intent_gate"]


def test_classify_lead_aligns_with_no_intent_assessment():
    company = SimpleNamespace(
        name="Random Regional Operator",
        industry="Logistics",
        employee_estimate=None,
        is_internal=True,
    )
    signals = [
        SimpleNamespace(
            signal_type="news",
            signal_text="Brief mention in logistics sector newsletter.",
        )
    ]
    assessment = assess_buyer_intent_gate(company_name=company.name, signals=signals)
    junk, reason, pri = classify_lead(company, None, signals)
    assert assessment.disposition == "no_intent"
    assert junk is True
    assert "buyer opportunity gate" in reason.lower()
    assert pri.tier == "COLD"
