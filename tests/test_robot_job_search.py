"""Robot Profile cache + composed job search (submit workflow)."""
from __future__ import annotations

from unittest.mock import MagicMock

from app.services.robot_job_search import (
    compose_robot_job_search,
    overlay_selected_product,
    profile_is_research_complete,
    profile_is_worth_caching,
)
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


def test_overlay_selected_product_stamps_sku_and_clears_choice():
    profile = {
        "company": {"name": "Unitree"},
        "needs_product_choice": True,
        "products": [{"name": "G1"}, {"name": "B2"}, {"name": "Go2"}, {"name": "H1"}],
        "selected_product": None,
        "facts": [{"predicate": "payload", "value": "20kg"}],
        "sources": [{"url": "https://www.unitree.com/"}],
    }
    out = overlay_selected_product(profile, "G1")
    assert out["needs_product_choice"] is False
    assert out["selected_product"]["name"] == "G1"
    assert profile["needs_product_choice"] is True  # original not mutated


def test_identity_only_cache_is_not_research_complete():
    assert profile_is_research_complete(
        {
            "company": {"name": "Unitree"},
            "needs_product_choice": True,
            "products": [{"name": "G1"}],
            "facts": [],
            "sources": [],
        }
    ) is False
    assert profile_is_research_complete(
        {
            "company": {"name": "Unitree"},
            "needs_product_choice": False,
            "facts": [{"predicate": "payload", "value": "20kg"}],
            "sources": [],
        }
    ) is True


def test_compose_reuses_grounded_company_cache_for_sku(monkeypatch):
    payload = {
        "company": {"name": "Unitree"},
        "selected_product": {"name": "G1"},
        "products": [{"name": "G1"}, {"name": "B2"}],
        "needs_product_choice": False,
        "facts": [{"predicate": "payload", "value": "20kg"}],
        "sources": [{"url": "https://www.unitree.com/g1"}],
        "profile_confidence": "B",
    }
    set_cached_profile("https://www.unitree.com/", None, payload)
    built = MagicMock()
    monkeypatch.setattr("app.services.robot_job_search.build_robot_profile", built)
    monkeypatch.setattr("app.services.robot_job_search.assert_public_http_url", lambda u: u)
    monkeypatch.setattr(
        "app.services.robot_job_search.match_jobs_from_profile",
        lambda *a, **k: {
            "state": "matches",
            "robot_name": "B2",
            "company_name": "Unitree",
            "capabilities": [],
            "families": [],
            "jobs": [{"job_key": "inspection", "title": "Patrol a site"}],
            "job_count": 8,
            "matcher": "requirement_v1",
            "robot_class": "quadruped",
        },
    )
    out = compose_robot_job_search("https://www.unitree.com/", product="B2")
    built.assert_not_called()
    assert out["timings"]["cached"] is True
    assert out["profile"]["selected_product"]["name"] == "B2"
    assert out["state"] == "matches"


def test_compose_does_not_match_from_identity_only_cache(monkeypatch):
    payload = {
        "company": {"name": "Unitree"},
        "selected_product": None,
        "products": [{"name": "G1"}, {"name": "B2"}],
        "needs_product_choice": True,
        "facts": [],
        "sources": [],
        "profile_confidence": "C",
    }
    set_cached_profile("https://www.unitree.com/", None, payload)

    class _Obj:
        def to_dict(self):
            return {
                "company": {"name": "Unitree"},
                "selected_product": {"name": "G1"},
                "products": [{"name": "G1"}, {"name": "B2"}],
                "needs_product_choice": False,
                "facts": [{"predicate": "payload", "value": "20kg"}],
                "sources": [{"url": "https://www.unitree.com/g1"}],
                "profile_confidence": "B",
            }

    built = MagicMock(return_value=_Obj())
    monkeypatch.setattr("app.services.robot_job_search.build_robot_profile", built)
    monkeypatch.setattr("app.services.robot_job_search.assert_public_http_url", lambda u: u)
    monkeypatch.setattr(
        "app.services.robot_job_search.match_jobs_from_profile",
        lambda *a, **k: {
            "state": "matches",
            "robot_name": "G1",
            "company_name": "Unitree",
            "capabilities": [],
            "families": [],
            "jobs": [{"job_key": "carry", "title": "Move totes"}],
            "job_count": 5,
            "matcher": "requirement_v1",
            "robot_class": "humanoid",
        },
    )
    out = compose_robot_job_search("https://www.unitree.com/", product="G1")
    built.assert_called_once()
    assert out["timings"]["cached"] is False
    assert out["profile"]["selected_product"]["name"] == "G1"


def test_low_coverage_profile_is_not_research_complete():
    thin = {
        "company": {"name": "1X"},
        "selected_product": {"name": "Neo"},
        "needs_product_choice": False,
        "facts": [{"predicate": "carrying_capacity", "value": 18}],
        "sources": [{"url": "https://www.1x.tech/neo"}],
        "coverage_level": "low",
        "profile_confidence": "C",
    }
    assert profile_is_research_complete(thin) is False
    assert profile_is_worth_caching(thin) is False
    grounded = {**thin, "coverage_level": "medium"}
    assert profile_is_research_complete(grounded) is True
    assert profile_is_worth_caching(grounded) is True


def test_compose_does_not_cache_low_coverage(monkeypatch):
    class _Obj:
        def to_dict(self):
            return {
                "company": {"name": "1X"},
                "selected_product": {"name": "Neo"},
                "products": [{"name": "Neo"}],
                "needs_product_choice": False,
                "facts": [{"predicate": "carrying_capacity", "value": 18}],
                "sources": [{"url": "https://www.1x.tech/neo"}],
                "coverage_level": "low",
                "profile_confidence": "C",
            }

    monkeypatch.setattr("app.services.robot_job_search.build_robot_profile", MagicMock(return_value=_Obj()))
    monkeypatch.setattr("app.services.robot_job_search.assert_public_http_url", lambda u: u)
    monkeypatch.setattr(
        "app.services.robot_job_search.match_jobs_from_profile",
        lambda *a, **k: {
            "state": "could_not_understand",
            "robot_name": "Neo",
            "company_name": "1X",
            "capabilities": [],
            "families": [],
            "jobs": [],
            "job_count": 0,
            "matcher": "requirement_v1",
            "robot_class": None,
        },
    )
    compose_robot_job_search("https://www.1x.tech/neo")
    assert get_cached_profile("https://www.1x.tech/neo", None) is None


def test_compose_robot_type_skips_sku_scrape(monkeypatch):
    """Lineup type-first must not build five SKU profiles."""
    build = MagicMock()
    monkeypatch.setattr("app.services.robot_job_search.build_robot_profile", build)
    monkeypatch.setattr("app.services.robot_job_search.assert_public_http_url", lambda u: u)
    out = compose_robot_job_search(
        "https://www.fftai.com/en",
        asserted_class="humanoid",
        lookup_grain="robot_type",
    )
    build.assert_not_called()
    assert out["state"] == "matches"
    assert out["job_count"] > 0
    assert out["company_name"] == "Fourier Intelligence"
    assert out["robot_class"] == "humanoid"
    assert out["timings"]["total_ms"] < 5000
    assert get_cached_profile("https://www.fftai.com/en", None) is None

