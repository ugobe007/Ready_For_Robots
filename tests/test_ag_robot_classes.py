"""Agriculture / marine / avionics / construction classes + LaserWeeder identity."""
from __future__ import annotations

from app.services.robot_capability_derive import derive_capabilities
from app.services.robot_class_qualify import (
    apply_asserted_class,
    normalize_class_id,
    public_class_options,
    thin_class_profile,
)
from app.services.robot_requirement_match import match_jobs_from_profile
from app.services.vendor_robot_lookup import (
    catalog_claim_facts,
    index_robot_names,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
)


def test_ten_class_options_include_work_domain_tiles():
    ids = [row["id"] for row in public_class_options()]
    assert len(ids) == 17
    assert ids[:6] == [
        "humanoid",
        "amr",
        "mobile_manipulator",
        "cobot",
        "quadruped",
        "autonomous_scrubber",
    ]
    assert ids[6:] == [
        "agriculture",
        "marine",
        "avionics",
        "aerospace",
        "construction",
        "healthcare",
        "mining",
        "warehouse",
        "logistics",
        "factory",
        "hospitality",
    ]


def test_normalize_maps_laserweeder_class_aliases():
    assert normalize_class_id("agricultural_robot") == "agriculture"
    assert normalize_class_id("agriculture") == "agriculture"
    assert normalize_class_id("construction_robot") == "construction"
    assert normalize_class_id("marine_robot") == "marine"
    assert normalize_class_id("aviation_robot") == "avionics"
    assert normalize_class_id("drone") == "avionics"
    assert normalize_class_id("evtol") == "avionics"
    assert normalize_class_id("aerospace_robot") == "aerospace"
    assert normalize_class_id("satellite") == "aerospace"
    assert normalize_class_id("humanoid") == "humanoid"


def test_asserted_agriculture_matches_field_jobs_not_humanoid():
    profile = apply_asserted_class(
        {
            "company": {"name": "Carbon Robotics"},
            "selected_product": {"name": "LaserWeeder"},
            "facts": [],
            "coverage_level": "low",
        },
        "agriculture",
    )
    caps = derive_capabilities(profile)
    assert caps["agriculture_task"].present is True
    assert caps["manipulate"].present is False
    out = match_jobs_from_profile(profile)
    assert out["state"] == "matches"
    assert out["job_count"] > 0
    families = {j.get("tape_family") for j in out["jobs"]}
    assert "agriculture" in families
    assert "pallet" not in families
    assert "gripper" not in families
    titles = " ".join(j.get("title") or "" for j in out["jobs"]).lower()
    assert "weed" in titles or "crop" in titles or "field" in titles or "orchard" in titles


def test_thin_agriculture_class_matches_weeding_jobs():
    profile = thin_class_profile("Carbon Robotics", "agriculture")
    out = match_jobs_from_profile(profile)
    assert out["state"] == "matches"
    assert any(j.get("tape_family") == "agriculture" for j in out["jobs"])
    assert any("weed" in (j.get("title") or "").lower() for j in out["jobs"])


def test_asserted_marine_and_avionics_match_their_jobs():
    marine = apply_asserted_class(
        {"company": {"name": "HullCo"}, "selected_product": {"name": "HullBot"}, "facts": []},
        "marine",
    )
    out_m = match_jobs_from_profile(marine)
    assert {j["tape_family"] for j in out_m["jobs"]} == {"marine"}

    avionics = apply_asserted_class(
        {"company": {"name": "HangarCo"}, "selected_product": {"name": "RampBot"}, "facts": []},
        "avionics",
    )
    out_a = match_jobs_from_profile(avionics)
    assert {j["tape_family"] for j in out_a["jobs"]} == {"avionics"}


def test_carbon_robotics_index_identity():
    reload_vendor_robots_index()
    vendor = lookup_vendor_by_url("https://carbonrobotics.com/")
    assert vendor is not None
    assert vendor.get("vendor_name") == "Carbon Robotics"
    assert "LaserWeeder" in index_robot_names(vendor)
    robot = next(r for r in vendor["robots"] if r.get("name") == "LaserWeeder")
    facts = catalog_claim_facts(robot)
    by_pred = {f["predicate"]: f["value"] for f in facts}
    assert by_pred["product_class"] in {"agricultural_robot", "agriculture"}
    assert by_pred.get("claims_agriculture") is True
    assert "payload_kg" not in (robot.get("specs") or {})
    assert by_pred.get("carrying_capacity") is None


def test_laserweeder_catalog_profile_matches_agriculture_jobs():
    reload_vendor_robots_index()
    vendor = lookup_vendor_by_url("https://www.carbonrobotics.com/")
    robot = next(r for r in vendor["robots"] if r.get("name") == "LaserWeeder")
    facts = catalog_claim_facts(robot)
    profile = {
        "company": {"name": "Carbon Robotics"},
        "selected_product": {"name": "LaserWeeder", "display_class": robot.get("primary_class")},
        "facts": facts,
        "coverage_level": "low",
    }
    caps = derive_capabilities(profile)
    assert caps["agriculture_task"].present is True
    assert caps["mobile"].present is True
    assert caps["manipulate"].present is False
    out = match_jobs_from_profile(profile)
    assert out["state"] == "matches"
    families = {j.get("tape_family") for j in out["jobs"]}
    assert families == {"agriculture"}
    assert not ({"pallet", "gripper", "transport"} & families)


def test_laserweeder_text_grounds_agriculture_class():
    from app.services.robot_understanding_v1 import facts as F
    from app.services.robot_understanding_v1.coverage import infer_morphology
    from app.services.robot_understanding_v1.models import RobotSource

    src = RobotSource(
        id="s",
        url="https://carbonrobotics.com/",
        source_type="product",
        fetched_at="t",
        title="LaserWeeder",
        confidence=0.85,
    )
    text = (
        "The LaserWeeder is an autonomous agricultural robot that removes weeds "
        "from vegetable crop rows with lasers."
    )
    fs = F._extract_from_page(
        src,
        text,
        subject="LaserWeeder",
        page_url="https://carbonrobotics.com/",
        page_title="LaserWeeder",
    )
    known = [f for f in fs if f.epistemic != "unknown"]
    preds = {f.predicate: f.value for f in known}
    assert preds.get("product_class") in {"agricultural_robot", "agriculture"}
    assert preds.get("claims_agriculture") is True
    assert infer_morphology(known) == "agricultural_robot"


def test_find_carbonrobotics_skips_picker_and_returns_ag_jobs(monkeypatch):
    import app.services.robot_understanding_v1.pipeline as P
    from app.services.robot_job_search import compose_robot_job_search
    from app.services.robot_profile_cache import clear_profile_cache_memory

    clear_profile_cache_memory()

    def boom(*_a, **_k):
        raise AssertionError("indexed Carbon Robotics must not crawl")

    monkeypatch.setattr(P, "fetch_page", boom)
    monkeypatch.setattr(P, "collect_source_pack", boom)
    out = compose_robot_job_search("https://carbonrobotics.com/")
    assert out["needs_class_choice"] is False
    assert out["state"] == "matches"
    assert out["job_count"] > 0
    families = {j.get("tape_family") for j in out["jobs"]}
    assert families == {"agriculture"}
    assert "humanoid" not in (out.get("robot_class") or "")
    assert (out.get("robot_class") or "") in {"agriculture", "agricultural_robot"}


def test_unknown_specs_stay_unknown_on_class_only_profile():
    profile = apply_asserted_class(
        {
            "company": {"name": "Carbon Robotics"},
            "selected_product": {"name": "LaserWeeder"},
            "facts": [],
        },
        "agriculture",
    )
    caps = derive_capabilities(profile)
    assert caps["payload"].present is False
    assert caps["reach"].present is False
