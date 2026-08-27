"""eVTOL flying cars must not match Spot-like airside ramp walking.

Archer Midnight / Joby eVTOL are the aircraft on the ramp. Walking the
ramp is inspect work for a quadruped or inspect drone.
"""
from __future__ import annotations

from app.services.robot_capability_derive import derive_capabilities
from app.services.robot_class_qualify import apply_asserted_class
from app.services.robot_requirement_match import match_jobs_from_profile
from app.services.vendor_robot_lookup import (
    catalog_claim_facts,
    index_robot_for_name,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
)

RAMP = "walk the airside ramp"
HANGAR = "inspect an airframe in the hangar"
EVTOL_ROUTE = "fly an evtol route"


def _titles(out: dict) -> list[str]:
    return [str(j.get("title") or "") for j in out.get("jobs") or []]


def _blob(out: dict) -> str:
    return " ".join(_titles(out)).lower()


def _catalog_profile(url: str, product_name: str, company: str) -> dict:
    reload_vendor_robots_index()
    vendor = lookup_vendor_by_url(url)
    assert vendor is not None, url
    robot = index_robot_for_name(vendor, product_name)
    assert robot is not None, product_name
    facts = catalog_claim_facts(robot)
    return {
        "company": {"name": company},
        "selected_product": {
            "name": product_name,
            "display_class": robot.get("primary_class"),
        },
        "facts": facts,
        "coverage_level": "low",
    }


def test_archer_midnight_is_evtol_not_ramp_walker():
    profile = _catalog_profile("https://archer.com/", "Midnight", "Archer")
    caps = derive_capabilities(profile)
    assert caps["evtol_flight"].present is True
    assert caps["drone_task"].present is False
    assert caps["inspect_route"].present is False
    assert caps["avionics_task"].present is True
    out = match_jobs_from_profile(profile)
    blob = _blob(out)
    assert RAMP not in blob
    assert HANGAR not in blob
    assert "autonomous drone" not in blob
    assert "delivery drone" not in blob
    assert EVTOL_ROUTE in blob
    assert out["state"] == "matches"


def test_joby_evtol_does_not_get_airside_ramp():
    profile = _catalog_profile(
        "https://www.jobyaviation.com/", "Joby eVTOL", "Joby Aviation"
    )
    caps = derive_capabilities(profile)
    assert caps["evtol_flight"].present is True
    assert caps["drone_task"].present is False
    blob = _blob(match_jobs_from_profile(profile))
    assert RAMP not in blob
    assert HANGAR not in blob
    assert EVTOL_ROUTE in blob


def test_skydio_inspect_drone_still_gets_airside_or_drone_inspect():
    profile = _catalog_profile("https://www.skydio.com/", "X10", "Skydio")
    caps = derive_capabilities(profile)
    assert caps["drone_task"].present is True
    assert caps["evtol_flight"].present is False
    assert caps["inspect_route"].present is False
    out = match_jobs_from_profile(profile)
    blob = _blob(out)
    assert RAMP in blob or HANGAR in blob or "autonomous drone" in blob
    assert EVTOL_ROUTE not in blob


def test_quadruped_still_gets_airside_ramp_walk():
    profile = apply_asserted_class(
        {
            "company": {"name": "Boston Dynamics"},
            "selected_product": {"name": "Spot"},
            "facts": [],
        },
        "quadruped",
    )
    caps = derive_capabilities(profile)
    assert caps["inspect_route"].present is True
    assert caps["evtol_flight"].present is False
    blob = _blob(match_jobs_from_profile(profile))
    assert RAMP in blob or HANGAR in blob


def test_find_archer_url_skips_crawl_and_drops_ramp(monkeypatch):
    import app.services.robot_understanding_v1.pipeline as P
    from app.services.robot_job_search import compose_robot_job_search
    from app.services.robot_profile_cache import clear_profile_cache_memory

    clear_profile_cache_memory()

    def boom(*_a, **_k):
        raise AssertionError("indexed Archer must not crawl")

    monkeypatch.setattr(P, "fetch_page", boom)
    monkeypatch.setattr(P, "collect_source_pack", boom)
    out = compose_robot_job_search("https://archer.com/")
    assert out["needs_class_choice"] is False
    assert (out.get("robot_class") or "") in {"evtol", "avionics"}
    blob = _blob(out)
    assert RAMP not in blob
    assert HANGAR not in blob
    assert EVTOL_ROUTE in blob
    assert out["state"] == "matches"


def test_find_skydio_url_keeps_inspect_jobs(monkeypatch):
    import app.services.robot_understanding_v1.pipeline as P
    from app.services.robot_job_search import compose_robot_job_search
    from app.services.robot_profile_cache import clear_profile_cache_memory

    clear_profile_cache_memory()

    def boom(*_a, **_k):
        raise AssertionError("indexed Skydio must not crawl")

    monkeypatch.setattr(P, "fetch_page", boom)
    monkeypatch.setattr(P, "collect_source_pack", boom)
    out = compose_robot_job_search("https://www.skydio.com/")
    blob = _blob(out)
    assert RAMP in blob or HANGAR in blob or "autonomous drone" in blob
    assert EVTOL_ROUTE not in blob
