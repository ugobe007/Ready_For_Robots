"""Tests for HOT/WARM headline quarantine heuristics."""
from types import SimpleNamespace

from app.services.headline_hot_quarantine import headline_hot_leak_reason


def test_news_prefix_is_headline_leak():
    ok, reason = headline_hot_leak_reason("News AI-powered")
    assert ok is True
    assert "news" in reason.lower() or "pattern" in reason.lower()


def test_new_costco_is_headline_leak():
    ok, _ = headline_hot_leak_reason("New Costco")
    assert ok is True


def test_event_colon_headline():
    ok, _ = headline_hot_leak_reason("NRF 2026: HPE")
    assert ok is True


def test_sentence_headline():
    ok, reason = headline_hot_leak_reason(
        "Milestone CEO Highlights Hotel AI Visibility"
    )
    assert ok is True
    assert "verb" in reason.lower() or "pattern" in reason.lower() or "ceo" in reason.lower()


def test_real_company_not_flagged():
    ok, _ = headline_hot_leak_reason("Costco Wholesale")
    assert ok is False


def test_new_york_not_flagged():
    ok, _ = headline_hot_leak_reason("New York")
    assert ok is False
