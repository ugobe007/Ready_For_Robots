"""Tests for humanoid deployment news RSS scanning."""
from unittest.mock import patch

from app.services.humanoid_deployment_news import (
    article_matches_robot,
    classify_article_evidence,
    news_evidence_level_from_sources,
    scan_humanoid_deployment_news,
)


def test_classify_deployment_headline():
    level, signals = classify_article_evidence({
        "title": "Agility Robotics deploys Digit humanoid fleet at GXO warehouse",
        "description": "",
    })
    assert level == "deployment"
    assert "deployment" in signals


def test_classify_trial_headline():
    level, signals = classify_article_evidence({
        "title": "Figure AI begins pilot program with BMW for humanoid robot trial",
        "description": "",
    })
    assert level == "trial"
    assert "trial" in signals


def test_article_matches_vendor_scope():
    art = {"title": "Apptronik humanoid robot pilot at Mercedes-Benz factory", "description": ""}
    assert article_matches_robot(art, "Apptronik Apollo", "Apptronik", vendor_scope=True)


def test_classify_chinese_deployment_headline():
    level, signals = classify_article_evidence({
        "title": "宇树科技人形机器人在工厂实现量产部署",
        "description": "",
    })
    assert level == "deployment"
    assert "deployment" in signals


def test_news_evidence_from_sources():
    sources = [
        {"type": "deployment_news_zh", "evidence_level": "trial", "title": "试点"},
        {"type": "deployment_news", "evidence_level": "deployment", "title": "deployed"},
    ]
    assert news_evidence_level_from_sources(sources) == "deployment"


def test_scan_aggregates_by_vendor():
    robots = [
        {"name": "Agility Digit", "vendor": "Agility Robotics", "model_slug": "agility-digit", "status": "available"},
        {"name": "Agility Digit 2", "vendor": "Agility Robotics", "model_slug": "agility-digit-2", "status": "pilot"},
    ]

    def fake_rss(query, **kwargs):
        if "Agility Robotics" in query:
            return [{
                "title": "Agility Robotics rolls out Digit humanoid deployment at logistics partner",
                "url": "https://example.com/agility",
                "description": "warehouse deployment pilot",
                "query": query,
                "locale": kwargs.get("locale", "en"),
            }]
        return []

    with patch("app.services.humanoid_deployment_news.fetch_news_rss", side_effect=fake_rss):
        with patch("app.services.humanoid_deployment_news.time.sleep"):
            result = scan_humanoid_deployment_news(robots, sleep_sec=0, include_chinese=False)

    assert result["summary"]["robots_with_trial_or_deployment_news"] == 2
    assert result["summary"]["robots_with_deployment_news"] == 2
    slugs = {r["model_slug"]: r["news_evidence_level"] for r in result["robots"]}
    assert slugs["agility-digit"] == "deployment"
