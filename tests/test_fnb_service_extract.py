"""F&B serving/cleaning extraction: named SKUs, not chrome, not a host allowlist.

Pudu-class pages (BellaBot waiter + CC1 scrubber) must yield a named lineup
with per-product classes. Chrome (/en, about, news) is never a SKU.
"""
from __future__ import annotations

from app.services.jobs_oem_listing import listing_from_catalog
from app.services.oem_sku_discover import (
    classify_href_candidate,
    is_site_chrome_name,
    is_site_chrome_slug,
    name_is_proven_product,
)
from app.services.robot_class_qualify import prefer_work_language_class
from app.services.robot_understanding_v1.fetch import FetchedPage
from app.services.robot_understanding_v1.resolve import (
    _discover_product_names,
    _sku_from_product_href,
    resolve_identity,
)
from app.services.vendor_robot_lookup import lookup_vendor_by_url


def _page(*, title: str, text: str, url: str, links: list[tuple[str, str]], html: str = "") -> FetchedPage:
    body = html or f"<html><title>{title}</title><body>{text}</body></html>"
    return FetchedPage(
        url=url,
        final_url=url,
        status_code=200,
        title=title,
        text=text,
        html=body,
        links=links,
    )


def test_locale_about_news_are_chrome_not_skus():
    for slug in ("en", "about", "news", "zh", "zh-cn"):
        assert is_site_chrome_slug(slug), slug
        assert _sku_from_product_href(f"https://oem.example/{slug}") is None
        assert classify_href_candidate(f"https://oem.example/{slug}", slug) == "chrome"
    assert is_site_chrome_name("About")
    assert is_site_chrome_name("News")
    assert not is_site_chrome_name("BellaBot")
    assert not is_site_chrome_name("CC1")


def test_fixture_html_names_serving_and_cleaning_bots():
    """Generic host — not pudurobotics.com — so this is evidence, not an allowlist."""
    origin = "https://fnb-oem.example"
    text = (
        "Meet BellaBot the restaurant delivery robot for table service and "
        "food running. Bussing station waitstaff. Dining room tray delivery "
        "and dish return. "
        "Meet CC1 the cleaning robot. Vacuuming, scrubbing, mopping on "
        "commercial floors. Janitor and custodian work in public venues."
    )
    html = (
        "<html><body>"
        "Meet BellaBot™ restaurant delivery robot for table service. "
        "Meet CC1 cleaning robot. Vacuuming, scrubbing, mopping."
        '<a href="/en">en</a><a href="/about">About</a><a href="/news">News</a>'
        '<a href="/products/bellabot">BellaBot</a>'
        '<a href="/products/cc1">CC1</a>'
        "</body></html>"
    )
    home = _page(
        title="Acme F&B Robotics",
        url=f"{origin}/",
        text=text,
        links=[
            (f"{origin}/en", "en"),
            (f"{origin}/about", "About"),
            (f"{origin}/news", "News"),
            (f"{origin}/products/bellabot", "BellaBot"),
            (f"{origin}/products/cc1", "CC1"),
        ],
        html=html,
    )
    names = _discover_product_names(home)
    lowered = {n.lower() for n in names}
    for noise in ("en", "about", "news"):
        assert noise not in lowered
    assert any("bellabot" in n.lower() for n in names)
    assert any(n.upper() == "CC1" or n.lower() == "cc1" for n in names)
    assert name_is_proven_product("BellaBot", text=text, html=html)
    assert name_is_proven_product("CC1", text=text, html=html)
    assert lookup_vendor_by_url(f"{origin}/") is None

    resolved = resolve_identity(f"{origin}/", home)
    by_class = {p.name: (p.display_class or "") for p in resolved.products}
    serving = [n for n, c in by_class.items() if c == "serving"]
    cleaning = [n for n, c in by_class.items() if c == "cleaning"]
    assert serving, by_class
    assert cleaning, by_class
    assert any("bella" in n.lower() for n in serving)
    assert any(n.upper() == "CC1" or "cc1" in n.lower() for n in cleaning)
    assert set(serving) & set(cleaning) == set()
    assert resolved.products, "named lineup, not empty qualify_robot"


def test_serving_blurb_is_not_cleaning_blurb():
    waiter = (
        "BellaBot tray delivery restaurant waiter. Table service and food running. "
        "Dining room bussing. Restaurants."
    )
    scrubber = (
        "CC1 vacuuming, scrubbing, mopping. Commercial floors. "
        "Floor cleaning janitor in public venues."
    )
    assert prefer_work_language_class(waiter, "service_robot") == "serving"
    assert prefer_work_language_class(scrubber, "service_robot") == "cleaning"
    assert prefer_work_language_class(waiter) != prefer_work_language_class(scrubber)


def test_pudu_vendor_index_lineup_is_named_and_split():
    """Catalog descriptions reclassify generic service_robot per product."""
    vendor = lookup_vendor_by_url("https://www.pudurobotics.com/en")
    assert vendor is not None
    rows = listing_from_catalog(vendor)
    names = {r["name"] for r in rows}
    assert "BellaBot" in names
    assert "CC1" in names
    assert "en" not in {n.lower() for n in names}
    assert "About" not in names
    by = {r["name"]: r.get("display_class") for r in rows}
    assert by["BellaBot"] == "serving"
    assert by["CC1"] == "cleaning"
    assert by["BellaBot"] != by["CC1"]
    assert by["BellaBot"] != "service_robot"
    assert len(rows) >= 2


def test_peer_oem_lineups_classify_without_host_allowlist():
    """Keenon / Bear pages — same rules as Pudu, not a pudurobotics.com allowlist."""
    bear = lookup_vendor_by_url("https://www.bearrobotics.ai")
    assert bear is not None
    bear_by = {r["name"]: r.get("display_class") for r in listing_from_catalog(bear)}
    assert bear_by.get("Servi") == "serving", bear_by
    assert bear_by.get("Servi Plus") == "serving", bear_by

    keenon = lookup_vendor_by_url("https://keenon.com") or lookup_vendor_by_url(
        "https://www.keenon.com"
    )
    assert keenon is not None
    keen_by = {r["name"]: r.get("display_class") for r in listing_from_catalog(keenon)}
    assert keen_by.get("Dinerbot T5") == "serving", keen_by
    assert keen_by.get("Keenon C30") == "cleaning", keen_by
    butler = keen_by.get("Butlerbot W3")
    if butler:
        assert butler == "hospitality", keen_by
