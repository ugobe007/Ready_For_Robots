"""Source-only Critic: Diligent is healthcare, not a humanoid empty FIND.

Agent-verify / pstack-release install pytest only. Do not import
robot_job_search here. Live compose coverage stays in
test_healthcare_class_jobs.py.
"""
from pathlib import Path

from app.services.pstack_protocol import critic_gate_ids, critic_heldout_find_urls
from scripts.pstack_release import DILIGENT, REQUIRED_CRITIC_GATE_IDS, healthcare_class_fixture

ROOT = Path(__file__).resolve().parents[1]


def test_critic_gate_ids_keep_prior_gates_and_add_healthcare():
    assert tuple(critic_gate_ids()) == REQUIRED_CRITIC_GATE_IDS
    assert critic_gate_ids()[-1] == "healthcare_class"
    for gate in (
        "find",
        "find_abort",
        "find_identity",
        "crm_leftover",
        "job_cards",
        "wall",
        "matcher",
        "oem_extract",
        "class_picker",
    ):
        assert gate in critic_gate_ids()


def test_heldout_includes_diligentrobots():
    urls = critic_heldout_find_urls()
    assert any("diligentrobots.com" in u for u in urls)
    assert DILIGENT in urls


def test_healthcare_class_fixture_passes_on_this_tree():
    ok, detail = healthcare_class_fixture()
    assert ok, detail


def test_fixture_fails_when_diligent_catalog_is_humanoid(monkeypatch):
    import scripts.pstack_release as rel

    monkeypatch.setattr(rel, "_diligent_catalog_classes", lambda: ["humanoid"])
    ok, detail = rel.healthcare_class_fixture()
    assert ok is False
    assert "humanoid" in detail.lower()


def test_fixture_fails_when_healthcare_tile_missing(monkeypatch):
    import scripts.pstack_release as rel

    monkeypatch.setattr(
        rel,
        "_ts_class_option_ids",
        lambda _src: [
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
        ],
    )
    ok, detail = rel.healthcare_class_fixture()
    assert ok is False
    assert "tile" in detail.lower() or "healthcare" in detail.lower()


def test_diligent_catalog_source_is_not_humanoid():
    import json

    from scripts.pstack_release import _diligent_catalog_classes

    classes = _diligent_catalog_classes()
    assert classes
    assert "humanoid" not in classes
    assert any(c == "healthcare" for c in classes)
    seed = json.loads(
        (ROOT / "app" / "data" / "vendor_robots_oem_sku_seed.json").read_text(
            encoding="utf-8"
        )
    )
    lineup = json.loads(
        (
            ROOT
            / "readyforrobots-new"
            / "client"
            / "src"
            / "lib"
            / "knownOemLineups.json"
        ).read_text(encoding="utf-8")
    )
    vendors = seed.get("vendors") if isinstance(seed, dict) else seed
    diligent = next(
        v
        for v in vendors
        if isinstance(v, dict)
        and "diligentrobots.com" in " ".join(str(d) for d in (v.get("domains") or []))
    )
    moxi = next(r for r in diligent["robots"] if r.get("name") == "Moxi")
    assert moxi.get("primary_class") == "healthcare"
    assert moxi.get("primary_class") != "humanoid"
    client = lineup["diligentrobots.com"]["robots"][0]
    assert client.get("display_class") == "healthcare"
    assert client.get("display_class") != "humanoid"
    assert client.get("name") == "Moxi"

