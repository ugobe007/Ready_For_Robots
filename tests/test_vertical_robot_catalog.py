"""Avionics vs aerospace split + combine/tractor/home/drone/debris identity."""
from __future__ import annotations

from app.services.robot_capability_derive import derive_capabilities
from app.services.robot_class_qualify import (
    apply_asserted_class,
    public_class_options,
    thin_class_profile,
)
from app.services.robot_requirement_match import match_jobs_from_profile
from app.services.vendor_robot_lookup import (
    catalog_claim_facts,
    index_robot_for_name,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
)


def _extract(url: str, title: str, text: str, subject: str):
    from app.services.robot_understanding_v1 import facts as F
    from app.services.robot_understanding_v1.coverage import infer_morphology
    from app.services.robot_understanding_v1.models import RobotSource

    src = RobotSource(
        id="s",
        url=url,
        source_type="product",
        fetched_at="t",
        title=title,
        confidence=0.85,
    )
    fs = F._extract_from_page(
        src, text, subject=subject, page_url=url, page_title=title
    )
    known = [f for f in fs if f.epistemic != "unknown"]
    preds = {f.predicate: f.value for f in known}
    return preds, infer_morphology(known)


def _match_families(profile: dict) -> set[str]:
    out = match_jobs_from_profile(profile)
    return {j.get("tape_family") for j in out["jobs"]}


def test_picker_has_aerospace_and_four_domain_tiles():
    ids = [row["id"] for row in public_class_options()]
    assert len(ids) == 12
    assert ids[6:] == [
        "agriculture",
        "marine",
        "avionics",
        "aerospace",
        "construction",
        "healthcare",
    ]
    by_id = {row["id"]: row for row in public_class_options()}
    assert "drone" in by_id["avionics"]["hint"].lower()
    assert "evtol" in by_id["avionics"]["hint"].lower()
    assert "satellite" in by_id["aerospace"]["hint"].lower()


def test_laserweeder_still_agriculture_no_regress():
    reload_vendor_robots_index()
    vendor = lookup_vendor_by_url("https://carbonrobotics.com/")
    assert vendor is not None
    robot = index_robot_for_name(vendor, "LaserWeeder")
    assert robot is not None
    facts = catalog_claim_facts(robot)
    by_pred = {f["predicate"]: f["value"] for f in facts}
    assert by_pred["product_class"] in {"agricultural_robot", "agriculture"}
    assert by_pred.get("claims_agriculture") is True
    profile = {
        "company": {"name": "Carbon Robotics"},
        "selected_product": {"name": "LaserWeeder", "display_class": robot.get("primary_class")},
        "facts": facts,
        "coverage_level": "low",
    }
    caps = derive_capabilities(profile)
    assert caps["agriculture_task"].present is True
    assert caps["payload"].present is False
    assert caps["reach"].present is False
    assert _match_families(profile) == {"agriculture"}


def test_combine_and_tractor_oem_classifies_agriculture():
    preds, morph = _extract(
        "https://www.deere.com/en/harvesting/x-series-combines/",
        "X Series Combines",
        "The John Deere X Series Combine is an autonomous combine that harvests grain in the field.",
        "X Series Combine",
    )
    assert preds.get("product_class") in {"agricultural_robot", "agriculture"}
    assert preds.get("claims_agriculture") is True
    assert morph == "agricultural_robot"

    tractor = apply_asserted_class(
        {
            "company": {"name": "John Deere"},
            "selected_product": {"name": "Autonomous Tractor"},
            "facts": [],
        },
        "agriculture",
    )
    caps = derive_capabilities(tractor)
    assert caps["agriculture_task"].present is True
    assert caps["payload"].present is False
    families = _match_families(tractor)
    assert families == {"agriculture"}
    titles = " ".join(
        j.get("title") or "" for j in match_jobs_from_profile(tractor)["jobs"]
    ).lower()
    assert "combine" in titles or "tractor" in titles or "plant" in titles or "harvest" in titles


def test_tractor_implement_is_configuration_not_class():
    preds, _morph = _extract(
        "https://www.deere.com/en/sprayers/see-spray-ultimate/",
        "See & Spray Ultimate",
        "See & Spray Ultimate is a hitch-mounted implement on a tractor that sprays crop rows.",
        "See & Spray Ultimate",
    )
    assert preds.get("configuration_kind") == "implement_on_host"
    assert preds.get("host_platform") == "tractor"
    assert preds.get("claims_agriculture") is True
    assert preds.get("product_class") not in {"tractor_attachment", "attachment"}

    profile = {
        "company": {"name": "John Deere"},
        "selected_product": {"name": "See & Spray Ultimate"},
        "facts": [
            {
                "predicate": "configuration_kind",
                "value": "implement_on_host",
                "epistemic": "explicit",
                "evidence_span": "implement on tractor",
            },
            {
                "predicate": "host_platform",
                "value": "tractor",
                "epistemic": "explicit",
                "evidence_span": "tractor host",
            },
        ],
    }
    caps = derive_capabilities(profile)
    assert caps["agriculture_task"].present is True
    assert caps["payload"].present is False
    assert _match_families(profile) == {"agriculture"}


def test_homebuilder_construction_oem_classifies_construction():
    preds, morph = _extract(
        "https://www.iconbuild.com/vulcan",
        "Vulcan",
        "ICON Vulcan is a 3D printing robot that builds homes and houses on the residential construction site.",
        "Vulcan",
    )
    assert preds.get("product_class") == "construction_robot"
    assert preds.get("claims_construction") is True
    assert morph == "construction_robot"

    reload_vendor_robots_index()
    vendor = lookup_vendor_by_url("https://www.iconbuild.com/")
    assert vendor is not None
    robot = index_robot_for_name(vendor, "Vulcan")
    assert robot is not None
    facts = catalog_claim_facts(robot)
    profile = {
        "company": {"name": "ICON"},
        "selected_product": {"name": "Vulcan", "display_class": robot.get("primary_class")},
        "facts": facts,
    }
    assert derive_capabilities(profile)["construction_task"].present is True
    families = _match_families(profile)
    assert families == {"construction"}
    titles = " ".join(
        j.get("title") or "" for j in match_jobs_from_profile(profile)["jobs"]
    ).lower()
    assert "home" in titles or "house" in titles or "building" in titles or "jobsite" in titles


def test_drone_and_evtol_classify_avionics():
    preds, morph = _extract(
        "https://www.skydio.com/x10",
        "Skydio X10",
        "The Skydio X10 is an autonomous inspection drone and UAV for aerial inspection.",
        "X10",
    )
    assert preds.get("product_class") in {"drone", "aviation_robot", "avionics"}
    assert preds.get("claims_avionics") is True
    assert morph in {"drone", "aviation_robot"}

    evtol = apply_asserted_class(
        {
            "company": {"name": "Joby Aviation"},
            "selected_product": {"name": "Joby eVTOL"},
            "facts": [],
        },
        "avionics",
    )
    assert derive_capabilities(evtol)["avionics_task"].present is True
    assert derive_capabilities(evtol)["aerospace_task"].present is False
    families = _match_families(evtol)
    assert families == {"avionics"}
    titles = " ".join(
        j.get("title") or "" for j in match_jobs_from_profile(evtol)["jobs"]
    ).lower()
    assert "drone" in titles or "evtol" in titles or "aircraft" in titles or "flight" in titles


def test_debris_and_sat_servicing_classify_aerospace():
    preds, morph = _extract(
        "https://astroscale.com/missions/elsa-d/",
        "ELSA-d",
        "ELSA-d is an on-orbit servicing spacecraft that demonstrates satellite servicing and debris capture.",
        "ELSA-d",
    )
    assert preds.get("product_class") in {"aerospace_robot", "aerospace"}
    assert preds.get("claims_aerospace") is True
    assert morph == "aerospace_robot"

    profile = thin_class_profile("Astroscale", "aerospace")
    caps = derive_capabilities(profile)
    assert caps["aerospace_task"].present is True
    assert caps["avionics_task"].present is False
    assert caps["payload"].present is False
    families = _match_families(profile)
    assert families == {"aerospace"}
    titles = " ".join(
        j.get("title") or "" for j in match_jobs_from_profile(profile)["jobs"]
    ).lower()
    assert "debris" in titles or "satellite" in titles or "orbit" in titles or "launch" in titles


def test_avionics_does_not_match_aerospace_jobs():
    avionics = apply_asserted_class(
        {"company": {"name": "Skydio"}, "selected_product": {"name": "X10"}, "facts": []},
        "avionics",
    )
    assert _match_families(avionics) == {"avionics"}
    aerospace = apply_asserted_class(
        {"company": {"name": "Astroscale"}, "selected_product": {"name": "ELSA-d"}, "facts": []},
        "aerospace",
    )
    assert _match_families(aerospace) == {"aerospace"}
