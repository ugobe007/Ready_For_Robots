"""Richtech URL lookup must be fast when the live host challenges bots."""
from __future__ import annotations

import time

from app.services.robot_understanding_v1.fetch import FetchedPage
from app.services.robot_understanding_v1.pipeline import build_robot_profile
from app.services.robot_understanding_v1.sources import collect_source_pack
from app.services.vendor_robot_lookup import (
    index_robot_names,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
    select_index_robot,
)


def _challenge_page(url: str) -> FetchedPage:
    return FetchedPage(
        url=url,
        final_url=url,
        status_code=429,
        title="Vercel Security Checkpoint",
        text="",
        html="",
        links=[],
        fetch_degraded=True,
        fetch_notes=["Bot challenge from manufacturer host (HTTP 429)"],
    )


def test_richtech_is_in_the_commercial_vendor_index():
    reload_vendor_robots_index()
    hit = lookup_vendor_by_url("https://www.richtechrobotics.com/")
    assert hit is not None
    names = index_robot_names(hit)
    assert "ADAM" in names
    assert "MATRADEE" in names
    assert "Scorpion" in names
    assert select_index_robot("https://www.richtechrobotics.com/", hit) is None
    adam = select_index_robot("https://www.richtechrobotics.com/adam", hit)
    assert adam is not None
    assert adam["name"] == "ADAM"


def test_challenged_homepage_does_not_fan_out_source_fetches():
    home = _challenge_page("https://www.richtechrobotics.com/")
    pack = collect_source_pack(home, product_name="ADAM", max_sources=6)
    assert pack == []


def test_richtech_homepage_is_a_fast_picker_when_live_host_challenges(monkeypatch):
    import app.services.robot_understanding_v1.pipeline as P

    calls: list[dict] = []

    def fake_fetch(url, timeout=(2.5, 6.0), allow_archive=True):
        calls.append({"url": url, "allow_archive": allow_archive})
        return _challenge_page(url)

    def boom(*_a, **_k):
        raise AssertionError("must not crawl product pages on a challenged catalog host")

    monkeypatch.setattr(
        P,
        "fetch_page",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("indexed OEM homepage must not fetch the live host")
        ),
    )
    monkeypatch.setattr(P, "collect_source_pack", boom)
    t0 = time.perf_counter()
    profile = P.build_robot_profile("https://www.richtechrobotics.com/")
    assert time.perf_counter() - t0 < 2.0
    assert profile.needs_product_choice
    names = {p.name for p in profile.products}
    assert "ADAM" in names
    assert "MATRADEE" in names
    assert len(profile.products) > 3
    assert calls == []


def test_richtech_adam_uses_catalog_when_live_pages_are_blocked(monkeypatch):
    import app.services.robot_understanding_v1.pipeline as P

    def boom(*_a, **_k):
        raise AssertionError("catalog SKU must not crawl when the live host is blocked")

    monkeypatch.setattr(
        P,
        "fetch_page",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("indexed SKU must not fetch the live OEM host")
        ),
    )
    monkeypatch.setattr(P, "collect_source_pack", boom)
    profile = P.build_robot_profile(
        "https://www.richtechrobotics.com/adam",
        product_name="ADAM",
    )
    assert profile.needs_product_choice is False
    assert profile.selected_product is not None
    assert profile.selected_product.name == "ADAM"
    confirmed = {
        f.predicate: f.value
        for f in profile.facts
        if f.epistemic not in {"unknown", "contradicted"}
    }
    assert confirmed.get("product_class") == "service_robot"
    assert profile.coverage_level in {"medium", "high"}
    assert any("vendor index" in n.lower() for n in profile.notes)
