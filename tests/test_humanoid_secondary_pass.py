"""Smoke tests for humanoid five-pillar secondary pass."""
from app.services.humanoid_spec_gaps import SEED_SPECS_BY_SLUG
from app.services.humanoid_secondary_pass import (
    build_humanoid_assessment,
    _quality_verdict,
    _capability_rank,
    PILLAR_RANK,
)


def test_quality_verdict_valid():
    row = {"name": "Unitree G1", "vendor": "Unitree Robotics", "model_slug": "unitree-g1"}
    v = _quality_verdict(row)
    assert v["is_valid_humanoid"] is True
    assert v["recommendation"] == "keep"


def test_capability_rank_weights_evidence():
    row = {"heif_total": 3.2, "score_total": 72, "sources": [{"url": "https://x.com", "evidence_level": "deployment"}]}
    gap = {"spec_fill_pct": 80.0, "missing_scoring_fields": ["price_usd"]}
    rank = _capability_rank(row, gap, news_level="deployment")
    assert rank["capability_confidence_rank"] > 50


def test_build_assessment_has_five_pillars():
    row = {
        "model_slug": "unitree-g1",
        "name": "Unitree G1",
        "vendor": "Unitree",
        "sources": [{"url": "https://example.com/a", "title": "G1 deploys", "type": "deployment_news", "evidence_level": "trial"}],
        "heif_total": 2.5,
        "score_total": 60,
    }
    gap = {"spec_fill_pct": 55.0, "missing_scoring_fields": ["price_usd"], "missing_row_fields": []}
    ass = build_humanoid_assessment(row, gap)
    assert set(ass["pillars"].keys()) == {
        "missing_data", "optimize_data", "quality_gate", "additional_data", "capability_rank"
    }
    assert ass["pillars"][PILLAR_RANK]["news_evidence_level"] == "trial"
    assert len(ass["pillars"]["additional_data"]["cited_sources"]) == 1


def test_flagship_sparse_slugs_have_seed_specs():
    for slug in ("figure-03", "agility-digit-2", "tesla-optimus-gen1"):
        assert slug in SEED_SPECS_BY_SLUG
        assert SEED_SPECS_BY_SLUG[slug].get("has_estop") is True
