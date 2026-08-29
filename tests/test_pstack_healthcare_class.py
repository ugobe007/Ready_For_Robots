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


def test_diligent_catalog_source_is_not_humanoid():
    from scripts.pstack_release import _diligent_catalog_classes

    classes = _diligent_catalog_classes()
    assert classes
    assert "humanoid" not in classes
    assert any(c == "healthcare" for c in classes)
    seed = (ROOT / "app" / "data" / "vendor_robots_oem_sku_seed.json").read_text(
        encoding="utf-8"
    )
    lineup = (
        ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "knownOemLineups.json"
    ).read_text(encoding="utf-8")
    assert "diligentrobots.com" in seed
    assert '"primary_class": "healthcare"' in seed
    assert '"display_class": "healthcare"' in lineup
    diligent_slice = seed[seed.lower().index("diligent robotics") :]
    diligent_slice = diligent_slice[: diligent_slice.find('"vendor_name"')]
    assert "humanoid" not in diligent_slice.lower()
    assert "Moxi" in diligent_slice
