"""Visual class + operator qualification so Jobs never dead-ends on thin evidence."""
from __future__ import annotations

from pathlib import Path

from app.services.robot_capability_derive import derive_capabilities
from app.services.robot_class_qualify import (
    apply_asserted_class,
    public_class_options,
    thin_class_profile,
)
from app.services.robot_job_search import compose_robot_job_search
from app.services.robot_profile_cache import clear_profile_cache_memory
from app.services.robot_requirement_match import match_jobs_from_profile
from app.services.robot_visual_class import classify_image_hints
from app.services.zero_state import INSUFFICIENT_PROFILE_EVIDENCE


def setup_function():
    clear_profile_cache_memory()


def test_photo_alt_humanoid_classifies_without_sku_name():
    hit = classify_image_hints(
        [("https://cdn.example.com/hero.webp", "bipedal humanoid robot standing")],
        page_text="Home robot",
    )
    assert hit is not None
    assert hit[0] == "humanoid"


def test_filename_neo_does_not_force_humanoid():
    """Avidbots Neo is a scrubber. 'neo' in a filename is not morphology."""
    hit = classify_image_hints(
        [("https://cdn.example.com/neo-hero.png", "autonomous floor scrubber")],
        page_text="",
    )
    assert hit is not None
    assert hit[0] == "autonomous_scrubber"


def test_apply_asserted_humanoid_derives_manipulate():
    profile = {
        "company": {"name": "1X"},
        "selected_product": {"name": "NEO"},
        "facts": [{"predicate": "payload_kg", "value": 18, "epistemic": "explicit"}],
        "coverage_level": "low",
    }
    out = apply_asserted_class(profile, "humanoid")
    caps = derive_capabilities(out)
    assert caps["manipulate"].present is True
    classes = {
        str(f.get("value")).lower()
        for f in out["facts"]
        if f.get("predicate") == "product_class"
    }
    assert "humanoid" in classes


def test_apply_asserted_amr_derives_transport():
    profile = {
        "company": {"name": "Locus"},
        "selected_product": {"name": "Origin"},
        "facts": [],
        "coverage_level": "low",
    }
    out = apply_asserted_class(profile, "amr")
    caps = derive_capabilities(out)
    assert caps["transport"].present is True


def test_compose_thin_profile_asks_for_class_not_insufficient_copy(monkeypatch):
    thin = {
        "company": {"name": "1X"},
        "selected_product": {"name": "NEO", "display_class": None},
        "products": [{"name": "NEO"}],
        "needs_product_choice": False,
        "facts": [{"predicate": "payload_kg", "value": 18, "epistemic": "explicit"}],
        "sources": [{"url": "https://www.1x.tech/neo"}],
        "coverage_level": "low",
        "profile_confidence": "C",
        "preview_images": ["https://cdn.example.com/neo.jpg"],
    }

    class _Obj:
        def to_dict(self):
            return thin

    monkeypatch.setattr(
        "app.services.robot_job_search.build_robot_profile",
        lambda *a, **k: _Obj(),
    )
    monkeypatch.setattr(
        "app.services.robot_job_search.assert_public_http_url", lambda u: u
    )
    monkeypatch.setattr(
        "app.services.robot_job_search.match_jobs_from_profile",
        lambda *a, **k: {
            "state": "could_not_understand",
            "robot_name": "NEO",
            "company_name": "1X",
            "capabilities": [],
            "families": [],
            "jobs": [],
            "job_count": 0,
            "matcher": "requirement_v1",
            "robot_class": None,
        },
    )
    out = compose_robot_job_search("https://www.1x.tech/neo")
    assert out["state"] == "qualify_robot"
    assert out["zero_reason"] is None
    assert out["zero_reason"] != INSUFFICIENT_PROFILE_EVIDENCE
    assert out["needs_class_choice"] is True
    ids = {row["id"] for row in out["class_options"]}
    assert "humanoid" in ids
    assert "amr" in ids
    assert out["preview_image_url"] == "https://cdn.example.com/neo.jpg"


def test_compose_asserted_humanoid_rematches(monkeypatch):
    thin = {
        "company": {"name": "1X"},
        "selected_product": {"name": "NEO"},
        "products": [{"name": "NEO"}],
        "needs_product_choice": False,
        "facts": [],
        "sources": [],
        "coverage_level": "low",
        "profile_confidence": "C",
    }

    class _Obj:
        def to_dict(self):
            return thin

    monkeypatch.setattr(
        "app.services.robot_job_search.build_robot_profile",
        lambda *a, **k: _Obj(),
    )
    monkeypatch.setattr(
        "app.services.robot_job_search.assert_public_http_url", lambda u: u
    )

    seen = {}

    def _match(profile, **k):
        seen["facts"] = list(profile.get("facts") or [])
        return {
            "state": "matches",
            "robot_name": "NEO",
            "company_name": "1X",
            "capabilities": [{"key": "manipulate", "label": "manipulation"}],
            "families": [],
            "jobs": [{"job_key": "cnc_load", "title": "Load a CNC"}],
            "job_count": 12,
            "matcher": "requirement_v1",
            "robot_class": "humanoid",
        }

    monkeypatch.setattr(
        "app.services.robot_job_search.match_jobs_from_profile", _match
    )
    out = compose_robot_job_search("https://www.1x.tech/neo", asserted_class="humanoid")
    assert any(
        f.get("predicate") == "product_class" and f.get("value") == "humanoid"
        for f in seen["facts"]
    )
    assert out["state"] == "matches"
    assert out["needs_class_choice"] is False
    assert out["job_count"] == 12


def test_asserted_humanoid_profile_matches_jobs():
    """Operator class is enough to rematch — never a dead-end copy."""
    profile = apply_asserted_class(
        {
            "company": {"name": "1X"},
            "selected_product": {"name": "NEO"},
            "facts": [],
            "coverage_level": "low",
        },
        "humanoid",
    )
    out = match_jobs_from_profile(profile)
    assert out["state"] == "matches"
    assert out["job_count"] > 0
    assert any(c.get("key") == "manipulate" for c in out["capabilities"])


def test_agtonomy_class_picker_agriculture_is_not_a_noop():
    """Incomplete identity + Agriculture must search, not re-open the picker."""
    out = compose_robot_job_search(
        "https://www.agtonomy.com/",
        asserted_class="agriculture",
        lookup_grain="robot_type",
    )
    assert out["needs_class_choice"] is False
    assert out["state"] != "qualify_robot"
    if out.get("job_count"):
        families = {j.get("tape_family") for j in out.get("jobs") or []}
        assert "agriculture" in families
        titles = " ".join(str(j.get("title") or "") for j in out.get("jobs") or []).lower()
        assert "weed" in titles or "crop" in titles or "field" in titles or "harvest" in titles
    else:
        assert out.get("zero_reason")


def test_incomplete_identity_asserted_agriculture_does_not_swallow(monkeypatch):
    """Product-grain unknown OEM used to return qualify_robot and drop the class."""
    thin = {
        "company": {"name": "Agtonomy"},
        "selected_product": None,
        "products": [],
        "needs_product_choice": False,
        "facts": [],
        "sources": [],
        "coverage_level": "low",
        "profile_confidence": "C",
    }

    class _Obj:
        def to_dict(self):
            return thin

    monkeypatch.setattr(
        "app.services.robot_job_search.build_robot_profile",
        lambda *a, **k: _Obj(),
    )
    monkeypatch.setattr(
        "app.services.robot_job_search.assert_public_http_url", lambda u: u
    )
    out = compose_robot_job_search(
        "https://agtonomy.com/",
        asserted_class="agriculture",
        lookup_grain="product",
    )
    assert out["needs_class_choice"] is False
    assert out["state"] != "qualify_robot"
    assert (out.get("job_count") or 0) > 0 or out.get("zero_reason")


def test_asserted_class_zero_jobs_does_not_reopen_picker(monkeypatch):
    thin = {
        "company": {"name": "Agtonomy"},
        "selected_product": None,
        "products": [],
        "needs_product_choice": False,
        "facts": [],
        "sources": [],
        "coverage_level": "low",
        "profile_confidence": "C",
    }

    class _Obj:
        def to_dict(self):
            return thin

    monkeypatch.setattr(
        "app.services.robot_job_search.build_robot_profile",
        lambda *a, **k: _Obj(),
    )
    monkeypatch.setattr(
        "app.services.robot_job_search.assert_public_http_url", lambda u: u
    )
    monkeypatch.setattr(
        "app.services.robot_job_search.match_jobs_from_profile",
        lambda *a, **k: {
            "state": "could_not_understand",
            "robot_name": "Agtonomy",
            "company_name": "Agtonomy",
            "capabilities": [],
            "families": [],
            "jobs": [],
            "job_count": 0,
            "matcher": "requirement_v1",
            "robot_class": "agriculture",
        },
    )
    out = compose_robot_job_search(
        "https://www.agtonomy.com/",
        asserted_class="agriculture",
        lookup_grain="product",
    )
    assert out["needs_class_choice"] is False
    assert out["state"] != "qualify_robot"
    assert out["job_count"] == 0


def test_thin_humanoid_class_matches_jobs_without_sku():
    """Type-first: product_class is enough. Matcher still inspects requirements."""
    profile = thin_class_profile("Fourier Intelligence", "humanoid")
    classes = {
        str(f.get("value")).lower()
        for f in profile["facts"]
        if f.get("predicate") == "product_class"
    }
    assert "humanoid" in classes
    out = match_jobs_from_profile(profile)
    assert out["state"] == "matches"
    assert out["job_count"] > 0
    assert any(c.get("key") == "manipulate" for c in out["capabilities"])


def test_jobs_ui_never_renders_insufficient_evidence_copy():
    text = Path(
        "readyforrobots-new/client/src/components/RobotJobsWorkspace.tsx"
    ).read_text()
    banned = "we found _____, but we couldn't establish enough capability evidence to match it confidently"
    assert banned not in text.lower()
    assert "couldn't establish enough capability evidence" not in text.lower()
    assert "ClassPicker" in text
    assert "Name the robot class" in text
    assert "CLASS_PICKER_PROMPT" in text
    assert "What kind of robot is" not in text
    assert "kid of robot" not in text.lower()


def test_public_class_options_include_ten_classes():
    rows = public_class_options()
    ids = [row["id"] for row in rows]
    assert ids == [
        "humanoid",
        "amr",
        "mobile_manipulator",
        "cobot",
        "quadruped",
        "autonomous_scrubber",
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
        "food_prep",
    ]
    assert len(rows) == 18
    for row in rows:
        assert row["label"].strip()
        assert row["hint"].strip()
    by_id = {row["id"]: row for row in rows}
    assert "tractor" in by_id["agriculture"]["hint"].lower() or "combine" in by_id["agriculture"]["hint"].lower()
    assert "hull" in by_id["marine"]["hint"].lower()
    assert "drone" in by_id["avionics"]["hint"].lower()
    assert "evtol" in by_id["avionics"]["hint"].lower()
    assert "satellite" in by_id["aerospace"]["hint"].lower()
    assert "home" in by_id["construction"]["hint"].lower() or "building" in by_id["construction"]["hint"].lower()
    assert "hospital" in by_id["healthcare"]["hint"].lower()
    assert "haul" in by_id["mining"]["hint"].lower() or "pit" in by_id["mining"]["hint"].lower()
    assert "fulfillment" in by_id["warehouse"]["hint"].lower()
    assert "hotel" in by_id["hospitality"]["hint"].lower()
    assert "food prep" not in by_id["hospitality"]["hint"].lower()
    assert "make-line" in by_id["food_prep"]["hint"].lower() or "bowl" in by_id["food_prep"]["hint"].lower()
