"""Humanoid deployment / PoC evidence report tests."""
from app.services.humanoid_deployment_report import (
    build_deployment_summary,
    build_humanoid_deployment_report_payload,
    classify_deployment_tier,
    summarize_robot,
)
from app.services.humanoid_scraper import SEED_ROBOTS, compute_scores


def _scored_seed(slug: str) -> dict:
    robot = next(r for r in SEED_ROBOTS if r["model_slug"] == slug)
    scores = compute_scores(robot["specs"], status=robot["status"], vendor=robot["vendor"])
    return {
        **robot,
        **scores,
        "sources": [{"url": robot.get("product_url"), "type": "seed"}],
    }


def test_classify_fleet_and_commercial():
    unitree = _scored_seed("unitree-g1")
    assert classify_deployment_tier(unitree) == "fleet"

    digit = _scored_seed("agility-digit")
    assert classify_deployment_tier(digit) in ("commercial", "fleet")


def test_classify_research_none():
    row = {
        "model_slug": "unknown-lab",
        "status": "research",
        "specs": {"commercial_deployments": 0},
        "sources": [],
    }
    assert classify_deployment_tier(row) == "none"


def test_classify_pilot_with_sources():
    row = {
        "model_slug": "demo-bot",
        "status": "pilot",
        "specs": {"commercial_deployments": 0},
        "sources": [{"url": "https://example.com/demo"}],
    }
    assert classify_deployment_tier(row) == "poc"


def test_summarize_robot_fields():
    fig = _scored_seed("figure-02")
    summary = summarize_robot(fig)
    assert summary["model_slug"] == "figure-02"
    assert summary["evidence_class"] in ("poc_signal", "deployment_signal", "capability_only")
    assert summary["heif_total"] > 0


def test_build_deployment_summary_counts():
    robots = [_scored_seed(slug) for slug in ("unitree-g1", "agility-digit", "figure-02")]
    summary = build_deployment_summary(robots)
    assert summary["total_robots"] == 3
    assert sum(summary["deployment_tier_breakdown"].values()) == 3
    assert summary["poc_or_better_count"] >= 2
    assert len(summary["key_findings"]) >= 3
    assert len(summary["robots"]) == 3


def test_build_report_payload_envelope():
    robots = [_scored_seed("unitree-g1")]
    payload = build_humanoid_deployment_report_payload(robots)
    assert payload["report"]["title"].startswith("Humanoid Deployment")
    assert payload["report"]["framework"].startswith("HEIF")
    assert "generated_at" in payload
