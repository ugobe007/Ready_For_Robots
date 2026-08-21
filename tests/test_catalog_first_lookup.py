"""Catalog-first URL lookup applies to every indexed OEM, not only Richtech."""
from __future__ import annotations

from app.services.robot_understanding_v1.fetch import FetchedPage
from app.services.vendor_robot_lookup import (
    catalog_claim_facts,
    index_robot_names,
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

    def fake_fetch(url, timeout=(2.5, 6.0), allow_archive=True):
        assert allow_archive is False
        return _page(url, text="Unitree G1 humanoid")

    def boom(*_a, **_k):
        raise AssertionError("indexed vendors must not fan out a live source pack")

    monkeypatch.setattr(P, "fetch_page", fake_fetch)
    monkeypatch.setattr(P, "collect_source_pack", boom)
    timings: dict = {}
    profile = P.build_robot_profile(
        "https://www.unitree.com/g1",
        product_name="Unitree G1",
        timings=timings,
    )
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

    monkeypatch.setattr(P, "fetch_page", lambda *a, **k: _page(a[0], text=""))
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
