"""LaserWeeder weeding laser must not match shop-floor laser/plasma CNC.

R31: COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES → MATCH.
Never keyword-leak "laser" from LaserWeeder onto cutting machines.
"""
from __future__ import annotations

from app.services.robot_capability_derive import derive_capabilities
from app.services.robot_class_qualify import apply_asserted_class
from app.services.robot_job_search import compose_robot_job_search
from app.services.robot_profile_cache import clear_profile_cache_memory
from app.services.robot_requirement_match import (
    evaluate_job,
    load_corpus,
    load_gold_jobs,
    match_jobs_from_profile,
    requirements_for_corpus_job,
)
from app.services.vendor_robot_lookup import (
    catalog_claim_facts,
    index_robot_for_name,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
)

CNC_EMPLOYERS = ("groninger", "fulcrum", "industrial metal")
CNC_TITLE_BITS = (
    "laser/plasma",
    "cutting machines",
    "cnc laser",
    "cnc",
    "tote",
    "warehouse",
    "pack station",
)
IMS_TITLE = "load and unload finished parts from laser/plasma cutting machines"


def _titles(out: dict) -> list[str]:
    return [str(j.get("title") or "") for j in out.get("jobs") or []]


def _blob(out: dict) -> str:
    parts = []
    for j in out.get("jobs") or []:
        parts.append(str(j.get("title") or ""))
        parts.append(str(j.get("company_name") or ""))
        parts.append(str(j.get("tape_family") or ""))
        parts.append(str(j.get("job_key") or ""))
    return " ".join(parts).lower()


def _assert_no_cnc_or_cutting_laser(out: dict) -> None:
    blob = _blob(out)
    for name in CNC_EMPLOYERS:
        assert name not in blob, blob
    for bit in CNC_TITLE_BITS:
        assert bit not in blob, blob
    assert IMS_TITLE not in blob
    families = {str(j.get("tape_family") or "") for j in out.get("jobs") or []}
    assert families.isdisjoint({"gripper", "pallet", "pick_pack", "pack", "transport", "cart"}), families


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
        "submitted_url": url,
    }


def _skip_crawl(monkeypatch) -> None:
    import app.services.robot_understanding_v1.pipeline as P

    def boom(*_a, **_k):
        raise AssertionError("indexed vendor must not crawl")

    monkeypatch.setattr(P, "fetch_page", boom)
    monkeypatch.setattr(P, "collect_source_pack", boom)
    clear_profile_cache_memory()


def _eval_ims(profile: dict):
    row = next(r for r in load_corpus() if r.get("job_key") == "manip_ims_riverside_ca")
    gold = load_gold_jobs()
    spec = gold.get("manip_ims_riverside_ca") or {
        "job_key": "manip_ims_riverside_ca",
        "title": row["title"],
        "company_name": row.get("company_name"),
        "requirements": requirements_for_corpus_job(row),
    }
    return evaluate_job(profile, spec, corpus_row=row)


def test_corpus_has_industrial_metal_laser_plasma_row():
    row = next(r for r in load_corpus() if r.get("job_key") == "manip_ims_riverside_ca")
    assert IMS_TITLE in (row.get("title") or "").lower()
    assert row.get("tape_family") == "gripper"
    assert "machine_tending" in (row.get("actions") or [])
    assert "laser_plasma" in (row.get("text") or "")


def test_catalog_laserweeder_is_weeding_not_cnc():
    profile = _catalog_profile(
        "https://carbonrobotics.com/", "LaserWeeder", "Carbon Robotics"
    )
    caps = derive_capabilities(profile)
    assert caps["agriculture_weed"].present is True
    assert caps["manipulate"].present is False
    out = match_jobs_from_profile(profile)
    blob = _blob(out)
    assert "weed" in blob
    assert "combine" not in blob
    _assert_no_cnc_or_cutting_laser(out)
    card = _eval_ims(profile)
    assert card.verdict == "NOT_A_MATCH"
    assert any("weeding laser" in b or "grounded work" in b for b in card.blockers)


def test_bare_laserweeder_gripper_facts_cannot_open_cnc():
    """Identity without product_class must still be weeding, not a cobot cell."""
    profile = {
        "company": {"name": "Carbon Robotics"},
        "selected_product": {"name": "LaserWeeder"},
        "submitted_url": "https://carbonrobotics.com/",
        "facts": [
            {
                "predicate": "end_effector",
                "value": "gripper",
                "epistemic": "explicit",
                "evidence_span": "high-power lasers",
            },
            {
                "predicate": "arm_count",
                "value": 1,
                "epistemic": "explicit",
                "evidence_span": "laser array",
            },
        ],
        "coverage_level": "medium",
    }
    caps = derive_capabilities(profile)
    assert caps["agriculture_weed"].present is True
    assert caps["manipulate"].present is False
    out = match_jobs_from_profile(profile)
    _assert_no_cnc_or_cutting_laser(out)
    assert "weed" in _blob(out)
    assert _eval_ims(profile).verdict == "NOT_A_MATCH"


def test_find_carbon_url_no_cutting_machines(monkeypatch):
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search("https://carbonrobotics.com/")
    assert out["state"] == "matches"
    _assert_no_cnc_or_cutting_laser(out)
    assert {j.get("tape_family") for j in out["jobs"]} == {"agriculture"}


def test_find_carbon_type_first_agriculture_tile_still_weeding_not_cnc(monkeypatch):
    """UI used to send lookup_grain=robot_type + agriculture (the FIND tile)."""
    _skip_crawl(monkeypatch)
    out = compose_robot_job_search(
        "https://carbonrobotics.com/",
        product="LaserWeeder",
        asserted_class="agriculture",
        lookup_grain="robot_type",
    )
    blob = _blob(out)
    assert "weed" in blob
    assert "combine" not in blob
    _assert_no_cnc_or_cutting_laser(out)


def test_farmdroid_fd20_no_cnc_or_cutting_laser():
    profile = _catalog_profile(
        "https://farmdroid.com/products/farmdroid-fd20/", "FD20", "FarmDroid"
    )
    out = match_jobs_from_profile(profile)
    _assert_no_cnc_or_cutting_laser(out)
    assert "weed" in _blob(out)
    assert "combine" not in _blob(out)


def test_deere_combine_no_cnc():
    profile = _catalog_profile(
        "https://www.deere.com/en/harvesting/x-series-combines/",
        "X Series Combine",
        "John Deere",
    )
    out = match_jobs_from_profile(profile)
    _assert_no_cnc_or_cutting_laser(out)
    assert {j.get("tape_family") for j in out["jobs"]} == {"agriculture"}


def test_icon_vulcan_no_cnc():
    profile = _catalog_profile("https://www.iconbuild.com/", "Vulcan", "ICON")
    out = match_jobs_from_profile(profile)
    _assert_no_cnc_or_cutting_laser(out)


def test_joby_still_one_lawa_card_not_cnc():
    profile = _catalog_profile(
        "https://www.jobyaviation.com/", "Joby eVTOL", "Joby Aviation"
    )
    out = match_jobs_from_profile(profile)
    assert out["job_count"] == 1
    assert "evtol route" in _blob(out)
    _assert_no_cnc_or_cutting_laser(out)


def test_cobot_still_gets_laser_plasma_cutting_job():
    profile = apply_asserted_class(
        {
            "company": {"name": "Universal Robots"},
            "selected_product": {"name": "UR20"},
            "facts": [],
        },
        "cobot",
    )
    caps = derive_capabilities(profile)
    assert caps["manipulate"].present is True
    assert caps["agriculture_weed"].present is False
    out = match_jobs_from_profile(profile)
    blob = _blob(out)
    assert IMS_TITLE in blob or "laser/plasma" in blob or "cnc laser" in blob
    assert "industrial metal" in blob or "fulcrum" in blob
