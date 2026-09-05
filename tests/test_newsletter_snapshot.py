"""Newsletter API snapshot — slim payload and read-only serve path."""
from unittest.mock import patch

from app.services.newsletter_snapshot import (
    hydrate_newsletter_mem_cache,
    get_newsletter_mem_cache,
    slim_edition_for_api,
    serve_api_snapshot,
)


def test_slim_edition_drops_fulltext():
    edition = {
        "latestEdition": {"date": "May 25, 2026", "edition": "#145"},
        "topStories": [
            {
                "company": "Acme",
                "headline": "Acme expands",
                "summary": "Short summary.",
                "fullText": "<p>Very long HTML body that should not ship to the API</p>" * 50,
                "signalStrength": 8,
            }
        ],
        "industryBrief": {"executive_take": "Take", "macro_trends": ["a"] * 10},
    }
    slim = slim_edition_for_api(edition, limit=15)
    story = slim["topStories"][0]
    assert "fullText" not in story
    assert story["company"] == "Acme"
    assert len(slim["industryBrief"]["macro_trends"]) <= 6


def test_serve_api_snapshot_uses_mem_cache():
    edition = slim_edition_for_api(
        {
            "latestEdition": {"date": "May 25, 2026"},
            "topStories": [{"company": "Cached Co", "headline": "Hi", "summary": "x"}],
        },
        limit=15,
    )
    hydrate_newsletter_mem_cache(edition)
    with patch("app.services.newsletter_snapshot.read_public_cache", return_value=None):
        out = serve_api_snapshot(limit=15)
    assert out["topStories"][0]["company"] == "Cached Co"
    assert get_newsletter_mem_cache() is not None
