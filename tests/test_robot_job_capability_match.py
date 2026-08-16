"""Golden capability-match tests — no OEM hostname allowlists."""
from __future__ import annotations

from app.services.robot_job_capability_match import match_robot_url, match_from_chip
from app.services.robot_capability_profile import build_capability_profile


MOBILE_MANIP_HTML = """
<html><head><title>Vega Mobile Manipulator | Example Robotics</title></head>
<body>
<h1>Vega — general-purpose mobile manipulation robot</h1>
<p>Omnidirectional mobile base with dual-arm dexterous hands for factory floors.</p>
<p>Autonomous navigation, machine tending, load and unload parts, kitting and material handling.</p>
<p>10+ lb payload per arm, 10+ hour runtime, manufacturing logistics and retail deployments.</p>
</body></html>
"""

SCRUB_HTML = """
<html><head><title>Neo Floor Scrubber</title></head>
<body>
<p>Autonomous hard-floor scrubber for overnight cleaning routes in hospitals and airports.</p>
<p>Large indoor floor area coverage with repeatable scrubbing.</p>
</body></html>
"""

OPAQUE_HTML = """
<html><head><title>Home</title></head>
<body><p>Welcome. Contact us for more information.</p></body></html>
"""


def test_mobile_manip_page_returns_jobs():
    result = match_robot_url(
        "https://example.com/robots/vega",
        html=MOBILE_MANIP_HTML,
    )
    assert result["state"] in {"matches", "thin_corpus"}
    assert len(result["jobs"]) > 0
    fam_ids = {f["id"] for f in result["families"]}
    assert fam_ids & {"mobile_manipulation", "manipulator", "transport_amr"}
    cap_keys = {c["key"] for c in result["capabilities"]}
    assert "mobile" in cap_keys or "dual_arm" in cap_keys
    # No fabricated capability absent from page
    assert "inspect" not in cap_keys
    assert "scrub" not in cap_keys
    titles = " ".join(j["title"].lower() for j in result["jobs"])
    assert any(
        w in titles for w in ("cnc", "kit", "load", "unload", "replenish", "tote", "pallet", "part")
    )


def test_scrub_page_prefers_scrub_family():
    result = match_robot_url("https://example.com/neo", html=SCRUB_HTML)
    assert result["state"] in {"matches", "thin_corpus"}
    fam_ids = [f["id"] for f in result["families"]]
    assert fam_ids[0] == "floor_scrub"
    assert any(j.get("tape_family") == "scrub" or "scrub" in (j["title"] or "").lower() for j in result["jobs"])


def test_opaque_page_could_not_understand():
    result = match_robot_url("https://example.com/", html=OPAQUE_HTML)
    assert result["state"] == "could_not_understand"
    assert result["jobs"] == []


def test_chip_recovery_returns_jobs():
    result = match_from_chip("manipulates")
    assert result["state"] in {"matches", "thin_corpus"}
    assert len(result["jobs"]) > 0


def test_no_dexmate_hostname_shortcut():
    """Hostname alone must not unlock matches without capability evidence."""
    profile = build_capability_profile(text="https://dexmate.ai/", robot_name="Dexmate")
    # URL string alone shouldn't invent dual-arm / dexterous
    keys = {c.key for c in profile.capabilities}
    assert "dual_arm" not in keys
    assert "dexterous" not in keys
