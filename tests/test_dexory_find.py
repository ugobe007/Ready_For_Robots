"""Dexory FIND: DexoryView stays unnamed-class. Impact is chrome.

Does not invent a scanner SKU. Catalog skip must not dump service_robot.
"""
from __future__ import annotations

from app.services.jobs_oem_listing import listing_payload_for_url
from app.services.oem_sku_catalog import compile_vendor_seed
from app.services.oem_sku_discover import (
    classify_href_candidate,
    is_site_chrome_name,
    trademark_product_names,
)
from app.services.robot_class_qualify import keep_claimed_display_class
from app.services.robot_profile_cache import clear_profile_cache_memory
from app.services.robot_understanding_v1.fetch import FetchedPage
from app.services.robot_understanding_v1.resolve import (
    _discover_product_names,
    _merge_catalog_names,
)
from app.services.url_workflow_critic import critique_url
from app.services.vendor_robot_lookup import (
    index_robot_for_name,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
)


def setup_function():
    reload_vendor_robots_index()
    clear_profile_cache_memory()


def test_compile_unclassified_sku_does_not_dump_service_robot():
    seed = compile_vendor_seed(
        {
            "companies": [
                {
                    "name": "Dexory",
                    "domains": ["dexory.com"],
                    "products": [
                        {
                            "name": "DexoryView",
                            "slug": "dexory-dexoryview",
                            "primary_class": None,
                            "task": None,
                            "setting": None,
                        }
                    ],
                }
            ]
        }
    )
    robot = seed["vendors"][0]["robots"][0]
    assert robot["primary_class"] in (None, "")
    assert robot.get("catalog_claims") in (None, [])


def test_dexoryview_seed_is_not_a_dump_class():
    vendor = lookup_vendor_by_url("https://dexory.com")
    assert vendor is not None
    robot = index_robot_for_name(vendor, "DexoryView")
    assert robot is not None
    assert (robot.get("primary_class") or "").strip() in ("",)
    claims = robot.get("catalog_claims") or []
    assert not any(
        str((c or {}).get("value") or "").lower() == "service_robot" for c in claims
    )
    listing = listing_payload_for_url("https://dexory.com")
    dby = {r["name"]: r.get("display_class") for r in listing.get("robots") or []}
    assert dby.get("DexoryView") is None
    assert "Impact" not in dby


def test_generic_catalog_claim_is_not_restored_as_display_class():
    assert keep_claimed_display_class(None, "service_robot", name="DexoryView") is None
    assert keep_claimed_display_class("serving", "service_robot", name="BellaBot") == "serving"
    assert keep_claimed_display_class(None, "humanoid", name="N1") == "humanoid"
    waiter = keep_claimed_display_class(
        None,
        "service_robot",
        name="BellaBot",
        description="Tray delivery restaurant waiter. Table service.",
    )
    assert waiter == "serving"


def test_dexory_impact_is_chrome_not_a_sku():
    assert is_site_chrome_name("Impact")
    assert is_site_chrome_name("Total Economic Impact")
    assert classify_href_candidate("https://www.dexory.com/impact", "Impact") == "chrome"
    names = trademark_product_names(
        "Forrester Consulting to conduct a Total Economic Impact™ (TEI) "
        "study on DexoryView, our warehouse intelligence platform."
    )
    assert "Impact" not in names
    page = FetchedPage(
        url="https://www.dexory.com/",
        final_url="https://www.dexory.com/",
        status_code=200,
        title="Dexory",
        text=(
            "Impact About Careers. DexoryView warehouse intelligence. "
            "Our autonomous robots scan the warehouse. Total Economic Impact™."
        ),
        html="",
        links=[
            ("https://www.dexory.com/impact", "Impact"),
            ("https://www.dexory.com/solutions", "DexoryView"),
        ],
    )
    discovered = _discover_product_names(page)
    assert "Impact" not in discovered
    merged = _merge_catalog_names(["DexoryView"], discovered)
    assert merged == ["DexoryView"]


def test_dexory_catalog_profile_skips_crawl_and_does_not_dump_class():
    from app.services.robot_understanding_v1 import pipeline as P

    timings: dict = {}
    profile = P.build_robot_profile("https://www.dexory.com/", timings=timings)
    assert timings.get("home_fetch") == "skipped"
    assert timings.get("source_strategy") == "catalog"
    names = [p.name for p in profile.products]
    assert names == ["DexoryView"]
    assert "Impact" not in names
    selected = profile.selected_product
    assert selected is not None
    assert selected.name == "DexoryView"
    assert (selected.display_class or "") not in {
        "service_robot",
        "service",
        "robot",
        "commercial",
    }
    assert selected.display_class in (None, "")
    class_vals = [
        str(f.value).lower()
        for f in profile.facts
        if f.predicate == "product_class" and f.epistemic not in ("unknown", "contradicted")
    ]
    assert "service_robot" not in class_vals


def test_dexory_critic_corpus_forbids_impact():
    critique = critique_url("https://dexory.com")
    names = [p.name for p in critique.products]
    assert "DexoryView" in names
    assert "Impact" not in names
    assert not any(p.display_class == "service_robot" for p in critique.products)
    assert critique.ok, [b.detail for b in critique.breaks]
