"""FIND `/` SKU URLs match configuration work-kind, not the parent FIND tile.

Production used to POST lookup_grain=robot_type with the agriculture /
construction tile whenever configurationClassForLookup hit. Carbon LaserWeeder
then got combine+spray+tractor. A named SKU is not a tile.
"""
from __future__ import annotations

from app.services.robot_capability_derive import derive_capabilities
from app.services.robot_class_qualify import (
    FIND_TILE_CLASSES,
    apply_asserted_class,
    lookup_class_id,
    normalize_class_id,
    thin_class_profile,
)
from app.services.robot_job_search import compose_robot_job_search
from app.services.robot_profile_cache import clear_profile_cache_memory
from app.services.vendor_robot_lookup import (
    index_robot_names,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
)


PAD_TITLE_BITS = ("cnc", "tote", "warehouse", "pack station")
COMBINE = "harvest grain with an autonomous combine"
BLOCK_LAY = "lay block for a commercial building"
PLANT_GAUGE = "inspect plant gauges"
WEED = "weed"


def _titles(out: dict) -> list[str]:
    return [str(j.get("title") or "") for j in out.get("jobs") or []]


def _blob(out: dict) -> str:
    parts = []
    for j in out.get("jobs") or []:
        parts.append(str(j.get("title") or ""))
        parts.append(str(j.get("company_name") or ""))
        parts.append(str(j.get("tape_family") or ""))
    return " ".join(parts).lower()


def _skip_crawl(monkeypatch) -> None:
    import app.services.robot_understanding_v1.pipeline as P

    def boom(*_a, **_k):
        raise AssertionError("indexed vendor must not crawl")

    monkeypatch.setattr(P, "fetch_page", boom)
    monkeypatch.setattr(P, "collect_source_pack", boom)
    clear_profile_cache_memory()


def test_lookup_class_keeps_sku_classes_off_parent_tiles():
    assert normalize_class_id("agricultural_robot") == "agriculture"
    assert normalize_class_id("construction_robot") == "construction"
    assert lookup_class_id("agricultural_robot") == "agricultural_robot"
    assert lookup_class_id("farm_robot") == "agricultural_robot"
    assert lookup_class_id("construction_robot") == "construction_robot"
    assert lookup_class_id("agriculture") == "agriculture"
    assert lookup_class_id("construction") == "construction"
    assert lookup_class_id("evtol") == "evtol"
    assert lookup_class_id("drone") == "drone"
    assert "agriculture" in FIND_TILE_CLASSES
    assert "construction" in FIND_TILE_CLASSES
    assert lookup_class_id("agricultural_robot") not in FIND_TILE_CLASSES
    assert lookup_class_id("construction_robot") not in FIND_TILE_CLASSES


def test_asserted_agricultural_robot_is_not_the_ag_union():
    profile = apply_asserted_class(
        {
            "company": {"name": "Carbon Robotics"},
            "selected_product": {"name": "LaserWeeder"},
            "facts": [],
        },
        "agricultural_robot",
    )
    classes = {
        str(f.get("value")).lower()
        for f in profile["facts"]
        if f.get("predicate") == "product_class"
    }
    assert "agricultural_robot" in classes
    assert "agriculture" not in classes
    caps = derive_capabilities(profile)
    assert caps["agriculture_weed"].present is False
    assert caps["agriculture_combine"].present is False
    blob = _blob(match_jobs_from_profile(profile))
    assert COMBINE not in blob


def test_thin_agriculture_tile_still_union():
    profile = thin_class_profile("Unknown farm OEM", "agriculture")
    caps = derive_capabilities(profile)
    assert caps["agriculture_weed"].present is True
    assert caps["agriculture_combine"].present is True
    blob = _blob(match_jobs_from_profile(profile))
    assert "weed" in blob
    assert "combine" in blob


def test_carbon_find_type_first_payload_is_weeding_not_combine_or_cnc(monkeypatch):
    """Payload `/` actually sends: product + asserted class + robot_type."""
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search(
        "https://carbonrobotics.com/",
        product="LaserWeeder",
        asserted_class="agriculture",
        lookup_grain="robot_type",
    )
    blob = _blob(out)
    assert out["state"] == "matches"
    assert WEED in blob
    assert COMBINE not in blob
    for bit in PAD_TITLE_BITS:
        assert bit not in blob, blob
    assert lookup_class_id(out.get("robot_class")) != "agriculture" or (
        "weed" in blob and COMBINE not in blob
    )


def test_carbon_find_sku_class_payload_is_weeding_not_combine(monkeypatch):
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search(
        "https://carbonrobotics.com/",
        product="LaserWeeder",
        asserted_class="agricultural_robot",
        lookup_grain="product",
    )
    blob = _blob(out)
    assert WEED in blob
    assert COMBINE not in blob
    for bit in PAD_TITLE_BITS:
        assert bit not in blob, blob


def test_icon_find_type_first_is_print_not_block_lay(monkeypatch):
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search(
        "https://www.iconbuild.com/",
        product="Vulcan",
        asserted_class="construction",
        lookup_grain="robot_type",
    )
    blob = _blob(out)
    assert "3d-print" in blob or "3d print" in blob
    assert BLOCK_LAY not in blob
    for bit in PAD_TITLE_BITS:
        assert bit not in blob, blob


def test_dusty_find_type_first_is_layout_not_block_or_print(monkeypatch):
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search(
        "https://dustyrobotics.com/",
        product="FieldPrinter",
        asserted_class="construction",
        lookup_grain="robot_type",
    )
    blob = _blob(out)
    assert "layout" in blob
    assert BLOCK_LAY not in blob
    assert "3d-print walls" not in blob


def test_hadrian_find_type_first_is_block_not_print(monkeypatch):
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search(
        "https://www.fbr.com.au/",
        product="Hadrian X",
        asserted_class="construction",
        lookup_grain="robot_type",
    )
    blob = _blob(out)
    assert "block" in blob
    assert "3d-print" not in blob and "3d print" not in blob


def test_claas_combine_find_is_harvest_not_weed(monkeypatch):
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search(
        "https://claas.com/en-us/products/combines/lexion-8000-7000",
        product="LEXION 8000-7000",
        asserted_class="agriculture",
        lookup_grain="robot_type",
    )
    blob = _blob(out)
    assert "harvest" in blob or "combine" in blob
    assert "weed vegetable" not in blob


def test_deere_combine_find_is_harvest_not_weed(monkeypatch):
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search(
        "https://www.deere.com/en/harvesting/x-series-combines/",
        product="X Series Combine",
        asserted_class="agriculture",
        lookup_grain="robot_type",
    )
    blob = _blob(out)
    assert "harvest" in blob or "combine" in blob
    assert "weed vegetable" not in blob


def test_skydio_find_type_first_is_drone_not_quadruped_plant_gauge(monkeypatch):
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search(
        "https://www.skydio.com/",
        product="Skydio X10",
        asserted_class="quadruped",
        lookup_grain="robot_type",
    )
    blob = _blob(out)
    assert PLANT_GAUGE not in blob
    assert "quadruped" not in (out.get("robot_class") or "").lower()
    assert (
        "drone" in blob
        or "airframe" in blob
        or "inspect" in blob
        or (out.get("robot_class") or "").lower() in {"drone", "uav"}
    )


def test_deere_vendor_index_lists_combine_tractor_and_spray():
    reload_vendor_robots_index()
    vendor = lookup_vendor_by_url("https://deere.com/")
    assert vendor is not None
    names = index_robot_names(vendor)
    blob = " ".join(names).lower()
    assert "combine" in blob
    assert "tractor" in blob
    assert "spray" in blob
