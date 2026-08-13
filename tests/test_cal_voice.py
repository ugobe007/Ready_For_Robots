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
    cal_buyer_email_signature,
    cal_persona_payload,
    cal_signature,
)


def test_cal_signature_includes_role():
    sig = cal_signature()
    assert sig.startswith("— Cal")
    assert f"\n{CAL_TITLE}, Ready For Robots" in sig
    assert cal_buyer_email_signature() == "Cal\nReadyForRobots"


def test_persona_payload_exports_voice_rules():
    payload = cal_persona_payload()
    assert payload["title"] == CAL_TITLE
    assert "automation opportunities" in payload["identity"].lower() or "find robots" in payload["identity"].lower()
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
    assert body.startswith("Hi Acme Logistics,") or body.startswith("Hi Acme team,")
    paragraphs = [p for p in body.split("\n\n") if p.strip()]
    opener = paragraphs[1].lower()
    assert opener.startswith("i'm cal with readyforrobots")
    assert "i've been looking at" in low
    assert "i'd be interested in your perspective" in low
    assert body.rstrip().endswith("ReadyForRobots")
    assert "Deployment Advisor" not in body
    assert len(body.split()) <= 280


def test_buyer_intro_first_paragraph_is_human():
    name = "Acme Logistics"
    for vid in BUYER_VARIANTS:
        body = build_buyer_variant_body(name, "Logistics", vid)
        paragraphs = [p for p in body.split("\n\n") if p.strip()]
        opener = paragraphs[1].strip().lower()
        assert opener.startswith("i'm cal with readyforrobots"), f"{vid} opener: {paragraphs[1][:90]}"


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
        for banned in CAL_BANNED_PHRASES:
            assert banned not in low, f"{vid} contains banned phrase: {banned}"


def test_bottleneck_first_matches_operator_pfg_example():
    body = build_buyer_variant_body(
        "Performance Food Group",
        "Food Distribution / Wholesale",
        "bottleneck_first",
    )
    expected = "\n".join([
        "Hi PFG team,",
        "",
        "I'm Cal with ReadyForRobots. I research how companies are using robotics and help identify jobs where automation could actually make a difference.",
        "",
        "I've been looking at food distribution, and I keep noticing something I wanted to check with you. Picking gets most of the attention, but a lot of the day-to-day pressure seems to happen elsewhere.",
        "",
        "Receiving and replenishment involve a lot of material movement, pallets have to move continuously through the operation, and inventory exceptions and returns create work that doesn't always fit neatly into the normal warehouse flow. Those are often the places where people end up filling the gaps.",
        "",
        "I'm curious if that's true at PFG.",
        "",
        "Where do you see the biggest opportunity to automate today? Is it still picking, or are there other parts of the operation that cause more problems?",
        "",
        "I'd be interested in your perspective.",
        "",
        "Cal",
        "ReadyForRobots",
    ])
    assert body == expected
