"""Cal voice rules — signature, banned phrases, and buyer intro shape."""
from app.services.agent_messaging import (
    BUYER_VARIANTS,
    build_buyer_variant_body,
)
from app.services.cal_assembly_agent import assemble_buyer_outreach
from app.services.cal_draft_guard import is_complete_cal_draft
from app.services.cal_persona import (
    CAL_ALWAYS,
    CAL_BANNED_PHRASES,
    CAL_NEVER,
    CAL_TITLE,
    cal_persona_payload,
    cal_signature,
)


def test_cal_signature_includes_role():
    sig = cal_signature()
    assert sig.startswith("— Cal")
    assert f"\nCal\n{CAL_TITLE}\nReady For Robots" in sig


def test_persona_payload_exports_voice_rules():
    payload = cal_persona_payload()
    assert payload["title"] == CAL_TITLE
    assert len(payload["always"]) == len(CAL_ALWAYS)
    assert len(payload["never"]) >= len(CAL_NEVER)
    assert "signature_example" in payload


def test_workflow_first_matches_observation_led_shape():
    body = build_buyer_variant_body("Acme Logistics", "Logistics", "workflow_first")
    low = body.lower()
    assert "which robot should we buy" in low
    assert "which workflow is costing acme logistics" in low
    assert "vendor-neutral" in low
    assert "worth a quick call" not in low
    assert "i spend my days" not in low
    assert body.endswith("Ready For Robots")
    assert "Deployment Advisor" in body


def test_buyer_variants_pass_assembly_without_banned_phrases():
    name = "Globex Logistics"
    for vid in BUYER_VARIANTS:
        body = build_buyer_variant_body(name, "Logistics", vid)
        full = f"Subject: test\n\n{body}"
        ok, reason = is_complete_cal_draft(full)
        assert ok, f"{vid} incomplete: {reason}"
        result = assemble_buyer_outreach(company_name=name, subject="test", body=body)
        assert result.approved, f"{vid} assembly issues: {result.issues}"
        low = body.lower()
        for banned in CAL_BANNED_PHRASES:
            assert banned not in low, f"{vid} contains banned phrase: {banned}"
