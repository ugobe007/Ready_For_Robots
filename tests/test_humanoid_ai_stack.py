"""Tests for humanoid AI stack catalog and API enrichment."""
from app.services.humanoid_ai_stack import (
    AI_STACK_BY_SLUG,
    enrich_robot_with_ai_stack,
    get_ai_stack,
    scoring_specs,
    specs_for_storage,
)
from app.api.humanoid_benchmark import _enrich_robot_scores, _seed_robots_payload


def test_seed_robots_include_ai_stack():
    slugs = {
        "figure-02",
        "generalist-gen1",
        "humanoid-hmnd01-alpha-bipedal",
        "galaxea-kengo",
    }
    payloads = {r["model_slug"]: r for r in _seed_robots_payload()}
    for slug in slugs:
        row = payloads[slug]
        assert row.get("ai_stack"), slug
        assert row["ai_stack"]["primary_model"]
        assert row["specs"].get("ai_stack")


def test_scoring_specs_strips_ai_stack():
    spec = {"payload_kg": 5.0, "ai_stack": {"primary_model": "Test"}}
    physical = scoring_specs(spec)
    assert "ai_stack" not in physical
    assert physical["payload_kg"] == 5.0


def test_specs_for_storage_attaches_catalog():
    stored = specs_for_storage({"height_cm": 170}, "foundation-phantom")
    assert stored["ai_stack"]["primary_model"] == "Cortex"
    assert stored["height_cm"] == 170


def test_enrich_robot_with_ai_stack_from_slug():
    row = enrich_robot_with_ai_stack(
        {"model_slug": "1x-neo", "specs": {}, "vendor": "1X", "status": "pilot"}
    )
    assert row["ai_stack"]["primary_model"].startswith("Redwood")


def test_enrich_preserves_stored_stack():
    custom = {"primary_model": "Custom Brain", "model_family": "hybrid"}
    row = _enrich_robot_scores(
        {
            "model_slug": "unknown-slug",
            "specs": {"ai_stack": custom, "payload_kg": 1},
            "status": "research",
            "vendor": "Test",
            "heif_total": 2.0,
            "score_total": 50,
        }
    )
    assert row["ai_stack"]["primary_model"] == "Custom Brain"


def test_catalog_covers_all_seed_slugs():
    from app.services.humanoid_scraper import SEED_ROBOTS

    missing = [r["model_slug"] for r in SEED_ROBOTS if r["model_slug"] not in AI_STACK_BY_SLUG]
    assert not missing, f"Add AI stacks for: {missing}"
