"""Validate Phelan outreach drafts before save/send — blocks truncated admin previews."""
from __future__ import annotations

import re

from app.services.phelan_persona import PHELAN_BANNED_PHRASES

_MIN_DRAFT_CHARS = 280
_COMPLETE_MARKERS = (
    "worth a quick reply",
    "ready for robots",
    "readyforrobots",
    "phelan",
    "robot job analyst",
    "i'm phelan",
    "i’m phelan",
    "— phelan",
    "- phelan",
    "\nphelan\n",
    "— cal",
    "- cal",
    "\ncal\n",
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
    "jobs robots can actually do well",
    "i'd be interested in your perspective",
    "i'm cal with readyforrobots",
    "robot coordinator",
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


_STALE_VOICE_MARKERS = (
    "i'm cal",
    "i am cal",
    "this is cal",
    "hi, i am cal",
    "deployment advisor",
    "robot job analyst",
    "robot placement specialist",
    "ai robotics placement specialist",
)


def is_legacy_cal_draft(draft: str | None) -> bool:
    """True when the body still uses the Cal name or an older title."""
    text = (draft or "").strip()
    if not text:
        return False
    low = text.lower()

    if any(marker in low for marker in _STALE_VOICE_MARKERS):
        return True
    if re.search(r"(?m)^[—-]?\s*cal\s*$", low):
        return True

    # Current letter: Phelan, titled Robot Coordinator.
    if "phelan" in low and "robot coordinator" in low:
        return any(marker in low for marker in _LEGACY_VOICE_MARKERS)

    for phrase in PHELAN_BANNED_PHRASES:
        if phrase in low:
            return True
    return any(marker in low for marker in _LEGACY_VOICE_MARKERS)


# Letters that ignore the operator-approved first touch. Name and title alone
# are not enough — these lines are a different message.
_OFF_INSTRUCTION_MARKERS = (
    "following up on task feasibility",
    "one field note",
    "something i'm seeing",
    "vendor-neutral",
    "evaluate physical task feasibility",
    "before vendor pocs",
    "before vendor poc",
    "i spend my time studying",
    "i spend my days",
    "we've identified",
    "we’ve identified",
    "one practical note, then one question",
    "robot job analyst",
    "robot placement specialist",
    "recruitment and placement infrastructure",
    "i work with logistics teams on one thing",
    "i work with hospitality teams on one thing",
    "i work with healthcare",
    "i work with food teams on one thing",
    "leadership team",
)


def buyer_letter_obeys_instructions(draft: str | None) -> tuple[bool, str]:
    """The operator letter: who Phelan is, what he has been looking at, one question, their perspective."""
    text = (draft or "").strip()
    if not text:
        return False, "Draft is empty"
    low = text.lower()
    for marker in _OFF_INSTRUCTION_MARKERS:
        if marker in low:
            return False, f"Draft violates operator instructions ({marker})"
    if "i'd be interested in your perspective" not in low and "i’d be interested in your perspective" not in low:
        return False, "Draft missing the approved close"
    has_frame = "i've been looking" in low or "i’ve been looking" in low
    has_identity = (
        "i research how companies are using robotics" in low
        or "this is phelan again" in low
    )
    if not has_frame or not has_identity:
        return False, "Draft missing the approved introduction"
    if "phelan" not in low or "robot coordinator" not in low:
        return False, "Draft missing Phelan, Robot Coordinator"
    return True, "ok"


def draft_needs_regeneration(draft: str | None, *, account_type: str = "buyer") -> tuple[bool, str]:
    """Detect truncated previews, template mismatches, or legacy Cal voice."""
    from app.services.brand import BRAND_STAGEGATE, content_brand

    at = (account_type or "buyer").lower()
    if at == "buyer" and content_brand(draft) == BRAND_STAGEGATE:
        return True, "Buyer account has StageGate-branded draft — regenerating"
    if is_legacy_cal_draft(draft):
        return True, "Legacy Cal voice — redrafting with current templates"
    ok, reason = is_complete_cal_draft(draft)
    if not ok:
        return True, reason
    low = (draft or "").lower()
    if at == "buyer":
        obeys, why = buyer_letter_obeys_instructions(draft)
        if not obeys:
            return True, why
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
    from app.services.phelan_outreach_send import parse_cal_draft

    ok, reason = is_complete_cal_draft(draft)
    if not ok:
        raise ValueError(reason)
    return parse_cal_draft(draft, fallback_name)
