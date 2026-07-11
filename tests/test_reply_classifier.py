"""Keyword-fallback reply classification — the safety net that must never drop a reply."""
import pytest

from app.services.reply_classifier import INTENTS, classify_reply, sentiment_for


@pytest.mark.parametrize(
    "subject,body,expected",
    [
        ("Re: your note", "Please remove me from your list, unsubscribe", "unsubscribe"),
        ("Out of Office", "I am out of office until Monday", "auto_reply"),
        ("Automatic reply", "I'm away from my desk", "auto_reply"),
        ("Re", "Not interested, we are all set thanks", "not_a_fit"),
        ("Re", "We tried robots before and it didn't work", "already_tried"),
        ("Re", "Can we schedule a call next week? what's your calendar", "meeting"),
        ("Re", "What does this cost? ballpark pricing?", "pricing"),
        ("Re", "Circle back next quarter please", "not_now"),
        ("Re", "You should talk to our ops lead, cc-ing them", "referral"),
        ("Re", "Yes, interested — tell me more", "interested"),
        ("Re", "ok", "other"),
    ],
)
def test_keyword_classifier_labels(subject, body, expected):
    cls = classify_reply(subject, body, use_llm=False)
    assert cls.intent == expected
    assert cls.intent in INTENTS
    assert cls.source == "keyword"


def test_hard_signals_skip_llm_even_when_enabled():
    # Opt-out / autoresponder are unambiguous and must resolve without an LLM call.
    assert classify_reply("x", "unsubscribe me now", use_llm=True).source == "keyword"
    assert classify_reply("Out of office", "back monday", use_llm=True).source == "keyword"


def test_sentiment_mapping_is_actionable():
    assert sentiment_for("meeting") == "positive"
    assert sentiment_for("not_a_fit") == "negative"
    assert sentiment_for("unsubscribe") == "negative"
    assert sentiment_for("not_now") == "neutral"


def test_empty_body_never_raises():
    cls = classify_reply(None, None, use_llm=False)
    assert cls.intent in INTENTS
