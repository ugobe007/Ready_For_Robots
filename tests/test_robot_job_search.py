"""Robot Profile cache + composed job search (submit workflow)."""
from __future__ import annotations

from unittest.mock import MagicMock

from app.services.robot_job_search import compose_robot_job_search
from app.services.robot_profile_cache import (
    clear_profile_cache_memory,
    get_cached_profile,
    normalize_profile_url,
    profile_cache_key,
    set_cached_profile,
)


def setup_function():
    clear_profile_cache_memory()


def test_normalize_profile_url_strips_www_and_slash():
    assert normalize_profile_url("https://www.AgilityRobotics.com/") == "https://agilityrobotics.com/"
    assert profile_cache_key("https://www.agilityrobotics.com") == profile_cache_key(
        "https://agilityrobotics.com/"
    )


def test_memory_cache_roundtrip():
    payload = {"company": {"name": "Agility Robotics"}, "selected_product": {"name": "Digit"}}
    set_cached_profile("https://agilityrobotics.com/", "Digit", payload)
    hit = get_cached_profile("https://www.agilityrobotics.com", "Digit")
    assert hit["selected_product"]["name"] == "Digit"


def test_compose_select_product_does_not_match(monkeypatch):
    profile = {
        "company": {"name": "Boston Dynamics"},
        "products": [
            {"name": "Spot", "display_class": "quadruped"},
            {"name": "Stretch", "display_class": "mobile_manipulator"},
            {"name": "Atlas", "display_class": "humanoid"},
        ],
        "selected_product": None,
        "needs_product_choice": True,
        "facts": [],
        "sources": [],
        "profile_confidence": "C",
    }

    class _Obj:
        def to_dict(self):
            return profile

    monkeypatch.setattr(
        "app.services.robot_job_search.build_robot_profile",
        lambda *a, **k: _Obj(),
    )
    match = MagicMock()
    monkeypatch.setattr("app.services.robot_job_search.match_jobs_from_profile", match)
    monkeypatch.setattr("app.services.robot_job_search.assert_public_http_url", lambda u: u)

    out = compose_robot_job_search("https://bostondynamics.com/")
    assert out["state"] == "select_product"
    assert out["needs_product_choice"] is True
    assert len(out["products"]) == 3
    assert out["jobs"] == []
    assert out["top_jobs"] == []
    match.assert_not_called()
    assert "resolve_ms" in out["timings"]
    assert "total_ms" in out["timings"]


def test_compose_cached_profile_skips_rebuild(monkeypatch):
    payload = {
        "company": {"name": "Dexmate"},
        "selected_product": {"name": "Vega", "display_class": "mobile_manipulator"},
        "products": [{"name": "Vega"}],
        "needs_product_choice": False,
        "facts": [{"predicate": "arm_count", "value": 2}],
        "sources": [],
        "profile_confidence": "B",
    }
    set_cached_profile("https://www.dexmate.ai/", None, payload)
    built = MagicMock()
    monkeypatch.setattr("app.services.robot_job_search.build_robot_profile", built)
    monkeypatch.setattr("app.services.robot_job_search.assert_public_http_url", lambda u: u)
    monkeypatch.setattr(
        "app.services.robot_job_search.match_jobs_from_profile",
        lambda *a, **k: {
            "state": "matches",
            "robot_name": "Vega",
            "company_name": "Dexmate",
            "capabilities": [{"key": "manipulate", "label": "dual-arm"}],
            "families": [],
            "jobs": [
                {
                    "job_key": "cnc_load",
                    "title": "Load parts into CNC",
                    "verdict": "POSSIBLE_MATCH",
                    "why": ["dual-arm manipulation"],
                }
            ],
            "job_count": 12,
            "matcher": "requirement_v1",
            "robot_class": "mobile_manipulator",
        },
    )
    out = compose_robot_job_search("https://www.dexmate.ai/")
    built.assert_not_called()
    assert out["timings"]["cached"] is True
    assert out["state"] == "matches"
    assert out["top_jobs"][0]["job_key"] == "cnc_load"
    assert out["job_count"] == 12
    assert out["profile"]["selected_product"]["name"] == "Vega"


def test_compose_uncached_returns_timings_and_top_jobs(monkeypatch):
    profile = {
        "company": {"name": "Locus Robotics"},
        "selected_product": {"name": "Origin", "display_class": "amr"},
        "products": [{"name": "Origin"}],
        "needs_product_choice": False,
        "facts": [],
        "sources": [{}],
        "profile_confidence": "C",
    }

    class _Obj:
        def to_dict(self):
            return profile

    def _build(*a, **k):
        timings = k.get("timings")
        if timings is not None:
            timings["resolve_ms"] = 120
            timings["profile_ms"] = 800
        return _Obj()

    monkeypatch.setattr("app.services.robot_job_search.build_robot_profile", _build)
    monkeypatch.setattr("app.services.robot_job_search.assert_public_http_url", lambda u: u)
    monkeypatch.setattr(
        "app.services.robot_job_search.match_jobs_from_profile",
        lambda *a, **k: {
            "state": "matches",
            "robot_name": "Origin",
            "company_name": "Locus Robotics",
            "capabilities": [],
            "families": [],
            "jobs": [{"job_key": f"j{i}", "title": f"Tote {i}"} for i in range(8)],
            "job_count": 20,
            "matcher": "requirement_v1",
            "robot_class": "amr",
        },
    )
    out = compose_robot_job_search("https://locusrobotics.com/")
    assert out["timings"]["cached"] is False
    assert out["timings"]["resolve_ms"] == 120
    assert out["timings"]["profile_ms"] == 800
    assert out["timings"]["match_ms"] >= 0
    assert out["timings"]["total_ms"] >= 0
    assert len(out["top_jobs"]) == 5
    assert len(out["jobs"]) == 8
