"""Humanoid intelligence report tests."""
from app.services.humanoid_intelligence_report import (
    _parse_news_sources,
    build_humanoid_intelligence_report_payload,
)
from app.services.humanoid_intelligence_report_pdf import build_humanoid_intelligence_report_pdf
from app.services.humanoid_scraper import SEED_ROBOTS, compute_scores


def _scored_seed(slug: str, *, sources=None) -> dict:
    robot = next(r for r in SEED_ROBOTS if r["model_slug"] == slug)
    scores = compute_scores(robot["specs"], status=robot["status"], vendor=robot["vendor"])
    return {
        **robot,
        **scores,
        "sources": sources or [{"url": robot.get("product_url"), "type": "seed"}],
    }


def test_parse_news_sources_customers():
    sources = [
        {
            "type": "deployment_news",
            "title": "Agility Digit deploys at BMW plant",
            "url": "https://example.com/1",
            "evidence_level": "deployment",
            "signals": ["deployment", "customer:BMW"],
        },
        {
            "type": "deployment_news",
            "title": "Pilot with GXO",
            "url": "https://example.com/2",
            "evidence_level": "trial",
            "signals": ["trial", "customer:GXO"],
        },
    ]
    parsed = _parse_news_sources(sources)
    assert parsed["deployment_article_count"] == 1
    assert parsed["trial_article_count"] == 1
    assert "BMW" in parsed["named_customers"]
    assert "GXO" in parsed["named_customers"]


def test_intelligence_report_top_ranked():
    robots = [
        _scored_seed("unitree-g1"),
        _scored_seed("agility-digit"),
        _scored_seed("figure-02"),
    ]
    payload = build_humanoid_intelligence_report_payload(robots, top_n=3)
    report = payload["report"]
    assert report["title"].startswith("Humanoid Intelligence")
    assert len(report["executive_summary"]) >= 2
    assert len(report["top_ranked"]) == 3
    leader = report["top_ranked"][0]
    assert leader["rank"] == 1
    assert leader["score_rationale"]["mobility"]["drivers"]
    assert leader["why_top_rank"]
    assert "trials_and_pocs" in leader
    assert "customer_integrations" in leader


def test_intelligence_report_customer_landscape():
    digit = _scored_seed(
        "agility-digit",
        sources=[
            {
                "type": "deployment_news",
                "title": "Digit at BMW",
                "evidence_level": "deployment",
                "signals": ["deployment", "customer:BMW"],
            }
        ],
    )
    payload = build_humanoid_intelligence_report_payload([digit], top_n=1)
    landscape = payload["report"]["customer_landscape"]
    assert any(c["customer"] == "BMW" for c in landscape)


def test_intelligence_report_comparisons():
    robots = [
        _scored_seed("unitree-g1"),
        _scored_seed("agility-digit"),
        _scored_seed("figure-02"),
    ]
    payload = build_humanoid_intelligence_report_payload(robots, top_n=3)
    comparisons = payload["report"]["comparisons"]
    assert len(comparisons["dimension_leaders"]) == 6
    assert len(comparisons["index_vs_deployment"]) == 3
    assert len(comparisons["peer_heif_matrix"]["robots"]) == 3
    assert comparisons["fleet_deployment_tier_breakdown"]


def test_intelligence_report_narrative():
    robots = [
        _scored_seed("unitree-g1"),
        _scored_seed("agility-digit"),
        _scored_seed("figure-02"),
    ]
    payload = build_humanoid_intelligence_report_payload(robots, top_n=3)
    narrative = payload["report"]["narrative"]
    assert narrative.get("market_overview")
    assert len(narrative.get("key_findings") or []) >= 3
    assert narrative["key_findings"][0].get("title")
    assert narrative["key_findings"][0].get("body")
    assert payload["report"]["executive_summary"]


def test_intelligence_report_pdf_bytes():
    robots = [
        _scored_seed("unitree-g1"),
        _scored_seed("agility-digit"),
    ]
    payload = build_humanoid_intelligence_report_payload(robots, top_n=2)
    pdf_bytes, filename = build_humanoid_intelligence_report_pdf(payload)
    assert pdf_bytes[:4] == b"%PDF"
    assert filename.endswith(".pdf")
