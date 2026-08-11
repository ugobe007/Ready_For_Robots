"""Tests for Deployment Evidence engine (no DB required for parse/score)."""
from app.services.deployment_evidence_engine import (
    classify_deployment_stage,
    commercial_evidence_score,
    evidence_level_for,
    extract_metrics,
    parse_deployment_claim,
    primitives_performed_from_text,
)


def test_agreement_is_not_commercial_deployment():
    text = (
        "Figure and Catalyst signed a commercial agreement beginning at "
        "Catalyst's Reno distribution center."
    )
    assert classify_deployment_stage(text) == "AGREEMENT"
    claim = parse_deployment_claim(
        text,
        source_type="oem_press_release",
        vendor_name="Figure",
        robot_model="Figure 02",
        customer_name="Catalyst",
    )
    assert claim["deployment_stage"] == "AGREEMENT"
    assert claim["evidence_level"] in {"E", "D", "C"}


def test_digit_gxo_extracts_totes_and_hours():
    text = (
        "Digit moved more than 100,000 totes at GXO and accumulated more than "
        "65,000 operating hours across nine customer facilities."
    )
    metrics = {m["metric_key"]: m["metric_value_numeric"] for m in extract_metrics(text)}
    assert metrics.get("totes_moved") == 100000
    assert metrics.get("operating_hours") == 65000
    prims = primitives_performed_from_text(
        "Digit unloading totes from AMRs and placing them onto a conveyor feeding pack-out"
    )
    assert "eng.acquire_cart_or_tote" in prims
    claim = parse_deployment_claim(
        text + " Digit unloading totes from AMRs onto a conveyor.",
        source_type="oem_press_release",
        vendor_name="Agility Robotics",
        robot_model="Digit",
        customer_name="GXO",
        facility_name="Flowery Branch, GA",
        work_type="Tote handling",
        workflow={"origin": "AMR", "action": "Unload tote", "destination": "Conveyor"},
    )
    assert claim["evidence_level"] in {"A", "B"}
    assert claim["confidence"] >= 0.7


def test_plans_to_deploy_sets_announced_not_live():
    text = "Company plans to deploy 1,000 robots at its warehouses."
    claim = parse_deployment_claim(text, source_type="public_news", vendor_name="VendorX")
    assert claim["robots_announced"] == 1000
    assert claim.get("robots_live") in (None, 0) or claim["deployment_stage"] in {
        "ANNOUNCED",
        "UNKNOWN",
        "AGREEMENT",
    }


def test_commercial_evidence_score_prefers_production_over_pilots():
    weak = commercial_evidence_score(
        [
            {"deployment_stage": "PILOT", "evidence_level": "D", "customer": "A"},
            {"deployment_stage": "PILOT", "evidence_level": "D", "customer": "B"},
        ]
    )
    strong = commercial_evidence_score(
        [
            {
                "deployment_stage": "COMMERCIAL_DEPLOYMENT",
                "evidence_level": "B",
                "customer": "GXO",
                "metrics": {"operating_hours": 65000},
            },
            {
                "deployment_stage": "EXPANSION",
                "evidence_level": "B",
                "customer": "GXO",
                "metrics": {},
            },
        ]
    )
    assert strong["commercial_evidence_score"] > weak["commercial_evidence_score"]


def test_evidence_level_customer_metrics_is_a():
    assert (
        evidence_level_for(
            source_type="customer_press",
            deployment_stage="COMMERCIAL_DEPLOYMENT",
            has_named_customer=True,
            has_metrics=True,
            is_customer_source=True,
        )
        == "A"
    )
