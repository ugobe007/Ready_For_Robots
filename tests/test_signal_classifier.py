"""Unified signal typing entry points (ontology + rules + fallback)."""

from app.services.signal_classifier import (
    classify_signals_with_fallback,
    primary_signal_type_for_text,
)


def test_primary_signal_type_matches_first_of_classify_signals():
    text = "The company raised a Series B funding round led by venture capital firms."
    merged = classify_signals_with_fallback(text)
    primary = primary_signal_type_for_text(text)
    assert primary == merged[0]


def test_primary_signal_type_passes_article_url_for_channel_inference():
    text = "We are expanding our warehouse and distribution center next year."
    p = primary_signal_type_for_text(text, article_url="https://news.google.com/rss/foo")
    assert p in merged_types(text)


def merged_types(text: str):
    return set(classify_signals_with_fallback(text))


def test_primary_signal_type_funding_fallback():
    text = "Startup closes venture capital round at high valuation."
    assert primary_signal_type_for_text(text) == "funding_round"
