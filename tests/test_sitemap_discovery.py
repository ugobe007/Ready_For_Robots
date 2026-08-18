"""Sitemap discovery fallback for thin/JS homepages — deterministic (mocked fetch)."""
from __future__ import annotations

import app.services.robot_understanding_v1.sources as S
from app.services.robot_understanding_v1.fetch import FetchedPage
from app.services.robot_understanding_v1.sources import (
    collect_source_pack,
    discover_from_sitemap,
)

SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://acme-robots.example/</loc></url>
  <url><loc>https://acme-robots.example/products/hauler-x1</loc></url>
  <url><loc>https://acme-robots.example/robots/scout-2</loc></url>
  <url><loc>https://acme-robots.example/about-us</loc></url>
  <url><loc>https://acme-robots.example/careers</loc></url>
  <url><loc>https://other-domain.example/products/leak</loc></url>
</urlset>
"""

SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://acme-robots.example/sitemap-products.xml</loc></sitemap>
</sitemapindex>
"""

CHILD_MAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://acme-robots.example/products/hauler-x1</loc></url>
</urlset>
"""


def _patch_text(monkeypatch, mapping: dict[str, str]) -> None:
    def fake_fetch_text(url, *, timeout=(3.0, 8.0)):
        for frag, body in mapping.items():
            if url.rstrip("/").endswith(frag.rstrip("/")):
                return 200, body
        return 0, ""

    monkeypatch.setattr(S, "fetch_text", fake_fetch_text)


def test_discover_keeps_same_origin_product_paths(monkeypatch):
    _patch_text(monkeypatch, {"/sitemap.xml": SITEMAP_XML})
    urls = [u for u, _ in discover_from_sitemap("https://acme-robots.example")]
    assert "https://acme-robots.example/products/hauler-x1" in urls
    assert "https://acme-robots.example/robots/scout-2" in urls
    # Rejected/non-product/cross-domain dropped
    assert all("about-us" not in u for u in urls)
    assert all("careers" not in u for u in urls)
    assert all("other-domain" not in u for u in urls)


def test_discover_follows_sitemap_index(monkeypatch):
    _patch_text(
        monkeypatch,
        {
            "/sitemap.xml": SITEMAP_INDEX,
            "/sitemap-products.xml": CHILD_MAP,
        },
    )
    urls = [u for u, _ in discover_from_sitemap("https://acme-robots.example")]
    assert urls == ["https://acme-robots.example/products/hauler-x1"]


def test_discover_subject_first(monkeypatch):
    _patch_text(monkeypatch, {"/sitemap.xml": SITEMAP_XML})
    urls = [u for u, _ in discover_from_sitemap("https://acme-robots.example", product_name="Scout 2")]
    assert urls[0] == "https://acme-robots.example/robots/scout-2"


def test_discover_fail_open_on_no_sitemap(monkeypatch):
    _patch_text(monkeypatch, {})  # every fetch returns (0, "")
    assert discover_from_sitemap("https://acme-robots.example") == []


def _thin_home() -> FetchedPage:
    return FetchedPage(
        url="https://acme-robots.example/",
        final_url="https://acme-robots.example/",
        status_code=200,
        title="Acme Robots",
        text="Acme Robots builds autonomous machines. " * 8,
        html="<html><body>Acme Robots</body></html>",
        links=[],  # SPA shell: no discoverable same-domain links
    )


def _rich_home() -> FetchedPage:
    links = [(f"https://acme-robots.example/p/{i}", f"link {i}") for i in range(12)]
    return FetchedPage(
        url="https://acme-robots.example/",
        final_url="https://acme-robots.example/",
        status_code=200,
        title="Acme Robots",
        text="Acme Robots builds autonomous machines. " * 8,
        html="<html></html>",
        links=links,
    )


def test_thin_homepage_triggers_sitemap(monkeypatch):
    _patch_text(monkeypatch, {"/sitemap.xml": SITEMAP_XML})
    called = {"n": 0}
    real = S.discover_from_sitemap

    def spy(origin, *, product_name=None):
        called["n"] += 1
        return real(origin, product_name=product_name)

    monkeypatch.setattr(S, "discover_from_sitemap", spy)
    # Fetch of discovered pages fails (network) → pack may be homepage-only, but
    # the important assertion is that discovery was attempted for a thin homepage.
    monkeypatch.setattr(S, "fetch_page", lambda url, **kw: _thin_home() if url.rstrip("/").endswith("example") else FetchedPage(url, url, 0, None, "", "", [], fetch_degraded=True))
    collect_source_pack(_thin_home(), max_sources=4)
    assert called["n"] == 1


def test_rich_homepage_skips_sitemap(monkeypatch):
    called = {"n": 0}

    def spy(origin, *, product_name=None):
        called["n"] += 1
        return []

    monkeypatch.setattr(S, "discover_from_sitemap", spy)
    monkeypatch.setattr(S, "fetch_page", lambda url, **kw: FetchedPage(url, url, 0, None, "", "", [], fetch_degraded=True))
    collect_source_pack(_rich_home(), max_sources=4)
    assert called["n"] == 0
