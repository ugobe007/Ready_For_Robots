"""Pipeline surface selection + assessment-aware ranking."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.lead_secondary_assessment import blend_pipeline_rank_score
from app.services.pipeline_inference_batch import select_pipeline_surface_company_ids


def test_blend_pipeline_rank_score_uses_secondary_when_present():
    company = SimpleNamespace(
        crm_metadata={
            "secondary_assessment": {
                "pillars": {
                    "opportunity_rank": {
                        "sales_opportunity_rank": 80.0,
                        "completeness_score": 0.75,
                    }
                }
            }
        }
    )
    blended = blend_pipeline_rank_score(company, tier_score=60.0)
    assert blended > 60.0
    assert blended == round(0.55 * 80.0 + 0.35 * 60.0 + 0.10 * 0.75 * 100.0, 4)


def test_blend_pipeline_rank_score_falls_back_to_tier_score():
    company = SimpleNamespace(crm_metadata={})
    assert blend_pipeline_rank_score(company, tier_score=72.5) == 72.5


def test_select_pipeline_surface_company_ids_uses_tier_staging():
    db = MagicMock()
    hot_co = SimpleNamespace(id=10)
    warm_co = SimpleNamespace(id=20)
    cold_co = SimpleNamespace(id=30)

    def fake_fetch(_db, tier, *, limit, exclude_ids):
        if tier == "HOT":
            return [(hot_co, False, "", SimpleNamespace(score=90.0, tier="HOT"))]
        if tier == "WARM":
            return [(warm_co, False, "", SimpleNamespace(score=70.0, tier="WARM"))]
        if tier == "COLD":
            return [(cold_co, False, "", SimpleNamespace(score=40.0, tier="COLD"))]
        return []

    with patch("app.api.leads._fetch_staged_by_tier", side_effect=fake_fetch):
        ids = select_pipeline_surface_company_ids(db, limit=100, slots_multiplier=2)

    assert ids == [10, 20, 30]
