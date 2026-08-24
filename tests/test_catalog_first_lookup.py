"""Catalog-first URL lookup applies to every indexed OEM, not only Richtech."""
from __future__ import annotations

from app.services.robot_understanding_v1.fetch import FetchedPage
from app.services.vendor_robot_lookup import (
    catalog_claim_facts,
    index_robot_names,
    load_vendor_robots_index,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
    select_index_robot,
)


def _page(url: str, *, text: str = "Manufacturer homepage", status: int = 200) -> FetchedPage:
    degraded = status >= 400 or not text.strip()
    return FetchedPage(
        url=url,
        final_url=url,
        status_code=status,
        title="Vendor",
        text=text,
        html=f"<html><body>{text}</body></html>",
        links=[],
        fetch_degraded=degraded,
        fetch_notes=["challenge"] if degraded and not text.strip() else [],
    )


def test_commercial_seed_covers_jobs_oem_homepages():
    reload_vendor_robots_index()
    bear = lookup_vendor_by_url("https://www.bearrobotics.ai/")
    assert bear is not None
    assert "Servi" in index_robot_names(bear)
    assert select_index_robot("https://www.bearrobotics.ai/servi", bear)["name"] == "Servi"

    pudu = lookup_vendor_by_url("https://www.pudurobotics.com/")
    assert pudu is not None
    assert "BellaBot" in index_robot_names(pudu)

    locus = lookup_vendor_by_url("https://www.locusrobotics.com/")
    assert locus is not None
    assert "Locus Origin" in index_robot_names(locus)

    bd = lookup_vendor_by_url("https://bostondynamics.com/")
    assert bd is not None
    names = index_robot_names(bd)
    assert any("Atlas" in n for n in names)
    assert "Spot" in names
    assert "Stretch" in names


def test_index_specs_fill_checklist_predicates():
    facts = catalog_claim_facts(
        {
            "name": "Unitree G1",
            "primary_class": "humanoid",
            "specs": {"payload_kg": 3.0, "battery_life_h": 1.75, "height_cm": 127},
        }
    )
    by_pred = {f["predicate"]: f["value"] for f in facts}
    assert by_pred["product_class"] == "humanoid"
    assert by_pred["carrying_capacity"] == 3.0
    assert by_pred["battery_runtime"] == 1.75
    assert by_pred["reach_or_workspace"] == 127


def test_indexed_sku_skips_live_source_pack(monkeypatch):
    import app.services.robot_understanding_v1.pipeline as P

    def boom_fetch(*_a, **_k):
        raise AssertionError("indexed vendors must not fetch the live OEM page")

    def boom(*_a, **_k):
        raise AssertionError("indexed vendors must not fan out a live source pack")

    monkeypatch.setattr(P, "fetch_page", boom_fetch)
    monkeypatch.setattr(P, "collect_source_pack", boom)
    timings: dict = {}
    profile = P.build_robot_profile(
        "https://www.unitree.com/g1",
        product_name="Unitree G1",
        timings=timings,
    )
    assert timings.get("home_fetch") == "skipped"
    assert timings.get("source_strategy") == "catalog"
    assert profile.needs_product_choice is False
    assert profile.selected_product is not None
    assert "G1" in profile.selected_product.name
    confirmed = {
        f.predicate: f.value
        for f in profile.facts
        if f.epistemic not in {"unknown", "contradicted"}
    }
    assert confirmed.get("product_class") == "humanoid"
    assert confirmed.get("carrying_capacity") == 3.0
    assert profile.coverage_level in {"medium", "high"}


def test_bear_servi_uses_catalog_without_source_pack(monkeypatch):
    import app.services.robot_understanding_v1.pipeline as P

    monkeypatch.setattr(
        P,
        "fetch_page",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("indexed SKUs must not wait on the live OEM host")
        ),
    )
    monkeypatch.setattr(
        P,
        "collect_source_pack",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("catalog commercial SKUs must not crawl")
        ),
    )
    profile = P.build_robot_profile(
        "https://www.bearrobotics.ai/servi",
        product_name="Servi",
    )
    assert profile.selected_product is not None
    assert profile.selected_product.name == "Servi"
    confirmed = {
        f.predicate: f.value
        for f in profile.facts
        if f.epistemic not in {"unknown", "contradicted"}
    }
    assert confirmed.get("product_class") == "service_robot"
    assert confirmed.get("carrying_capacity") == 30.0


def test_unknown_oem_still_uses_live_pack_without_archive(monkeypatch):
    import app.services.robot_understanding_v1.pipeline as P

    pack_calls: list[dict] = []

    def fake_fetch(url, timeout=(2.5, 6.0), allow_archive=True):
        return _page(url, text="Acme cobot arm for machine tending")

    def fake_pack(home, **kwargs):
        pack_calls.append(kwargs)
        return []

    monkeypatch.setattr(P, "fetch_page", fake_fetch)
    monkeypatch.setattr(P, "collect_source_pack", fake_pack)
    timings: dict = {}
    P.build_robot_profile("https://unknown-oem.example/", timings=timings)
    assert timings.get("source_strategy") == "live_pack"
    assert pack_calls
    assert pack_calls[0].get("allow_archive") is False

def test_reflex_homepage_is_in_vendor_index():
    reload_vendor_robots_index()
    hit = lookup_vendor_by_url("https://www.reflexrobotics.com/")
    assert hit is not None
    names = index_robot_names(hit)
    assert any("Gen2" in n or "Gen 2" in n for n in names)
    assert any("Humanoid" in n for n in names)
    assert select_index_robot("https://www.reflexrobotics.com/", hit) is None
    assert select_index_robot("https://www.reflexrobotics.com", hit) is None


def test_reflex_homepage_opens_picker_without_live_fetch(monkeypatch):
    import time
    import app.services.robot_understanding_v1.pipeline as P

    def boom_fetch(*_a, **_k):
        raise AssertionError("Reflex homepage must not wait on reflexrobotics.com")

    def boom_pack(*_a, **_k):
        raise AssertionError("catalog homepage must not crawl product pages")

    monkeypatch.setattr(P, "fetch_page", boom_fetch)
    monkeypatch.setattr(P, "collect_source_pack", boom_pack)
    timings: dict = {}
    t0 = time.perf_counter()
    profile = P.build_robot_profile("https://www.reflexrobotics.com/", timings=timings)
    assert time.perf_counter() - t0 < 1.0
    assert timings.get("home_fetch") == "skipped"
    assert timings.get("source_strategy") == "catalog"
    assert profile.needs_product_choice is True
    names = {p.name for p in profile.products}
    assert any("Gen2" in n or "Gen 2" in n for n in names)
    assert any("Humanoid" in n for n in names)
    assert profile.company.name == "Reflex Robotics"


def test_every_indexed_vendor_homepage_skips_live_fetch(monkeypatch):
    """Reflex is not special — any indexed OEM homepage must skip live I/O."""
    import app.services.robot_understanding_v1.pipeline as P

    def boom_fetch(*_a, **_k):
        raise AssertionError("indexed vendor homepages must not fetch the live OEM host")

    def boom_pack(*_a, **_k):
        raise AssertionError("indexed vendor homepages must not crawl product pages")

    monkeypatch.setattr(P, "fetch_page", boom_fetch)
    monkeypatch.setattr(P, "collect_source_pack", boom_pack)
    reload_vendor_robots_index()
    indexed = [
        v
        for v in (load_vendor_robots_index().get("vendors") or [])
        if v.get("robots")
        and lookup_vendor_by_url(
            (v.get("vendor_url") or "").strip()
            or (f"https://{(v.get('domains') or ['x'])[0]}/")
        )
    ]
    assert len(indexed) >= 50
    prefer = []
    rest = []
    for vendor in indexed:
        label = (vendor.get("vendor_name") or "").lower()
        if any(token in label for token in ("reflex", "richtech", "mir (", "otto motors")):
            prefer.append(vendor)
        else:
            rest.append(vendor)
    checked = 0
    homepage_sku_vendors = 0
    for vendor in (prefer + rest)[:45]:
        robots = vendor.get("robots") or []
        url = (vendor.get("vendor_url") or "").strip()
        domains = vendor.get("domains") or []
        if not url and domains:
            url = f"https://{domains[0]}/"
        timings: dict = {}
        profile = P.build_robot_profile(url, timings=timings)
        assert timings.get("home_fetch") == "skipped", vendor.get("vendor_name")
        assert profile.products, vendor.get("vendor_name")
        assert len(profile.products) <= 3, vendor.get("vendor_name")
        checked += 1
        if len(robots) > 1 and profile.needs_product_choice:
            homepage_sku_vendors += 1
    assert checked >= 40
    assert homepage_sku_vendors >= 8


def test_unknown_oem_home_fetch_shares_find_deadline(monkeypatch):
    """Unknown hosts may crawl, but homepage + pack share one budget under 22s."""
    import time
    import app.services.robot_understanding_v1.pipeline as P

    seen: dict = {}

    def fake_fetch(url, timeout=(2.5, 6.0), allow_archive=True):
        seen["timeout"] = timeout
        seen["allow_archive"] = allow_archive
        return _page(url, text="Acme cobot arm for machine tending")

    def fake_pack(home, **kwargs):
        seen["deadline"] = kwargs.get("deadline_monotonic")
        seen["pack_allow_archive"] = kwargs.get("allow_archive")
        return []

    monkeypatch.setattr(P, "fetch_page", fake_fetch)
    monkeypatch.setattr(P, "collect_source_pack", fake_pack)
    t0 = time.monotonic()
    P.build_robot_profile("https://unknown-oem.example/")
    connect, read = seen["timeout"]
    assert seen["allow_archive"] is False
    assert connect + read <= 12.5
    assert seen["pack_allow_archive"] is False
    assert seen["deadline"] is not None
    assert seen["deadline"] - t0 <= 12.5

