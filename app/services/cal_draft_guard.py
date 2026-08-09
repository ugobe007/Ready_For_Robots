"""Validate Cal outreach drafts before save/send — blocks truncated admin previews."""
from __future__ import annotations

import re

from app.services.cal_persona import CAL_BANNED_PHRASES

_MIN_DRAFT_CHARS = 280
_COMPLETE_MARKERS = (
    "worth a quick reply",
    "ready for robots",
    "— cal",
    "- cal",
    "deployment advisor",
    "automation advisor",
    "vendor-neutral",
    "vendor neutral",
    "explore timing",
    "book a",
    "discovery call",
    "reply — i'll send",
    "short list of vendors",
    "who to skip",
)
_TRUNCATED_TAIL = re.compile(r"\b\w{1,12}$")  # ends mid-word (no sentence punctuation)


def is_complete_cal_draft(draft: str | None) -> tuple[bool, str]:
    """Return (ok, reason). Rejects 140-char list previews and cut-off bodies."""
    text = (draft or "").strip()
    if not text:
        return False, "Draft is empty"
    if len(text) < _MIN_DRAFT_CHARS:
        return False, f"Draft too short ({len(text)} chars) — likely a truncated preview"
    low = text.lower()
    if not any(marker in low for marker in _COMPLETE_MARKERS):
        return False, "Draft missing Cal sign-off — looks incomplete"
    # Subject + body previews often end mid-word after "labor pressu"
    body = text
    if low.startswith("subject:"):
        parts = text.split("\n\n", 1)
        body = parts[1] if len(parts) > 1 else ""
    body = body.strip()
    if body and not body.endswith((".", "?", "!", "—", "-")):
        last_line = body.splitlines()[-1].strip()
        if _TRUNCATED_TAIL.match(last_line) and len(text) < 400:
            return False, "Draft ends mid-sentence — regenerate before sending"
    return True, "ok"


_WRONG_BUYER_PHRASES = (
    "automation research desk",
    "track robot companies by deployment",
    "i have a short list of vendors worth a look",
)
_WRONG_VENDOR_PHRASES = (
    "worth a quick reply to explore timing",
    "we've identified",
)

# Older CTA variants that should be force-refreshed in saved drafts.
_STALE_CTA_MARKERS = (
    "if your team has active rfqs or bid projects for this workflow",
    "if your team has rfqs or bid projects for this workflow",
    "reply with the rfq/bid package and project specs",
    "i'll help route the right follow-up",
    "i'll hand it directly to robert for follow-up",
    "i'll hand this directly to robert today",
)

# Pre–voice-rewrite templates (v2) — still stored on many CRM accounts.
_LEGACY_VOICE_MARKERS = (
    "part of my job surprises people",
    "i spend my days looking at where robot",
    "one pattern keeps showing up",
    "if robotics is on the roadmap",
    "no presentation, just a practical conversation",
    "if it's worth a short exchange",
    "we're vendor-neutral, so i care about fit",
    "i'll tell you what's actually holding up in the field",
    "my job is to help companies find robots that actually fit their workflow",
    "something i notice on site visits: six months after install",
    "the ones that last almost never won on spec-sheet speed",
    "is warehouse automation something",
)


def is_legacy_cal_draft(draft: str | None) -> bool:
    """True when body uses pre-v3 Cal sales voice or old two-line signature."""
    text = (draft or "").strip()
    if not text:
        return False
    low = text.lower()

    # New voice always signs with role line.
    if "— cal" in low and "ready for robots" in low:
        if "deployment advisor" not in low and "automation advisor" not in low:
            return True

    # Old three-line sign-off style now replaced by one compact role line.
    if "\ncal\ndeployment advisor\nready for robots" in low:
        return True

    for phrase in CAL_BANNED_PHRASES:
        if phrase in low:
            return True
    return any(marker in low for marker in _LEGACY_VOICE_MARKERS)


def draft_needs_regeneration(draft: str | None, *, account_type: str = "buyer") -> tuple[bool, str]:
    """Detect truncated previews, template mismatches, or legacy Cal voice."""
    from app.services.brand import BRAND_STAGEGATE, content_brand

    if is_legacy_cal_draft(draft):
        return True, "Legacy Cal voice — redrafting with current templates"
    at = (account_type or "buyer").lower()
    if at == "buyer" and content_brand(draft) == BRAND_STAGEGATE:
        return True, "Buyer account has StageGate-branded draft — regenerating"
    ok, reason = is_complete_cal_draft(draft)
    if not ok:
        return True, reason
    low = (draft or "").lower()
    if at == "buyer" and any(p in low for p in _WRONG_BUYER_PHRASES):
        return True, "Buyer account has vendor-facing draft — regenerating"
    if at == "buyer":
        try:
            from app.services.agent_messaging import BUYER_OUTREACH_CTA

            current_cta = (BUYER_OUTREACH_CTA or "").strip().lower()
        except Exception:
            current_cta = ""
        has_stale_cta = any(marker in low for marker in _STALE_CTA_MARKERS)
        if has_stale_cta and (not current_cta or current_cta not in low):
            return True, "Buyer draft has stale CTA — regenerating"
    if at == "vendor" and any(p in low for p in _WRONG_VENDOR_PHRASES) and "buyer lead" not in low:
        return True, "Vendor account has buyer-facing draft — regenerating"
    return False, "ok"


def parse_cal_draft_or_raise(draft: str | None, fallback_name: str) -> tuple[str, str]:
    """Parse subject/body and reject incomplete stored drafts."""
    from app.services.cal_outreach_send import parse_cal_draft

    ok, reason = is_complete_cal_draft(draft)
    if not ok:
        raise ValueError(reason)
    return parse_cal_draft(draft, fallback_name)
