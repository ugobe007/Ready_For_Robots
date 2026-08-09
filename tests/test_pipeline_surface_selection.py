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


def test_build_public_pipeline_feed_backfills_monitoring_from_warm_tail_when_cold_sparse():
    from app.api.leads import build_public_pipeline_feed

    db = MagicMock()

    def _mk_tuple(cid: int, tier: str, score: float):
        c = SimpleNamespace(id=cid, name=f"C{cid}")
        return (c, False, "", SimpleNamespace(score=score, tier=tier))

    def fake_fetch(_db, tier, *, limit, exclude_ids, pool_cap=None):
        if tier == "HOT":
            return [_mk_tuple(i, "HOT", 95.0 - i) for i in range(1, 16)]
        if tier == "WARM":
            # Enough warm head + tail to synthesize missing monitoring rows.
            return [_mk_tuple(100 + i, "WARM", 75.0 - i * 0.1) for i in range(35)]
        if tier == "COLD":
            # Sparse cold pool.
            return [_mk_tuple(300 + i, "COLD", 40.0 - i) for i in range(2)]
        return []

    def fake_rows(staged, *, slim=False):
        rows = []
        for c, _junk, _reason, pri in staged:
            rows.append(
                {
                    "id": c.id,
                    "company_name": c.name,
                    "priority_tier": pri.tier,
                    "lead_tier": pri.tier,
                }
            )
        return rows

    def fake_fmt_pipeline_card(c, _junk, _reason, pri, fast=False):
        return {
            "id": c.id,
            "company_name": c.name,
            "priority_tier": pri.tier,
            "lead_tier": pri.tier,
        }

    with patch("app.api.leads._fetch_staged_by_tier", side_effect=fake_fetch), patch(
        "app.api.leads._fetch_staged_by_industries", return_value=[]
    ), patch("app.api.leads._staged_tuples_to_feed_rows", side_effect=fake_rows), patch(
        "app.api.leads._fmt_pipeline_card", side_effect=fake_fmt_pipeline_card
    ):
        rows = build_public_pipeline_feed(db, limit=50)

    assert len(rows) == 50
    synth = [r for r in rows if r.get("monitoring_source") == "synthetic_warm_tail"]
    assert len(synth) == 13
    tiers = {"HOT": 0, "WARM": 0, "COLD": 0}
    for r in rows:
        tiers[(r.get("priority_tier") or "").upper()] += 1
    assert tiers == {"HOT": 15, "WARM": 20, "COLD": 15}
