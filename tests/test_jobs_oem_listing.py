"""FIND lists named robots per OEM URL — names, then descriptions, then specs.

FIND surfaces three robots at a time. Catalogs are not capped at 3.
"""
from __future__ import annotations

from app.services.jobs_oem_listing import (
    FIND_PRODUCT_LIST_CAP,
    listing_from_catalog,
    listing_from_page,
    listing_payload_for_url,
    split_primary_robots,
)
from app.services.vendor_robot_lookup import (
    index_robot_names,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
)


def test_split_primary_robots_expands_families():
    assert split_primary_robots("MiR250/600/1350", "MiR") == [
        "MiR250",
        "MiR600",
        "MiR1350",
    ]
    assert split_primary_robots("OTTO 100/750/1500", "OTTO Motors") == [
        "OTTO 100",
        "OTTO 750",
        "OTTO 1500",
    ]
    assert split_primary_robots("Locus Origin/Vector", "Locus Robotics") == [
        "Locus Origin",
        "Locus Vector",
    ]
    assert split_primary_robots("AGV/AMR", "Daifuku") == []
    assert len(split_primary_robots("A/B/C/D", "Acme")) == 4


def test_jobs_seed_url_lists_top_three_named_robots():
    reload_vendor_robots_index()
    mir = lookup_vendor_by_url("https://www.mobile-industrial-robots.com/")
    assert mir is not None
    assert index_robot_names(mir)[:3] == ["MiR250", "MiR600", "MiR1350"]

    otto = lookup_vendor_by_url("https://ottomotors.com/")
    assert otto is not None
    assert "OTTO 100" in index_robot_names(otto)

    hai = lookup_vendor_by_url("https://www.hairobotics.com/")
    assert hai is not None
    assert "HAIPICK" in index_robot_names(hai)


def test_jobs_seed_homepage_skips_fetch_and_caps_picker(monkeypatch):
    import app.services.robot_understanding_v1.pipeline as P

    monkeypatch.setattr(
        P,
        "fetch_page",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("jobs-seed OEM must not wait on the live host")
        ),
    )
    monkeypatch.setattr(
        P,
        "collect_source_pack",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("jobs-seed OEM must not crawl SKUs")
        ),
    )
    timings: dict = {}
    profile = P.build_robot_profile(
        "https://www.mobile-industrial-robots.com/", timings=timings
    )
    assert timings.get("home_fetch") == "skipped"
    assert profile.needs_product_choice is True
    names = [p.name for p in profile.products]
    assert names == ["MiR250", "MiR600", "MiR1350"]
    assert all(p.description for p in profile.products)


def test_page_parse_is_name_then_description_then_specs():
    text = (
        "The OTTO 100 is a compact indoor AMR for cart transport. "
        "Payload 100 kg. Runtime 4 hours on a charge. "
        "OTTO 750 moves pallets in factories. Payload 750 kg."
    )
    rows = listing_from_page(["OTTO 100", "OTTO 750"], text)
    assert rows[0]["name"] == "OTTO 100"
    assert rows[0]["description"]
    assert "compact indoor AMR" in (rows[0]["description"] or "")
    assert rows[0]["specs"]["payload_kg"] == 100
    assert rows[0]["specs"]["battery_life_h"] == 4
    assert rows[1]["specs"]["payload_kg"] == 750


def test_unknown_oem_discover_keeps_homepage_names(monkeypatch):
    import app.services.robot_understanding_v1.pipeline as P
    from app.services.robot_understanding_v1.fetch import FetchedPage

    page_text = (
        "Digit is a bipedal robot for totes in warehouses. Digit lifts totes. "
        "Vega is a warehouse AMR for mixed SKUs. Vega moves mixed SKUs. "
        "Atlas walks through industrial sites. Atlas is a humanoid robot. "
        "Apollo is a humanoid for factory work. Apollo works in factories. "
        "Neo is a home robot for indoor tasks. Neo does indoor tasks."
    )

    def fake_fetch(url, timeout=(2.5, 6.0), allow_archive=True):
        return FetchedPage(
            url=url,
            final_url=url,
            status_code=200,
            title="Acme Robotics",
            text=page_text,
            html=f"<html><body>{page_text}</body></html>",
            links=[],
        )

    monkeypatch.setattr(P, "fetch_page", fake_fetch)
    monkeypatch.setattr(P, "collect_source_pack", lambda *_a, **_k: [])
    profile = P.build_robot_profile("https://unknown-bots.example/")
    names = {p.name for p in profile.products}
    assert {"Digit", "Vega", "Atlas", "Apollo", "Neo"} <= names
    assert len(names) >= 5


def test_research_names_are_not_invented_products():
    assert split_primary_robots("research humanoid", "ByteDance") == []
    assert split_primary_robots("research", "Huawei") == []


def test_retail_homepages_are_not_oem_listings():
    reload_vendor_robots_index()
    assert lookup_vendor_by_url("https://www.amazon.com/") is None
    assert lookup_vendor_by_url("https://www.walmart.com/") is None
    assert lookup_vendor_by_url("https://www.mi.com/") is None


def test_yaskawa_and_abb_aliases_list_named_robots():
    reload_vendor_robots_index()
    abb = lookup_vendor_by_url("https://www.abb.com/")
    assert abb is not None
    assert index_robot_names(abb)
    yaskawa = lookup_vendor_by_url("https://www.yaskawa.com/")
    assert yaskawa is not None
    names = index_robot_names(yaskawa)
    assert any("GP" in n or "HC" in n for n in names)


def test_listing_from_catalog_is_name_then_description():
    reload_vendor_robots_index()
    mir = lookup_vendor_by_url("https://www.mobile-industrial-robots.com/")
    rows = listing_from_catalog(mir)
    assert [r["name"] for r in rows][:3]
    assert all(r.get("description") for r in rows)
    assert [r["name"] for r in rows] == index_robot_names(mir)


def test_catalog_lineup_is_not_capped_at_three():
    reload_vendor_robots_index()
    richtech = lookup_vendor_by_url("https://www.richtechrobotics.com/")
    names = index_robot_names(richtech)
    assert len(names) > FIND_PRODUCT_LIST_CAP
    rows = listing_from_catalog(richtech)
    assert [r["name"] for r in rows] == names
    page = listing_from_catalog(richtech, limit=FIND_PRODUCT_LIST_CAP)
    assert [r["name"] for r in page] == names[:FIND_PRODUCT_LIST_CAP]


def test_listing_payload_matches_bare_reflex_host():
    reload_vendor_robots_index()
    payload = listing_payload_for_url("reflexrobotics.com")
    assert payload["matched"] is True
    names = [r["name"] for r in payload["robots"]]
    assert any("Gen2" in n or "Gen 2" in n for n in names)
    assert any("Humanoid" in n for n in names)
    assert names
    assert payload["robots"][0]["description"]  # specs folded into blurb when present


def test_oem_listing_http_does_not_resolve_dns(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    import app.services.robot_url_safety as S

    def boom(*_a, **_k):
        raise AssertionError("oem-listing must not wait on DNS")

    monkeypatch.setattr(S, "assert_public_http_url", boom)
    monkeypatch.setattr(S, "_system_resolve_ips", boom)
    client = TestClient(app)
    res = client.get("/api/oem-listing", params={"url": "reflexrobotics.com"})
    assert res.status_code == 200
    body = res.json()
    assert body["matched"] is True
    assert body["robots"]
