"""eVTOL / drone / ag / construction FIND must not pad with CNC or pack jobs.

Joby on https://www.jobyaviation.com/ must not return groninger / Fulcrum /
Industrial Metal Supply CNC tend-cell work. A short honest eVTOL list (the
LAWA vertiport card) is correct. Never invent employers.
"""
from __future__ import annotations

from app.services.robot_capability_derive import derive_capabilities
from app.services.robot_class_qualify import (
    apply_asserted_class,
    lookup_class_id,
    normalize_class_id,
    thin_class_profile,
)
from app.services.robot_job_search import compose_robot_job_search
from app.services.robot_profile_cache import clear_profile_cache_memory
from app.services.robot_requirement_match import match_jobs_from_profile
from app.services.vendor_robot_lookup import (
    catalog_claim_facts,
    index_robot_for_name,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
)

PAD_EMPLOYERS = ("groninger", "fulcrum", "industrial metal")
PAD_TITLE_BITS = ("cnc", "tote", "warehouse", "pack station")
PAD_FAMILIES = frozenset(
    {"gripper", "pallet", "pick_pack", "pack", "transport", "cart"}
)
EVTOL_ROUTE = "fly an evtol route"


def _titles(out: dict) -> list[str]:
    return [str(j.get("title") or "") for j in out.get("jobs") or []]


def _blob(out: dict) -> str:
    parts = []
    for j in out.get("jobs") or []:
        parts.append(str(j.get("title") or ""))
        parts.append(str(j.get("company_name") or ""))
        parts.append(str(j.get("tape_family") or ""))
    return " ".join(parts).lower()


def _families(out: dict) -> set[str]:
    return {str(j.get("tape_family") or "") for j in out.get("jobs") or []}


def _assert_no_cnc_pad(out: dict) -> None:
    blob = _blob(out)
    for name in PAD_EMPLOYERS:
        assert name not in blob, blob
    for bit in PAD_TITLE_BITS:
        assert bit not in blob, blob
    assert _families(out).isdisjoint(PAD_FAMILIES), _families(out)


def _catalog_profile(url: str, product_name: str, company: str) -> dict:
    reload_vendor_robots_index()
    vendor = lookup_vendor_by_url(url)
    assert vendor is not None, url
    robot = index_robot_for_name(vendor, product_name)
    assert robot is not None, product_name
    return {
        "company": {"name": company},
        "selected_product": {
            "name": product_name,
            "display_class": robot.get("primary_class"),
        },
        "facts": catalog_claim_facts(robot),
        "coverage_level": "low",
    }


def _skip_crawl(monkeypatch) -> None:
    import app.services.robot_understanding_v1.pipeline as P

    def boom(*_a, **_k):
        raise AssertionError("indexed vendor must not crawl")

    monkeypatch.setattr(P, "fetch_page", boom)
    monkeypatch.setattr(P, "collect_source_pack", boom)
    clear_profile_cache_memory()


def test_lookup_class_keeps_evtol_and_drone_off_the_avionics_tile():
    assert normalize_class_id("evtol") == "avionics"
    assert normalize_class_id("drone") == "avionics"
    assert lookup_class_id("evtol") == "evtol"
    assert lookup_class_id("drone") == "drone"
    assert lookup_class_id("uav") == "drone"
    assert lookup_class_id("avionics") == "avionics"


def test_joby_catalog_is_one_evtol_job_not_cnc():
    profile = _catalog_profile(
        "https://www.jobyaviation.com/", "Joby eVTOL", "Joby Aviation"
    )
    caps = derive_capabilities(profile)
    assert caps["evtol_flight"].present is True
    assert caps["manipulate"].present is False
    out = match_jobs_from_profile(profile)
    assert out["state"] == "matches"
    assert out["job_count"] == 1
    assert EVTOL_ROUTE in _blob(out)
    _assert_no_cnc_pad(out)
    assert _families(out) == {"avionics"}


def test_noisy_evtol_arm_facts_still_do_not_open_cnc():
    """Factory-page gripper/arm language must not pad eVTOL with tend-cell jobs."""
    profile = _catalog_profile(
        "https://www.jobyaviation.com/", "Joby eVTOL", "Joby Aviation"
    )
    profile["facts"] = list(profile["facts"]) + [
        {
            "predicate": "end_effector",
            "value": "gripper",
            "epistemic": "explicit",
            "evidence_span": "factory gripper",
        },
        {
            "predicate": "arm_count",
            "value": 1,
            "epistemic": "explicit",
            "evidence_span": "robot arm",
        },
    ]
    caps = derive_capabilities(profile)
    assert caps["evtol_flight"].present is True
    assert caps["manipulate"].present is False
    out = match_jobs_from_profile(profile)
    blob = _blob(out)
    assert EVTOL_ROUTE in blob
    _assert_no_cnc_pad(out)
    assert all("load parts into cnc" not in t.lower() for t in _titles(out))


def test_asserted_evtol_is_not_the_avionics_union():
    profile = apply_asserted_class(
        {
            "company": {"name": "Joby Aviation"},
            "selected_product": {"name": "Joby eVTOL"},
            "facts": [],
        },
        "evtol",
    )
    classes = {
        str(f.get("value")).lower()
        for f in profile["facts"]
        if f.get("predicate") == "product_class"
    }
    assert "evtol" in classes
    assert "avionics" not in classes
    out = match_jobs_from_profile(profile)
    blob = _blob(out)
    assert EVTOL_ROUTE in blob
    assert "walk the airside ramp" not in blob
    assert "autonomous drone" not in blob
    assert "delivery drone" not in blob
    _assert_no_cnc_pad(out)


def test_type_first_evtol_skips_cnc_and_ramp(monkeypatch):
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search(
        "https://www.jobyaviation.com/",
        product="Joby eVTOL",
        asserted_class="evtol",
        lookup_grain="robot_type",
    )
    assert out["robot_class"] == "evtol"
    blob = _blob(out)
    assert EVTOL_ROUTE in blob
    assert "walk the airside ramp" not in blob
    _assert_no_cnc_pad(out)


def test_find_joby_url_no_cnc(monkeypatch):
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search("https://www.jobyaviation.com/")
    assert out["state"] == "matches"
    assert EVTOL_ROUTE in _blob(out)
    _assert_no_cnc_pad(out)


def test_find_archer_url_no_cnc(monkeypatch):
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search("https://archer.com/")
    assert EVTOL_ROUTE in _blob(out)
    _assert_no_cnc_pad(out)
    assert "walk the airside ramp" not in _blob(out)


def test_find_skydio_no_cnc_or_evtol_route(monkeypatch):
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search("https://www.skydio.com/")
    blob = _blob(out)
    _assert_no_cnc_pad(out)
    assert EVTOL_ROUTE not in blob
    assert (
        "walk the airside ramp" in blob
        or "inspect an airframe" in blob
        or "autonomous drone" in blob
        or "delivery drone" in blob
    )


def test_find_carbon_laserweeder_no_cnc(monkeypatch):
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search("https://carbonrobotics.com/")
    assert _families(out) == {"agriculture"}
    _assert_no_cnc_pad(out)


def test_deere_combine_catalog_no_cnc():
    profile = _catalog_profile(
        "https://www.deere.com/en/harvesting/x-series-combines/",
        "X Series Combine",
        "John Deere",
    )
    out = match_jobs_from_profile(profile)
    assert _families(out) == {"agriculture"}
    _assert_no_cnc_pad(out)


def test_icon_vulcan_catalog_no_cnc():
    profile = _catalog_profile("https://www.iconbuild.com/", "Vulcan", "ICON")
    out = match_jobs_from_profile(profile)
    assert _families(out) == {"construction"}
    _assert_no_cnc_pad(out)


def test_thin_avionics_tile_still_flying_work_not_cnc():
    profile = thin_class_profile("HangarCo", "avionics")
    out = match_jobs_from_profile(profile)
    assert _families(out) == {"avionics"}
    _assert_no_cnc_pad(out)
