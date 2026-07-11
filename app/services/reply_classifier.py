"""Classify inbound outreach replies for the communication learning loop.

Runs inline in the inbound webhook. LLM-first with a keyword fallback so a
provider hiccup can never drop a reply — the keyword pass always returns a
usable label. Labels feed both the intent-aware cadence and the weekly
per-variant learning report.

Taxonomy (coarse, sales-actionable):
    interested     — wants to engage / positive signal, no explicit meeting ask
    meeting        — asks for a call/demo/time
    pricing        — asks about cost/budget/quote
    referral       — points to someone else / "talk to X"
    not_now        — timing pushback ("next quarter", "circle back")
    already_tried  — tried robots/automation before, skeptical
    not_a_fit      — explicit no / not relevant
    unsubscribe    — remove me / stop / opt-out
    auto_reply     — OOO / bounce / autoresponder
    other          — anything unclassified
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

INTENTS = (
    "interested",
    "meeting",
    "pricing",
    "referral",
    "not_now",
    "already_tried",
    "not_a_fit",
    "unsubscribe",
    "auto_reply",
    "other",
)

# Sentiment bucket per intent — used by the report and the cadence branch.
_SENTIMENT = {
    "interested": "positive",
    "meeting": "positive",
    "pricing": "positive",
    "referral": "positive",
    "not_now": "neutral",
    "already_tried": "neutral",
    "auto_reply": "neutral",
    "other": "neutral",
    "not_a_fit": "negative",
    "unsubscribe": "negative",
}


@dataclass
class ReplyClassification:
    intent: str
    sentiment: str
    source: str  # "llm" | "keyword"


def sentiment_for(intent: str) -> str:
    return _SENTIMENT.get(intent, "neutral")


def _keyword_classify(subject: str | None, body: str | None) -> str:
    """Deterministic fallback. Order matters: hard stops first."""
    blob = f"{subject or ''}\n{body or ''}".lower()

    # Autoresponders / bounces — never treat as engagement.
    if any(
        x in blob
        for x in (
            "out of office",
            "out-of-office",
            "automatic reply",
            "auto-reply",
            "autoreply",
            "on vacation",
            "away from my desk",
            "undeliverable",
            "delivery has failed",
            "mailer-daemon",
            "delivery status notification",
            "address not found",
        )
    ):
        return "auto_reply"

    if any(
        x in blob
        for x in (
            "unsubscribe",
            "remove me",
            "take me off",
            "stop emailing",
            "do not contact",
            "don't contact",
            "opt out",
            "opt-out",
        )
    ):
        return "unsubscribe"

    if any(
        x in blob
        for x in (
            "not interested",
            "no thanks",
            "no thank you",
            "not a fit",
            "not relevant",
            "we're all set",
            "we are all set",
            "not for us",
            "please stop",
        )
    ):
        return "not_a_fit"

    if any(
        x in blob
        for x in (
            "already tried",
            "tried that",
            "tried robots",
            "tried automation",
            "didn't work",
            "did not work",
            "burned before",
            "failed pilot",
            "pilot failed",
        )
    ):
        return "already_tried"

    if any(
        x in blob
        for x in (
            "next quarter",
            "next year",
            "not now",
            "circle back",
            "reach out later",
            "check back",
            "revisit",
            "down the road",
            "not this year",
        )
    ):
        return "not_now"

    if any(
        x in blob
        for x in (
            "price",
            "pricing",
            "cost",
            "budget",
            "quote",
            "how much",
            "ballpark",
        )
    ):
        return "pricing"

    if any(
        x in blob
        for x in (
            "meeting",
            "call",
            "demo",
            "schedule",
            "calendar",
            "book a time",
            "hop on",
            "chat",
            "available",
            "what time",
        )
    ):
        return "meeting"

    if any(
        x in blob
        for x in (
            "talk to",
            "reach out to",
            "connect you",
            "forward this",
            "the right person",
            "cc'ing",
            "loop in",
            "wrong person",
        )
    ):
        return "referral"

    if any(
        x in blob
        for x in (
            "interested",
            "tell me more",
            "send it",
            "sounds good",
            "learn more",
            "curious",
            "would like to",
            "yes please",
            "keen",
        )
    ):
        return "interested"

    return "other"


_LLM_SYSTEM = (
    "You label a single inbound sales-email reply with exactly one intent from this "
    "list: interested, meeting, pricing, referral, not_now, already_tried, not_a_fit, "
    "unsubscribe, auto_reply, other. 'already_tried' = they previously tried robots or "
    "automation and are skeptical. 'auto_reply' = out-of-office/bounce/autoresponder. "
    "'not_a_fit' = an explicit no. Respond with ONLY a JSON object like "
    '{"intent":"meeting"}. No prose.'
)


def _llm_classify(subject: str | None, body: str | None) -> str | None:
    text = (body or "").strip()
    if not text:
        return None
    try:
        from app.services.llm_client import get_llm_client, get_llm_model

        client = get_llm_client(timeout=12.0, max_retries=0)
        resp = client.chat.completions.create(
            model=get_llm_model(),
            temperature=0,
            max_tokens=20,
            messages=[
                {"role": "system", "content": _LLM_SYSTEM},
                {
                    "role": "user",
                    "content": f"Subject: {subject or '(none)'}\n\nReply:\n{text[:2000]}",
                },
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()
        # Tolerate code fences / stray text around the JSON.
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1:
            raw = raw[start : end + 1]
        intent = str(json.loads(raw).get("intent") or "").strip().lower()
        return intent if intent in INTENTS else None
    except Exception as exc:  # noqa: BLE001 — never let classification drop a reply
        logger.info("reply LLM classify fell back to keywords: %s", exc)
        return None


def classify_reply(
    subject: str | None, body: str | None, *, use_llm: bool = True
) -> ReplyClassification:
    """Return (intent, sentiment, source). Always succeeds via keyword fallback."""
    keyword = _keyword_classify(subject, body)

    # Hard signals (opt-out / autoresponder) are unambiguous — trust keywords and
    # skip the LLM round-trip entirely.
    if keyword in ("unsubscribe", "auto_reply"):
        return ReplyClassification(keyword, sentiment_for(keyword), "keyword")

    if use_llm:
        llm = _llm_classify(subject, body)
        if llm:
            return ReplyClassification(llm, sentiment_for(llm), "llm")

    return ReplyClassification(keyword, sentiment_for(keyword), "keyword")
