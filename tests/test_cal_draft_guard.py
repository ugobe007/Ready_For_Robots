from app.services.agent_messaging import (
    BUYER_VARIANTS,
    build_buyer_variant_body,
    buyer_variant_subject,
    pick_buyer_variant,
)
from app.services.cal_assembly_agent import assemble_buyer_outreach
from app.services.cal_autonomy import cal_buyer_outreach_body
from app.services.cal_draft_guard import draft_needs_regeneration, is_complete_cal_draft, is_legacy_cal_draft, parse_cal_draft_or_raise

_THEATER = (
    "innovation theater",
    "carpet demo",
    "where the money hides",
    "annoyingly picky",
    "quietly dies",
    'reply "send it"',
)


class _FakeCompany:
    def __init__(self, name: str, industry: str = "Logistics", company_id: int | None = None):
        self.name = name
        self.industry = industry
        self.id = company_id


def test_truncated_preview_rejected():
    truncated = (
        "Subject: quick question about UPS Supply Chain Solutions's ops\n\n"
        "Hi — Cal from Ready For Robots.\n\n"
        "I help ops teams narrow the robotics vendor field. We monitor public signals — labor pressu"
    )
    ok, reason = is_complete_cal_draft(truncated)
    assert not ok
    assert "short" in reason.lower() or "mid-sentence" in reason.lower()


def test_every_buyer_variant_passes_guard_and_assembly():
    # All three trust-first angles must clear the completeness guard, the assembly
    # gate (company name in body), and never need regeneration on first draft.
    name = "UPS Supply Chain Solutions"
    for vid in BUYER_VARIANTS:
        subject = buyer_variant_subject(name, "Logistics", vid)
        body = build_buyer_variant_body(name, "Logistics", vid)
        full = f"Subject: {subject}\n\n{body}"
        ok, reason = is_complete_cal_draft(full)
        assert ok, f"{vid} failed guard: {reason}"
        assert name in body, f"{vid} missing company name"
        assert "— Cal" in body and "Ready For Robots" in body
        assert "Deployment Advisor" in body
        needs, _ = draft_needs_regeneration(full, account_type="buyer")
        assert not needs, f"{vid} wrongly flagged for regeneration"
        assert assemble_buyer_outreach(company_name=name, subject=subject, body=body).approved
        # Old surveillance framing must never reappear.
        low = full.lower()
        assert "we monitor" not in low and "watchlist" not in low


def test_buyer_variants_are_humble_not_presumptuous():
    # The whole point of the rewrite: don't diagnose their business. Each angle
    # must leave room for "not now" / "already tried" rather than asserting pain.
    name = "Acme Distribution"
    humility_markers = (
        "not yet",
        "vendor-neutral",
        "vendor neutral",
        "no pitch",
        "isn't very useful",
        "wrong problem",
        "wrong job",
        "right workflow",
        "actively exploring",
        "still deciding",
    )
    for vid in BUYER_VARIANTS:
        body = build_buyer_variant_body(name, "Logistics", vid).lower()
        for banned in _THEATER:
            assert banned not in body, f"{vid} regressed marketing theater: {banned}"
        assert any(m in body for m in humility_markers), f"{vid} reads presumptuous"


def test_buyer_variant_selection_is_deterministic_round_robin():
    assert pick_buyer_variant(0) == BUYER_VARIANTS[0]
    assert pick_buyer_variant(1) == BUYER_VARIANTS[1]
    assert pick_buyer_variant(2) == BUYER_VARIANTS[2]
    assert pick_buyer_variant(3) == BUYER_VARIANTS[0]
    # Same company id always resolves to the same angle (draft==send agreement).
    assert pick_buyer_variant(42) == pick_buyer_variant(42)
    # Rotation can be restricted to a subset (e.g. after retiring a loser).
    only = (BUYER_VARIANTS[0], BUYER_VARIANTS[2])
    assert pick_buyer_variant(1, allowed=only) in only


def test_cal_buyer_outreach_body_respects_explicit_variant():
    company = _FakeCompany("Globex Logistics", "Logistics", company_id=7)
    for vid in BUYER_VARIANTS:
        body = cal_buyer_outreach_body(company, variant_id=vid)
        assert body == build_buyer_variant_body("Globex Logistics", "Logistics", vid)


def test_legacy_ups_what_survives_draft():
    legacy = """Subject: the logistics robots still running six months in

Hi,

Part of my job surprises people: I don't track which robots demo well. I track which ones are still running six months after install.

— Cal
Ready For Robots"""
    assert is_legacy_cal_draft(legacy)
    needs, reason = draft_needs_regeneration(legacy, account_type="buyer")
    assert needs
    assert "legacy" in reason.lower()


def test_current_voice_not_legacy():
    body = build_buyer_variant_body("UPS Supply Chain Solutions", "Logistics", "what_survives")
    assert not is_legacy_cal_draft(body)
    needs, _ = draft_needs_regeneration(body, account_type="buyer")
    assert not needs


def test_wrong_vendor_pitch_on_buyer_needs_regeneration():
    vendor_pitch = (
        "Hey,\n\nCal here — I run the automation research desk at Ready For Robots.\n\n"
        "We track robot companies by deployment type and industry fit. Based on Hawaiian Airlines's profile, "
        "I have a short list of vendors worth a look.\n\n"
        "Want me to send over the shortlist? Quick reply is all it takes.\n\n"
        "— Cal\nReady For Robots"
    )
    needs, reason = draft_needs_regeneration(vendor_pitch, account_type="buyer")
    assert needs
    assert "vendor-facing" in reason or "legacy" in reason.lower()


def test_parse_cal_draft_or_raise_raises_on_truncated():
    truncated = "Subject: test\n\nHi — Cal from Ready For Robots.\n\nI help ops teams narrow the robotics vendor field. We monitor public signals — labor pressu"
    try:
        parse_cal_draft_or_raise(truncated, "Acme")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "short" in str(exc).lower() or "mid-sentence" in str(exc).lower()
