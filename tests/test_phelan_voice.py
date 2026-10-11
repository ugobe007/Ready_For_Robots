"""Cal voice rules — signature, banned phrases, and buyer intro shape."""
from app.services.agent_messaging import (
    BUYER_VARIANTS,
    build_buyer_variant_body,
)
from app.services.phelan_assembly_agent import assemble_buyer_outreach
from app.services.phelan_draft_guard import is_complete_cal_draft
from app.services.phelan_persona import (
    CAL_ALWAYS,
    PHELAN_BANNED_PHRASES,
    CAL_NEVER,
    CAL_TITLE,
    phelan_buyer_email_signature,
    cal_persona_payload,
    phelan_signature,
)


def test_cal_signature_includes_role():
    sig = phelan_signature()
    assert sig.startswith("— Phelan")
    assert CAL_TITLE == "Robot Coordinator"
    assert f"\n{CAL_TITLE}, Ready For Robots" in sig
    buyer_sig = phelan_buyer_email_signature()
    assert "Robot Coordinator | Ready For Robots" in buyer_sig
    assert "phelan@readyforrobots.com" in buyer_sig
    assert "Cal" not in buyer_sig


def test_persona_payload_exports_voice_rules():
    payload = cal_persona_payload()
    assert payload["title"] == CAL_TITLE
    ident = payload["identity"].lower()
    assert "jobs recruiter" in ident or "jobs advisor" in ident or "robot jobs" in ident or "job cards" in ident
    assert "problem" in payload["identity"].lower() or "task" in payload["mission"].lower()
    assert len(payload["always"]) == len(CAL_ALWAYS)
    assert len(payload["never"]) >= len(CAL_NEVER)
    assert "signature_example" in payload
    body = build_buyer_variant_body("Acme Logistics", "Logistics", "workflow_first").lower()
    assert "poc trial" not in body
    assert "help customers find" not in body


def test_workflow_first_matches_observation_led_shape():
    body = build_buyer_variant_body("Acme Logistics", "Logistics", "workflow_first")
    low = body.lower()
    assert body.startswith("Hi _______, nice to meet you.")
    assert "i am a robot coordinator for readyforrobots" in low
    assert "may i send them to you for review?" in low
    assert "i've been looking at" not in low
    assert body.rstrip().endswith("Phelan.")
    assert "Deployment Advisor" not in body
    assert len(body.split()) <= 280


def test_buyer_intro_first_paragraph_is_human():
    name = "Acme Logistics"
    for vid in BUYER_VARIANTS:
        body = build_buyer_variant_body(name, "Logistics", vid)
        assert body.startswith("Hi _______, nice to meet you."), vid
        assert "I am a Robot Coordinator for ReadyForRobots" in body


def test_long_name_anchor_keeps_greeting_first():
    name = "UPS Supply Chain Solutions"
    body = build_buyer_variant_body(name, "Logistics", "workflow_first")
    lines = [ln for ln in body.splitlines() if ln.strip()]
    assert lines[0].startswith("Hi ")
    assert "UPS" in lines[0] or "UPS" in body
    assert "UPS" in body


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
        for banned in PHELAN_BANNED_PHRASES:
            assert banned not in low, f"{vid} contains banned phrase: {banned}"


def test_bottleneck_first_matches_operator_pfg_example():
    body = build_buyer_variant_body(
        "Performance Food Group",
        "Food Distribution / Wholesale",
        "bottleneck_first",
    )
    assert body.startswith("Hi _______, nice to meet you.")
    assert "I am a Robot Coordinator for ReadyForRobots" in body
    assert "I help find robots for automation jobs" in body
    assert "at Performance Food Group" in body
    assert "May I send them to you for review?" in body
    assert body.endswith("Phelan.")
    assert "I've been looking" not in body
    assert "I'd be interested in your perspective" not in body
