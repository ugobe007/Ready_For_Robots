"""Agtonomy FIND: chrome homepage fails fast; no invented SKU; bounded timeout."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

from app.services.robot_job_search import compose_robot_job_search, profile_is_worth_caching
from app.services.robot_profile_cache import (
    clear_profile_cache_memory,
    get_cached_profile,
    profile_is_chrome_identity,
)
from app.services.robot_understanding_v1.fetch import FetchedPage
from app.services.robot_understanding_v1.pipeline import build_robot_profile
from app.services.robot_understanding_v1.sources import (
    collect_source_pack,
    homepage_is_chrome_only,
)


def setup_function():
    clear_profile_cache_memory()


def _agtonomy_home() -> FetchedPage:
    origin = "https://www.agtonomy.com"
    body = (
        "Agtonomy Home About News Careers. Smart Automation Made Simple. "
        "Let Automation Handle the Routine From mowing to hauling. "
        "Trusted Equipment. About Us Contact Us FAQ News Careers."
    )
    return FetchedPage(
        url=f"{origin}/",
        final_url=f"{origin}/",
        status_code=200,
        title="Agtonomy",
        text=body * 3,
        html=f"<html><title>Agtonomy</title><body>{body}</body></html>",
        links=[
            (f"{origin}/", "Home"),
            (f"{origin}/about", "About"),
            (f"{origin}/news", "News"),
            (f"{origin}/careers", "Careers"),
            (f"{origin}/contact-us", "Contact Us"),
            (f"{origin}/faq", "FAQ"),
            (f"{origin}/privacy", "Privacy"),
            (f"{origin}/terms", "Terms"),
        ],
    )


def test_agtonomy_homepage_is_chrome_only():
    home = _agtonomy_home()
    assert homepage_is_chrome_only(home) is True
    assert homepage_is_chrome_only(home, product_name="Handle") is False


def test_agtonomy_source_pack_is_homepage_only_and_bounded(monkeypatch):
    def fake_fetch(url, timeout=(2.5, 6.0), **kw):
        time.sleep(0.5)
        raise AssertionError(f"must not fetch {url}")

    monkeypatch.setattr(
        "app.services.robot_understanding_v1.sources.fetch_page", fake_fetch
    )
    t0 = time.monotonic()
    pack = collect_source_pack(_agtonomy_home(), max_sources=6)
    elapsed = time.monotonic() - t0
    assert elapsed < 0.25
    assert len(pack) <= 1


def test_agtonomy_build_profile_skips_hub_crawl(monkeypatch):
    home = _agtonomy_home()

    def fake_fetch(url, timeout=(2.5, 6.0), **kw):
        if str(url).rstrip("/").endswith("agtonomy.com"):
            return home
        raise AssertionError(f"chrome identity must not crawl {url}")

    monkeypatch.setattr(
        "app.services.robot_understanding_v1.pipeline.fetch_page", fake_fetch
    )
    monkeypatch.setattr(
        "app.services.robot_understanding_v1.pipeline.lookup_vendor_by_url",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        "app.services.robot_understanding_v1.pipeline.assert_public_http_url",
        lambda u: "https://www.agtonomy.com/" if "agtonomy" in str(u) else u,
    )
    timings: dict = {}
    t0 = time.monotonic()
    profile = build_robot_profile("https://www.agtonomy.com/", timings=timings)
    elapsed = time.monotonic() - t0
    assert elapsed < 1.0
    assert timings.get("source_strategy") == "chrome"
    names = [p.name for p in profile.products]
    assert "Handle" not in names
    payload = profile.to_dict()
    assert profile_is_chrome_identity(payload) is True
    assert profile_is_worth_caching(payload) is True
    notes = " ".join(profile.notes)
    assert "skipped hub crawl" in notes.lower()


def test_agtonomy_compose_shows_class_picker_without_sku(monkeypatch):
    class _Obj:
        def to_dict(self):
            return {
                "company": {"name": "Agtonomy", "primary_domain": "agtonomy.com"},
                "products": [],
                "selected_product": None,
                "needs_product_choice": False,
                "facts": [],
                "sources": [{"url": "https://www.agtonomy.com/"}],
                "coverage_level": "low",
                "profile_confidence": "C",
                "notes": [
                    "Homepage is site chrome (JS shell / nav only) — skipped hub crawl; "
                    "class picker is next. Do not invent a SKU."
                ],
            }

    monkeypatch.setattr(
        "app.services.robot_job_search.build_robot_profile",
        MagicMock(return_value=_Obj()),
    )
    monkeypatch.setattr(
        "app.services.robot_job_search.assert_public_http_url", lambda u: u
    )
    out = compose_robot_job_search("https://www.agtonomy.com/")
    assert out["needs_class_choice"] is True
    assert out["state"] == "qualify_robot"
    assert out["products"] == []
    assert get_cached_profile("https://www.agtonomy.com/", None) is not None


def test_agtonomy_agriculture_type_first_does_not_rebuild(monkeypatch):
    build = MagicMock()
    monkeypatch.setattr("app.services.robot_job_search.build_robot_profile", build)
    monkeypatch.setattr(
        "app.services.robot_job_search.assert_public_http_url", lambda u: u
    )
    t0 = time.monotonic()
    out = compose_robot_job_search(
        "https://www.agtonomy.com/",
        asserted_class="agriculture",
        lookup_grain="robot_type",
    )
    elapsed = time.monotonic() - t0
    build.assert_not_called()
    assert elapsed < 2.0
    assert out["needs_class_choice"] is False
    assert out["state"] != "qualify_robot"
