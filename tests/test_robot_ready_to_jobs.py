"""
Golden tests: old match-url understanding → Robot Job corpus.

Uses injected robot_capabilities (same shape as analyze_robot_capabilities)
plus page_text — no live OEM fetches in CI.
"""
from __future__ import annotations

from app.services.robot_job_capability_match import (
    match_from_chip,
    match_robot_url,
    profile_from_robot_ready_caps,
    is_weak_robot_ready_profile,
)
from app.services.robot_capability_profile import build_capability_profile


# --- Fixtures shaped like live match-url responses (Aug 2026 probes) ---

AGILITY_CAPS = {
    "type": "Warehouse/Logistics",
    "use_case": "Warehouse Logistics",
    "capabilities": ["cloud connected"],
    "profile_score": 68,
}
AGILITY_TEXT = (
    "Digit is a commercially deployed humanoid robot. "
    "Warehouses and factories. 35 pound carrying capacity. "
    "Digit Moves Over 100,000 Totes in Commercial Deployment."
)

DEXMATE_CAPS = {
    "type": "Service Robot",
    "use_case": "General Automation",
    "capabilities": [],
    "profile_score": 50,
}
DEXMATE_TEXT = (
    "Vega mobile manipulator. Omnidirectional mobile base with dual-arm "
    "dexterous hands for factory floors. Autonomous navigation, load and unload."
)

LOCUS_CAPS = {
    "type": "Delivery/Transport",
    "use_case": "Warehouse Logistics",
    "capabilities": ["autonomous navigation", "payload delivery", "cloud connected"],
    "profile_score": 84,
}
LOCUS_TEXT = (
    "Origin AMR for warehouse tote transport and goods-to-person fulfillment. "
    "Autonomous mobile robot material handling."
)

AVIDBOTS_CAPS = {
    "type": "Disinfection/Cleaning",
    "use_case": "Healthcare Operations",
    "capabilities": ["autonomous navigation"],
    "profile_score": 68,
}
AVIDBOTS_TEXT = (
    "Neo autonomous hard-floor scrubber for overnight cleaning routes "
    "in hospitals and airports."
)

OPAQUE_CAPS = {
    "type": "Unknown",
    "use_case": "General Automation",
    "capabilities": [],
    "profile_score": 35,
}


def test_agility_resolves_profile_and_jobs():
    result = match_robot_url(
        "https://www.agilityrobotics.com/",
        robot_capabilities=AGILITY_CAPS,
        page_text=AGILITY_TEXT,
    )
    assert result["state"] in {"matches", "thin_corpus"}
    assert len(result["jobs"]) > 0
    assert result.get("robot_capabilities", {}).get("type") == "Warehouse/Logistics"
    keys = {c["key"] for c in result["capabilities"]}
    assert keys & {"mobile", "humanoid", "tote_handling", "material_transport"}


def test_dexmate_resolves_profile_and_jobs():
    result = match_robot_url(
        "https://www.dexmate.ai/",
        robot_capabilities=DEXMATE_CAPS,
        page_text=DEXMATE_TEXT,
    )
    assert result["state"] in {"matches", "thin_corpus"}
    assert len(result["jobs"]) > 0
    keys = {c["key"] for c in result["capabilities"]}
    assert keys & {"dual_arm", "dexterous", "mobile"}


def test_locus_still_works():
    result = match_robot_url(
        "https://www.locusrobotics.com/",
        robot_capabilities=LOCUS_CAPS,
        page_text=LOCUS_TEXT,
    )
    assert result["state"] in {"matches", "thin_corpus"}
    assert len(result["jobs"]) > 0
    fams = {f["id"] for f in result["families"]}
    assert fams & {"transport_amr", "mobile_manipulation"}


def test_avidbots_still_works():
    result = match_robot_url(
        "https://www.avidbots.com/",
        robot_capabilities=AVIDBOTS_CAPS,
        page_text=AVIDBOTS_TEXT,
    )
    assert result["state"] in {"matches", "thin_corpus"}
    assert len(result["jobs"]) > 0
    fams = [f["id"] for f in result["families"]]
    assert fams[0] == "floor_scrub" or "floor_scrub" in fams


def test_opaque_could_not_understand():
    assert is_weak_robot_ready_profile(OPAQUE_CAPS)
    result = match_robot_url(
        "https://example.com/",
        robot_capabilities=OPAQUE_CAPS,
        page_text="Welcome. Contact us.",
    )
    assert result["state"] == "could_not_understand"
    assert result["jobs"] == []


def test_chip_recovery_still_works():
    result = match_from_chip("manipulates")
    assert result["state"] in {"matches", "thin_corpus"}
    assert len(result["jobs"]) > 0


def test_no_hostname_allowlist_invention():
    profile = build_capability_profile(text="https://dexmate.ai/", robot_name="Dexmate")
    keys = {c.key for c in profile.capabilities}
    assert "dual_arm" not in keys


def test_profile_bridge_from_ready_caps():
    profile = profile_from_robot_ready_caps(
        AVIDBOTS_CAPS,
        page_text=AVIDBOTS_TEXT,
        submitted_domain="avidbots.com",
    )
    assert profile.understood
    assert any(f["id"] == "floor_scrub" for f in profile.families)
