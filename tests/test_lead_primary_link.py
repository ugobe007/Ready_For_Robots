"""Unit tests for lead URL resolution and pipeline hints."""

from app.services.lead_primary_link import enrich_lead_link_fields


def test_website_wins_over_evidence():
    sigs = [{"source_url": "https://news.example/a"}]
    out = enrich_lead_link_fields(
        website="https://corp.example",
        signals=sigs,
        overall_score=50,
    )
    assert out["primary_link_kind"] == "website"
    assert out["primary_link_url"] == "https://corp.example"


def test_evidence_when_no_site():
    sigs = [{"source_url": "https://reuters.com/x"}]
    out = enrich_lead_link_fields(website=None, signals=sigs, overall_score=30)
    assert out["identity_resolution"] == "evidence"
    assert out["primary_link_kind"] == "evidence"


def test_unresolved_low_score_suggests_review():
    out = enrich_lead_link_fields(
        website=None,
        signals=[{"source_url": "seed_v3"}],
        overall_score=10,
        signal_count=1,
    )
    assert out["needs_website_inference"] is True
    assert out["suggested_pipeline_action"] == "review_for_removal"
