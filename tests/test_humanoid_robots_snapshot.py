"""Humanoid /robots page snapshot serve path."""
from unittest.mock import patch

from app.services.humanoid_robots_snapshot import (
    hydrate_robots_list_mem_cache,
    serve_robots_list,
)


def test_serve_robots_list_uses_mem_cache():
    payload = {
        "robots": [{"id": 1, "name": "Atlas", "vendor": "Boston Dynamics", "model_slug": "atlas"}],
        "generated_at": "2026-06-12T00:00:00+00:00",
    }
    hydrate_robots_list_mem_cache(payload)
    with patch("app.services.humanoid_robots_snapshot.read_public_cache", return_value=None):
        out = serve_robots_list()
    assert out["robots"][0]["name"] == "Atlas"
