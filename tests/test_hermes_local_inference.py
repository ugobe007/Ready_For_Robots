"""Local inference overlay mapping (no LLM, no DB)."""
from types import SimpleNamespace

from app.services.hermes_local_inference import overlay_from_dossier


def test_overlay_from_dossier_maps_labor_and_fit():
    dossier = SimpleNamespace(
        is_lead=True,
        junk_reason=None,
        specific_problem="Labor shortage in the warehouse",
        why_lead=["AMR tote language", "RFP in Q3"],
        robot_categories=["amr", "palletizer"],
        intent_score=74.4,
        lead_value_score=80,
        tier="WARM",
    )
    overlay = overlay_from_dossier(dossier)
    assert overlay["engine"] == "lead_inference_engine"
    assert overlay["automation_fit"] == 74
    assert overlay["labor_intensity"] == "high"
    assert overlay["facility_clarity"] == "named_site"
    assert overlay["blockers"] == []
    assert overlay["vendor_shortlist"] == []
    assert overlay["rationale"] == "Labor shortage in the warehouse"


def test_overlay_from_dossier_junk_sets_blocker():
    dossier = SimpleNamespace(
        is_lead=False,
        junk_reason="listicle_headline",
        specific_problem="",
        why_lead=[],
        robot_categories=[],
        intent_score=0,
        lead_value_score=0,
        tier="COLD",
    )
    overlay = overlay_from_dossier(dossier)
    assert overlay["automation_fit"] == 0
    assert "listicle_headline" in overlay["blockers"]
