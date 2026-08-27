"""Verified OEM seed: named SKU ingest + configuration MATCH (not category dump)."""
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


def _titles(profile: dict) -> str:
    return " ".join(
        str(j.get("title") or "") for j in match_jobs_from_profile(profile)["jobs"]
    ).lower()


def _families(profile: dict) -> set[str]:
    return {j.get("tape_family") for j in match_jobs_from_profile(profile)["jobs"]}


def test_farmdroid_fd20_is_weeding_not_combine():
    profile = _catalog_profile(
        "https://farmdroid.com/products/farmdroid-fd20/", "FD20", "FarmDroid"
    )
    caps = derive_capabilities(profile)
    assert caps["agriculture_task"].present is True
    assert caps["agriculture_weed"].present is True
    assert caps["agriculture_combine"].present is False
    blob = _titles(profile)
    assert "weed" in blob
    assert "combine" not in blob
    assert "cnc" not in blob


def test_laserweeder_still_weeding_not_combine():
    profile = _catalog_profile("https://carbonrobotics.com/", "LaserWeeder", "Carbon Robotics")
    caps = derive_capabilities(profile)
    assert caps["agriculture_weed"].present is True
    assert caps["agriculture_combine"].present is False
    blob = _titles(profile)
    assert "weed" in blob
    assert "combine" not in blob
    assert _families(profile) == {"agriculture"}


def test_icon_vulcan_prints_homes_not_block_or_cnc():
    profile = _catalog_profile("https://www.iconbuild.com/", "Vulcan", "ICON")
    caps = derive_capabilities(profile)
    assert caps["construction_print"].present is True
    assert caps["construction_block"].present is False
    blob = _titles(profile)
    assert "3d-print" in blob or "3d print" in blob
    assert "lay block" not in blob
    assert "cnc" not in blob
    assert _families(profile) == {"construction"}


def test_hadrian_lays_block_not_3d_print():
    profile = _catalog_profile("https://www.fbr.com.au/", "Hadrian X", "FBR")
    caps = derive_capabilities(profile)
    assert caps["construction_block"].present is True
    assert caps["construction_print"].present is False
    blob = _titles(profile)
    assert "block" in blob
    assert "3d-print" not in blob and "3d print" not in blob


def test_elroy_chaparral_is_autonomous_flight_not_lawa_or_drone():
    profile = _catalog_profile(
        "https://elroyair.com/chaparral/aircraft", "Chaparral", "Elroy Air"
    )
    caps = derive_capabilities(profile)
    assert caps["autonomous_flight"].present is True
    assert caps["evtol_flight"].present is False
    assert caps["drone_task"].present is False
    blob = _titles(profile)
    assert "autonomous airplane" in blob
    assert "evtol route" not in blob
    assert "autonomous drone" not in blob


def test_volocopter_and_ehang_are_evtol_not_drone():
    volo = _catalog_profile(
        "https://www.volocopter.com/en/product/volocity", "VoloCity", "Volocopter"
    )
    assert derive_capabilities(volo)["evtol_flight"].present is True
    assert derive_capabilities(volo)["drone_task"].present is False
    blob = _titles(volo)
    assert "evtol route" in blob
    assert "autonomous drone" not in blob

    ehang = _catalog_profile("https://www.ehang.com/ehang216s", "EH216-S", "EHang")
    assert derive_capabilities(ehang)["evtol_flight"].present is True
    assert derive_capabilities(ehang)["drone_task"].present is False


def test_dji_and_elios_are_drone_not_evtol():
    dji = _catalog_profile(
        "https://enterprise.dji.com/matrice-350-rtk", "Matrice 350 RTK", "DJI"
    )
    assert derive_capabilities(dji)["drone_task"].present is True
    assert derive_capabilities(dji)["evtol_flight"].present is False
    assert "evtol route" not in _titles(dji)

    elios = _catalog_profile("https://www.flyability.com/elios-3", "Elios 3", "Flyability")
    assert derive_capabilities(elios)["drone_task"].present is True
    assert derive_capabilities(elios)["evtol_flight"].present is False


def test_robotnik_amr_is_warehouse_not_weeding_or_evtol():
    profile = _catalog_profile(
        "https://robotnik.eu/products/mobile-robots/rb-robout/",
        "RB-ROBOUT",
        "Robotnik",
    )
    caps = derive_capabilities(profile)
    assert profile["selected_product"]["display_class"] == "amr"
    assert caps["agriculture_task"].present is False
    assert caps["evtol_flight"].present is False
    families = _families(profile)
    assert "agriculture" not in families
    assert "avionics" not in families


def test_find_tile_agriculture_is_union_not_one_sku():
    profile = apply_asserted_class(
        {
            "company": {"name": "Unknown farm OEM"},
            "selected_product": {"name": "Field robot"},
            "facts": [],
        },
        "agriculture",
    )
    caps = derive_capabilities(profile)
    assert caps["agriculture_weed"].present is True
    assert caps["agriculture_combine"].present is True
    blob = _titles(profile)
    assert "weed" in blob
    assert "combine" in blob


def test_naio_orio_indexed_and_weeding():
    profile = _catalog_profile(
        "https://www.naio-technologies.com/en/orio-robot/", "Orio", "Naio Technologies"
    )
    assert derive_capabilities(profile)["agriculture_weed"].present is True
    assert "combine" not in _titles(profile)
