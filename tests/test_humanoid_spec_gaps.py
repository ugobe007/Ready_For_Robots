"""Humanoid spec gap analysis tests."""
from app.services.humanoid_spec_gaps import (
    SEED_SPECS_BY_SLUG,
    analyze_robot_gaps,
    scoring_field_defs,
    spec_field_missing,
)


def test_seed_specs_cover_key_fields():
    g1 = SEED_SPECS_BY_SLUG["unitree-g1"]
    assert not spec_field_missing(g1, "top_speed_mps", "numeric")
    assert not spec_field_missing(g1, "payload_kg", "numeric")
    assert not spec_field_missing(g1, "autonomy_level", "enum")


def test_analyze_robot_gaps_sparse():
    gap = analyze_robot_gaps({
        "model_slug": "astribot-s1",
        "name": "Astribot S1",
        "vendor": "Astribot",
        "status": "pilot",
        "specs": {},
        "product_url": None,
        "sources": [],
        "heif_total": 1.5,
        "score_total": 37.5,
        "last_scraped_at": None,
    })
    assert gap["spec_fill_pct"] == 0.0
    assert "top_speed_mps" in gap["missing_scoring_fields"]
    assert "product_url" in gap["missing_row_fields"]


def test_analyze_robot_gaps_full_seed():
    gap = analyze_robot_gaps({
        "model_slug": "unitree-g1",
        "name": "Unitree G1",
        "vendor": "Unitree Robotics",
        "status": "available",
        "specs": SEED_SPECS_BY_SLUG["unitree-g1"],
        "product_url": "https://www.unitree.com/g1",
        "sources": [{"type": "seed"}],
        "heif_total": 2.5,
        "score_total": 62.5,
        "last_scraped_at": "2026-01-01",
    })
    assert gap["spec_fill_pct"] == 100.0
    assert gap["seed_specs_available"] is True
    assert gap["missing_scoring_fields"] == []


def test_scoring_field_defs_match_heif_dimensions():
    names = {f.name for f in scoring_field_defs()}
    assert "top_speed_mps" in names
    assert "has_sdk" in names
    assert "collision_force_n" in names
