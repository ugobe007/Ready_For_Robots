"""Phase 2 — context-aware opener grounding.

Cal may cite a verifiable, company-specific reason for reaching out, but only
when there's real signal text to stand behind. No signal → no reason line →
the clean industry opener is unchanged. Any injected reason must still clear
the completeness guard and carry none of the banned AI tells.
"""
from app.services.agent_messaging import (
    BUYER_VARIANTS,
    build_buyer_variant_body,
    build_context_reason,
)
from app.services.cal_draft_guard import is_complete_cal_draft

_AI_TELLS = ("honest", "genuinely", "i'd love", "hope you're well", "circling back", "just bumping")


def test_reason_none_without_signal():
    assert build_context_reason("Acme Logistics", "") is None
    assert build_context_reason("Acme Logistics", "   ") is None
    assert build_context_reason("", "Acme is opening a new distribution center in Dallas.") is None


def test_reason_none_for_low_quality_blob():
    # Too short / junk-y text should not become a cited reason.
    assert build_context_reason("Acme", "http://x http://y") is None
    assert build_context_reason("Acme", "aligns with our signals") is None


def test_reason_rejects_inference_prose_without_event():
    # Synthesized category prose is not a verifiable event — reciting it back
    # reads as assumptive/naive, which is exactly what we must avoid.
    blob = (
        "Harvard Maintenance, a large Facilities Services operator, sits in a "
        "sector facing acute front-line labor shortages that are pushing "
        "operators to consider automation."
    )
    assert build_context_reason("Harvard Maintenance", blob) is None


def test_reason_grounded_and_names_company():
    fact = "Acme Logistics is opening a new 500,000 sq ft distribution center in Dallas this fall."
    reason = build_context_reason("Acme Logistics", fact)
    assert reason is not None
    assert "Acme Logistics" in reason
    # It should quote the real fact, not invent one.
    assert "distribution center" in reason
    low = reason.lower()
    for tell in _AI_TELLS:
        assert tell not in low, f"reason regressed AI tell: {tell}"


def test_reason_handles_fact_without_company_name():
    fact = "A 300-person hiring push for automation engineers was posted this quarter."
    reason = build_context_reason("Globex", fact)
    assert reason is not None
    assert "Globex" in reason
    assert "automation engineers" in reason


def test_variant_without_reason_unchanged():
    for vid in BUYER_VARIANTS:
        base = build_buyer_variant_body("Acme Logistics", "Logistics", vid)
        with_none = build_buyer_variant_body("Acme Logistics", "Logistics", vid, reason=None)
        assert base == with_none


def test_variant_with_reason_injects_and_stays_complete():
    fact = "Acme Logistics is opening a new distribution center in Dallas this fall."
    reason = build_context_reason("Acme Logistics", fact)
    assert reason is not None
    for vid in BUYER_VARIANTS:
        body = build_buyer_variant_body("Acme Logistics", "Logistics", vid, reason=reason)
        assert reason in body, f"{vid} did not inject the reason"
        # Reason lands after the greeting, before Cal's vantage line.
        assert body.startswith("Hi,\n\n" + reason)
        full = f"Subject: what actually holds up\n\n{body}"
        ok, why = is_complete_cal_draft(full)
        assert ok, f"{vid} with reason failed guard: {why}"
        low = body.lower()
        for tell in _AI_TELLS:
            assert tell not in low, f"{vid} regressed AI tell with reason: {tell}"
