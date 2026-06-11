"""Tests for humanoid gap logic engine."""
from app.services.humanoid_gap_engine import (
    build_humanoid_data_plan,
    SOURCE_NEWS_LLM,
    SOURCE_SEED_CATALOG,
)


def _sparse_row():
    return {
        "model_slug": "unitree-g1",
        "name": "Unitree G1",
        "vendor": "Unitree Robotics",
        "status": "available",
        "product_url": None,
        "specs": {"has_estop": True, "payload_kg": 3},
        "sources": [],
        "heif_total": 1.8,
        "score_total": 45.0,
        "last_scraped_at": None,
    }


def test_build_plan_lists_missing_fields_and_why():
    plan = build_humanoid_data_plan(_sparse_row())
    assert plan["model_slug"] == "unitree-g1"
    assert plan["spec_fill_pct"] < 100
    assert plan["missing_items"]
    assert plan["action_plan"]
    assert any(s["step"] == "rescore" for s in plan["action_plan"])
    assert "summary" in plan
    first = plan["missing_items"][0]
    assert first.get("why")
    assert first.get("find_via")


def test_build_plan_prefers_seed_catalog_for_flagship():
    plan = build_humanoid_data_plan(_sparse_row())
    seed_steps = [s for s in plan["action_plan"] if s["step"] == "seed_catalog_merge"]
    assert seed_steps
    assert seed_steps[0]["targets"]
    seedable = [m for m in plan["missing_items"] if m.get("seed_available")]
    assert seedable
    assert SOURCE_SEED_CATALOG in seedable[0]["find_via"]


def test_build_plan_includes_news_for_unseeded_fields():
    row = {
        "model_slug": "obscure-bot-x9",
        "name": "Obscure Bot X9",
        "vendor": "Obscure Robotics",
        "status": "research",
        "product_url": None,
        "specs": {},
        "sources": [],
        "heif_total": 0.5,
        "score_total": 12.0,
    }
    plan = build_humanoid_data_plan(row)
    news_steps = [s for s in plan["action_plan"] if s["step"] == "news_llm_scrape"]
    assert news_steps
    assert news_steps[0]["queries"]
    assert any(SOURCE_NEWS_LLM in m["find_via"] for m in plan["missing_items"])


def test_dimensions_at_risk_when_safety_missing():
    row = _sparse_row()
    plan = build_humanoid_data_plan(row)
    safety_missing = any(
        "safety" in (m.get("dimensions") or [])
        for m in plan["missing_items"]
        if m["field"] in ("collision_force_n", "safety_certified", "force_limited_joints")
    )
    if safety_missing:
        assert "safety" in plan.get("dimensions_at_risk", [])
