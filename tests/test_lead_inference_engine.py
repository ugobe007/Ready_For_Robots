"""Tests for lead inference engine logic chain."""
from app.services.lead_inference_engine import evaluate_lead_candidate


def test_rejects_listicle_headline():
    d = evaluate_lead_candidate(
        company_name="7 Best Automatic Wet Cat Food Feeders",
        context_text="We tested the top feeders for your pet.",
    )
    assert d.is_lead is False
    assert d.disposition == "junk"
    assert "listicle" in (d.junk_reason or "")


def test_rejects_job_seo_stub():
    d = evaluate_lead_candidate(
        company_name="Your Job",
        context_text="Career advice for warehouse workers.",
    )
    assert d.is_lead is False


def test_rejects_incomplete_headline():
    d = evaluate_lead_candidate(
        company_name="Modern Mediterranean restaurant to",
        context_text="Opening soon downtown.",
    )
    assert d.is_lead is False


def test_accepts_real_company_with_automation_intent():
    text = (
        "Acme Logistics announced a $12 million warehouse automation initiative "
        "to address labor shortages. The company will deploy AMRs for sortation "
        "and palletizing across three distribution centers. RFP responses due Q3 2026."
    )
    d = evaluate_lead_candidate(
        company_name="Acme Logistics",
        context_text=text,
        signal_types=["warehouse_throughput", "labor_shortage"],
        industry="Logistics",
        employee_estimate=2500,
    )
    assert d.is_lead is True
    assert d.disposition == "lead"
    assert d.tier in ("HOT", "WARM", "COLD")
    assert d.specific_problem
    assert "amr" in " ".join(d.robot_categories).lower() or "material" in " ".join(d.application_areas).lower()
    assert d.procurement.get("has_rfp") is True
    assert d.lead_value_score > 0
    assert len(d.references) >= 2
    assert any(r.get("type") == "inference_rule" for r in d.references)


def test_rejects_market_report_without_buyer_intent():
    d = evaluate_lead_candidate(
        company_name="Global Robotics Market",
        context_text="The global robotics market size is expected to reach $50 billion by 2030.",
    )
    assert d.is_lead is False


def test_rejects_oem_funding_pr_article():
    d = evaluate_lead_candidate(
        company_name="Midwest Fulfillment Group",
        context_text=(
            "Figure AI raises $675M in funding round as robotics startup "
            "accelerates humanoid production and factory expansion."
        ),
    )
    assert d.is_lead is False
    assert "seller" in (d.junk_reason or "").lower() or "vendor" in (d.junk_reason or "").lower()
