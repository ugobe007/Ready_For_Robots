"""
M2 MATCH TRUTH — requirement satisfaction, not family scores.

Frozen Understanding profiles only. Extractors are not called.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.services.robot_requirement_match import (
    LIKELY,
    MATCHED,
    UNKNOWN,
    UNMET,
    VERDICT_NOT,
    VERDICT_POSSIBLE,
    match_job_spec,
    match_jobs_from_profile,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "m2_profiles"


def _profile(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def _req(card, rid: str):
    return next(r for r in card.requirements if r.id == rid)


def test_novolex_vega_is_possible_match_with_unknowns():
    card = match_job_spec(_profile("vega"), "manip_novolex_kinston_nc")
    assert card.verdict == VERDICT_POSSIBLE
    assert _req(card, "manipulate_physical_case").state == MATCHED
    assert _req(card, "acquire_case_from_conveyor").state == UNKNOWN
    assert _req(card, "place_case_into_pallet").state == UNKNOWN
    assert _req(card, "payload_vs_object_weight").state == UNKNOWN
    assert _req(card, "compatible_grasp").state == UNKNOWN
    assert _req(card, "throughput_vs_line_rate").state == UNKNOWN
    assert card.blockers == []
    why = " ".join(card.why).lower()
    assert "dual-arm" in why or "manipulation" in why
    assert "2.2" in why or "reach" in why
    assert any("case weight" in u.lower() for u in card.still_unknown)
    assert any("gripper" in u.lower() or "grasp" in u.lower() for u in card.still_unknown)
    assert any("cycle" in u.lower() for u in card.still_unknown)
    assert "score" not in card.to_api_job()


def test_novolex_digit_is_possible_match_if_manipulation_grounded():
    card = match_job_spec(_profile("digit"), "manip_novolex_kinston_nc")
    assert card.verdict == VERDICT_POSSIBLE
    assert _req(card, "manipulate_physical_case").state == MATCHED
    assert _req(card, "payload_vs_object_weight").state == UNKNOWN
    assert card.blockers == []


def test_novolex_origin_is_not_a_match_blocker_named():
    card = match_job_spec(_profile("origin"), "manip_novolex_kinston_nc")
    assert card.verdict == VERDICT_NOT
    assert _req(card, "manipulate_physical_case").state == UNMET
    assert any("manipulation" in b.lower() for b in card.blockers)
    assert any("case acquisition" in b.lower() or "pallet" in b.lower() for b in card.blockers)


def test_novolex_neo_is_not_a_match():
    card = match_job_spec(_profile("neo"), "manip_novolex_kinston_nc")
    assert card.verdict == VERDICT_NOT
    assert _req(card, "manipulate_physical_case").state == UNMET


def test_curascript_origin_and_digit_vs_neo_and_fixed_arm():
    origin = match_job_spec(_profile("origin"), "origin_curascript_tempe")
    digit = match_job_spec(_profile("digit"), "origin_curascript_tempe")
    neo = match_job_spec(_profile("neo"), "origin_curascript_tempe")
    arm = match_job_spec(_profile("fixed_arm"), "origin_curascript_tempe")
    assert origin.verdict == VERDICT_POSSIBLE
    assert digit.verdict == VERDICT_POSSIBLE
    assert _req(origin, "relocate_totes_or_carts").state == MATCHED
    assert neo.verdict == VERDICT_NOT
    assert arm.verdict == VERDICT_NOT
    assert _req(arm, "mobility").state == UNMET


def test_airport_scrub_neo_vs_everyone_else():
    neo = match_job_spec(_profile("neo"), "neo_unifi_atl")
    vega = match_job_spec(_profile("vega"), "neo_unifi_atl")
    digit = match_job_spec(_profile("digit"), "neo_unifi_atl")
    origin = match_job_spec(_profile("origin"), "neo_unifi_atl")
    assert neo.verdict == VERDICT_POSSIBLE
    assert _req(neo, "hard_floor_scrub").state == MATCHED
    assert vega.verdict == VERDICT_NOT
    assert digit.verdict == VERDICT_NOT
    assert origin.verdict == VERDICT_NOT


def test_inspection_spot_vs_transport_and_manipulation():
    spot = match_job_spec(_profile("spot"), "plant_inspect")
    origin = match_job_spec(_profile("origin"), "plant_inspect")
    vega = match_job_spec(_profile("vega"), "plant_inspect")
    neo = match_job_spec(_profile("neo"), "plant_inspect")
    assert spot.verdict == VERDICT_POSSIBLE
    inspect = _req(spot, "inspect_route_mobility")
    assert inspect.state in {MATCHED, LIKELY}
    assert inspect.derivation == "inspect_from_quadruped" or inspect.state == MATCHED
    assert origin.verdict == VERDICT_NOT
    assert vega.verdict == VERDICT_NOT
    assert neo.verdict == VERDICT_NOT


def test_corpus_boards_are_materially_differentiated():
    vega = match_jobs_from_profile(_profile("vega"))
    digit = match_jobs_from_profile(_profile("digit"))
    origin = match_jobs_from_profile(_profile("origin"))
    neo = match_jobs_from_profile(_profile("neo"))
    assert vega["matcher"] == "requirement_v1"

    def families(result):
        return {j["tape_family"] for j in result["jobs"]}

    def keys(result):
        return {j["job_key"] for j in result["jobs"]}

    vega_f, digit_f, origin_f, neo_f = map(families, (vega, digit, origin, neo))
    vega_keys, digit_keys, origin_keys, neo_keys = map(keys, (vega, digit, origin, neo))

    assert vega_f <= {"pallet", "gripper"}
    assert "manip_novolex_kinston_nc" in vega_keys
    assert "scrub" not in vega_f
    assert "transport" not in vega_f

    assert origin_f <= {"transport", "cart"}
    assert "origin_curascript_tempe" in origin_keys
    assert origin_f.isdisjoint({"pallet", "gripper", "scrub", "inspect"})

    assert neo_f == {"scrub"}
    assert "neo_unifi_atl" in neo_keys
    assert neo_f.isdisjoint({"pallet", "gripper", "transport", "cart"})

    # Digit top of board is distinctive work, not an AMR tote list.
    # Tote/cart jobs remain possible (see utilization ranking test) but sit
    # below manipulation/mobile-manipulation in the default window.
    assert digit_f <= {"gripper", "pallet"}
    assert "scrub" not in digit_f

    assert vega_keys != origin_keys
    assert origin_keys != neo_keys
    assert vega_keys != neo_keys
    assert digit_keys != neo_keys

    for job in vega["jobs"] + origin["jobs"] + neo["jobs"] + digit["jobs"]:
        assert job["verdict"] == VERDICT_POSSIBLE
        assert job["why"]
        assert "score" not in job


def test_ranking_prefers_distinctive_capability_utilization():
    """Among jobs that pass the gate, rank by how much of this robot is used.

    Digit + tote is valid. Digit + machine load uses more of Digit, so it
    ranks first. Origin + tote remains an excellent Origin match. No quota.
    """
    digit = match_jobs_from_profile(_profile("digit"), limit=40)
    origin = match_jobs_from_profile(_profile("origin"), limit=12)

    digit_jobs = digit["jobs"]
    families = [j["tape_family"] for j in digit_jobs]
    keys = [j["job_key"] for j in digit_jobs]
    first_tote = next(
        i for i, family in enumerate(families) if family in {"transport", "cart"}
    )
    assert first_tote > 0
    assert all(family in {"gripper", "pallet"} for family in families[:first_tote])
    assert "cnc_load" in keys
    assert "cnc_unload" in keys
    assert "hospital_med_carts" in keys
    assert "origin_curascript_tempe" in keys
    assert keys.index("cnc_load") < keys.index("hospital_med_carts")
    assert keys.index("cnc_unload") < keys.index("origin_curascript_tempe")

    origin_families = {j["tape_family"] for j in origin["jobs"]}
    origin_keys = {j["job_key"] for j in origin["jobs"]}
    assert origin_families <= {"transport", "cart"}
    assert "origin_curascript_tempe" in origin_keys
    assert origin["jobs"][0]["tape_family"] in {"transport", "cart"}
    assert all("score" not in j for j in digit_jobs + origin["jobs"])


def test_hospitality_delivery_robot_matches_transport_work():
    """A hospitality/healthcare delivery robot (Relay) is a transport robot.

    Regression: it used to derive only `mobile` and match 0 jobs because the
    ontology had no slot for autonomous item delivery/transport (only warehouse
    tote handling). It must now match transport/cart work — and only that.
    """
    from app.services.robot_capability_derive import derive_capabilities

    profile = _profile("relay")
    caps = derive_capabilities(profile)
    assert caps["transport"].present  # delivery/transport grounded
    assert not caps["manipulate"].present  # a delivery cart does not manipulate
    assert caps["mobile"].present

    result = match_jobs_from_profile(profile, limit=60)
    assert result["job_count"] > 0  # no longer 0 jobs
    families = {j["tape_family"] for j in result["jobs"]}
    # Delivery/transport work only (incl. hospitality serving, hospital clinical
    # delivery, eldercare resident services) — never manipulation, food/beverage
    # prep, scrubbing, or inspection.
    assert families <= {"transport", "cart", "serve", "clinical_delivery", "resident_services"}
    assert families & {"transport", "cart"}
    assert families.isdisjoint({"pallet", "gripper", "scrub", "inspect", "food_prep", "beverage", "restroom"})
    for job in result["jobs"]:
        assert job["verdict"] == VERDICT_POSSIBLE
        assert job["why"]
        assert any("transport" in w.lower() or "delivery" in w.lower() or "mobile" in w.lower() for w in job["why"])
    assert any(c["key"] == "transport" for c in result["capabilities"])


def test_delivery_robot_does_not_match_manipulation_or_scrub():
    """Truthful gating: a delivery robot must still be rejected from manipulation
    and scrubbing work it cannot do."""
    assert match_job_spec(_profile("relay"), "manip_novolex_kinston_nc").verdict == VERDICT_NOT
    assert match_job_spec(_profile("relay"), "neo_unifi_atl").verdict == VERDICT_NOT


def test_hospitality_ontology_serve_food_beverage_restroom():
    """Hospitality is cross-cutting: serving, food prep, beverage prep, and
    restroom cleaning are now first-class capabilities that map to their own work
    families — and only those (no false industrial/scrub/manipulation matches)."""
    from app.services.robot_capability_derive import derive_capabilities

    def fams(name):
        return {j["tape_family"] for j in match_jobs_from_profile(_profile(name), limit=60)["jobs"]}

    # Serving robot (Bear Servi): item delivery → serve/transport work.
    servi_caps = derive_capabilities(_profile("servi"))
    assert servi_caps["transport"].present and servi_caps["mobile"].present
    servi_fams = fams("servi")
    assert "serve" in servi_fams
    # A delivery/transport robot serves all delivery families (incl. hospital
    # clinical + eldercare resident delivery), never manipulation/cleaning work.
    assert servi_fams <= {"serve", "transport", "cart", "clinical_delivery", "resident_services"}
    assert servi_fams.isdisjoint({"food_prep", "beverage", "restroom", "scrub", "pallet", "gripper", "inspect"})

    # Food-prep robot (Miso Flippy): food_prep only — never industrial manipulation.
    flippy_caps = derive_capabilities(_profile("flippy"))
    assert flippy_caps["food_prep"].present
    assert not flippy_caps["manipulate"].present  # distinct from CNC/case manipulation
    assert fams("flippy") == {"food_prep"}

    # Beverage robot (Richtech ADAM): beverage_prep work (dual-arm is incidental).
    adam_fams = fams("adam")
    assert "beverage" in adam_fams
    assert adam_fams.isdisjoint({"scrub", "restroom", "transport", "serve"})

    # Restroom cleaning robot (Somatic): restroom work, not hard-floor scrub jobs.
    somatic_caps = derive_capabilities(_profile("somatic"))
    assert somatic_caps["surface_clean"].present and somatic_caps["mobile"].present
    assert fams("somatic") == {"restroom"}


def test_frozen_robots_do_not_leak_into_hospitality_families():
    """The new hospitality families require their specific capabilities, so the
    frozen canonical robots (which lack them) never match hospitality work."""
    for name in ("vega", "digit", "origin", "neo", "spot"):
        fams = {j["tape_family"] for j in match_jobs_from_profile(_profile(name), limit=60)["jobs"]}
        assert fams.isdisjoint({"food_prep", "beverage", "restroom"}), (name, fams)


def test_healthcare_eldercare_delivery_matches_transport_robots():
    """Hospital clinical delivery + eldercare resident services require the
    autonomous item-delivery (transport) capability. A delivery robot (Relay)
    matches them; a warehouse tote-AMR (Origin, tote_transport only) does not —
    so the frozen Origin board is unchanged."""
    relay_fams = {j["tape_family"] for j in match_jobs_from_profile(_profile("relay"), limit=60)["jobs"]}
    assert {"clinical_delivery", "resident_services"} <= relay_fams

    # A warehouse tote-AMR (tote_transport, no item-delivery `transport`) is not a
    # clinical/resident delivery robot — deliver_items requires `transport`.
    origin_fams = {j["tape_family"] for j in match_jobs_from_profile(_profile("origin"), limit=60)["jobs"]}
    assert origin_fams.isdisjoint({"clinical_delivery", "resident_services"})


def test_api_uses_requirement_matcher_when_profile_present():
    from app.api.robot_job_match import RobotJobMatchIn, post_robot_job_match

    body = RobotJobMatchIn(
        url="https://www.dexmate.ai/",
        profile=_profile("vega"),
    )
    result = post_robot_job_match(body)
    assert result["matcher"] == "requirement_v1"
    assert result["state"] in {"matches", "thin_corpus"}
    assert any(j["job_key"] == "manip_novolex_kinston_nc" for j in result["jobs"])
    assert all("score" not in j for j in result["jobs"])


def test_no_percentage_and_unknowns_stay_unknown():
    card = match_job_spec(_profile("vega"), "manip_novolex_kinston_nc")
    payload = _req(card, "payload_vs_object_weight")
    assert payload.state == UNKNOWN
    dumped = json.dumps(card.to_api_job())
    assert "%" not in dumped
    assert "score" not in dumped
