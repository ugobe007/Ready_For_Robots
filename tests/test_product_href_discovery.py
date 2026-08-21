"""Discover robot SKUs from manufacturer product URLs (not an OEM allowlist)."""
from __future__ import annotations

from app.services.robot_understanding_v1.fetch import FetchedPage
from app.services.robot_understanding_v1.resolve import (
    _discover_product_names,
    _sku_from_product_href,
    resolve_identity,
)
from app.services.robot_profile_cache import NAMESPACE


def _page(*, title: str, text: str, url: str, links: list[tuple[str, str]]) -> FetchedPage:
    return FetchedPage(
        url=url,
        final_url=url,
        status_code=200,
        title=title,
        text=text,
        html=f"<html><title>{title}</title><body>{text}</body></html>",
        links=links,
    )


def test_sku_from_engineai_product_paths():
    assert _sku_from_product_href("https://en.engineai.com.cn/product-pm01.html") == "PM01"
    assert _sku_from_product_href("https://en.engineai.com.cn/product-t800") == "T800"
    assert _sku_from_product_href("https://en.engineai.com.cn/product-s2.html") == "S2"
    assert _sku_from_product_href("https://en.engineai.com.cn/product-purchase.html") is None
    assert _sku_from_product_href("https://en.engineai.com.cn/about.html") is None


def test_engineai_homepage_links_yield_product_picker():
    origin = "https://en.engineai.com.cn"
    home = _page(
        title="ENGINEAI",
        url=f"{origin}/",
        text=(
            "ENGINEAI Products PM01 T800 JS01 SA01 SE01 S2 "
            "PM01 A lightweight embodied intelligent agent. "
            "SE01 general-purpose humanoid robot. "
            "T800 Full-Scale High-Mobility General-Purpose Robot."
        ),
        links=[
            (f"{origin}/product-pm01.html", "PM01"),
            (f"{origin}/product-t800.html", "T800"),
            (f"{origin}/product-js01.html", "JS01"),
            (f"{origin}/product-sa01.html", "SA01"),
            (f"{origin}/product-se01.html", "SE01"),
            (f"{origin}/product-s2.html", "S2"),
            (f"{origin}/product-purchase.html", "Product Purchase"),
        ],
    )
    names = _discover_product_names(home)
    assert "PM01" in names
    assert "T800" in names
    assert "SE01" in names
    assert "Purchase" not in names
    assert "Product Purchase" not in names
    resolved = resolve_identity(f"{origin}/", home)
    assert resolved.company.primary_domain == "engineai.com.cn"
    assert resolved.company.name.upper() == "ENGINEAI"
    found = {p.name for p in resolved.products}
    assert {"PM01", "T800", "SE01"} <= found
    assert len(resolved.products) >= 3


def test_allowlist_digit_still_discovered_without_product_href():
    home = _page(
        title="Digit | Agility Robotics",
        url="https://www.agilityrobotics.com/",
        text="Digit humanoid robot Digit warehouses Digit totes Digit.",
        links=[
            ("https://www.agilityrobotics.com/robots/digit", "Digit"),
        ],
    )
    names = _discover_product_names(home)
    assert "Digit" in names


def test_profile_cache_namespace_busts_stale_engineai_identity():
    assert NAMESPACE == "robot_profile_v3"
