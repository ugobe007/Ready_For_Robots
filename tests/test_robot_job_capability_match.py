"""
Golden capability-match tests — bridge from match-url caps, no OEM allowlists.
"""
from __future__ import annotations

from app.services.robot_job_capability_match import match_robot_url, match_from_chip
from app.services.robot_capability_profile import build_capability_profile


MOBILE_MANIP_CAPS = {
    "type": "Warehouse/Logistics",
    "use_case": "Warehouse Logistics",
    "capabilities": ["autonomous navigation", "payload delivery"],
    "profile_score": 80,
}
MOBILE_MANIP_TEXT = (
    "Omnidirectional mobile base with dual-arm dexterous hands for factory floors. "
    "Autonomous navigation, machine tending, load and unload parts, kitting and material handling."
)

SCRUB_CAPS = {
    "type": "Disinfection/Cleaning",
    "use_case": "Healthcare Operations",
    "capabilities": ["autonomous navigation"],
    "profile_score": 70,
}
SCRUB_TEXT = "Autonomous hard-floor scrubber for overnight cleaning routes."

OPAQUE_CAPS = {
    "type": "Unknown",
    "use_case": "General Automation",
    "capabilities": [],
    "profile_score": 35,
}


def test_mobile_manip_page_returns_jobs():
    result = match_robot_url(
        "https://example.com/robots/vega",
        robot_capabilities=MOBILE_MANIP_CAPS,
        page_text=MOBILE_MANIP_TEXT,
    )
    assert result["state"] in {"matches", "thin_corpus"}
    assert len(result["jobs"]) > 0
    fam_ids = {f["id"] for f in result["families"]}
    assert fam_ids & {"mobile_manipulation", "manipulator", "transport_amr"}
    cap_keys = {c["key"] for c in result["capabilities"]}
    assert "mobile" in cap_keys or "dual_arm" in cap_keys
    assert "scrub" not in cap_keys


def test_scrub_page_prefers_scrub_family():
    result = match_robot_url(
        "https://example.com/neo",
        robot_capabilities=SCRUB_CAPS,
        page_text=SCRUB_TEXT,
    )
    assert result["state"] in {"matches", "thin_corpus"}
    fam_ids = [f["id"] for f in result["families"]]
    assert fam_ids[0] == "floor_scrub"


def test_opaque_page_could_not_understand():
    result = match_robot_url(
        "https://example.com/",
        robot_capabilities=OPAQUE_CAPS,
        page_text="Welcome. Contact us for more information.",
    )
    assert result["state"] == "could_not_understand"
    assert result["jobs"] == []


def test_chip_recovery_returns_jobs():
    result = match_from_chip("manipulates")
    assert result["state"] in {"matches", "thin_corpus"}
    assert len(result["jobs"]) > 0


def test_no_dexmate_hostname_shortcut():
    profile = build_capability_profile(text="https://dexmate.ai/", robot_name="Dexmate")
    keys = {c.key for c in profile.capabilities}
    assert "dual_arm" not in keys
    assert "dexterous" not in keys
