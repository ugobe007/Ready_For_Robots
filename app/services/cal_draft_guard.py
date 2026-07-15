"""Validate Cal outreach drafts before save/send — blocks truncated admin previews."""
from __future__ import annotations

import re

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


def draft_needs_regeneration(draft: str | None, *, account_type: str = "buyer") -> tuple[bool, str]:
    """Detect truncated previews or buyer/vendor template mismatches."""
    ok, reason = is_complete_cal_draft(draft)
    if not ok:
        return True, reason
    low = (draft or "").lower()
    at = (account_type or "buyer").lower()
    if at == "buyer" and any(p in low for p in _WRONG_BUYER_PHRASES):
        return True, "Buyer account has vendor-facing draft — regenerating"
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
