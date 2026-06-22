"""Central hard-delete policy tests."""
from types import SimpleNamespace

from app.services.lead_filter import classify_lead, is_junk
from app.services.pipeline_delete_policy import (
    hard_delete_allowed,
    unknown_industry_delete_allowed,
    unknown_rss_noise_quarantine_allowed,
)
from app.services.signal_text_normalize import strip_signal_html


def _sig(text: str, signal_type: str = "news"):
    return SimpleNamespace(signal_text=text, signal_type=signal_type)


def test_quarantined_never_hard_deleted():
    co = SimpleNamespace(name="Marriott Hotels", is_internal=False)
    ok, _, _ = hard_delete_allowed(co, [])
    assert not ok


def test_hilton_rss_not_hard_deleted():
    co = SimpleNamespace(name="Hilton Hotels", is_internal=True)
    html = (
        'Hilton Hotels <a href="https://news.google.com/rss/articles/X">'
        "Hilton Hotels expands robot pilot</a>"
    )
    ok, _, _ = hard_delete_allowed(co, [_sig(html)])
    assert not ok


def test_rss_unknown_not_deleted_without_junk_name():
    html = (
        'PE firm Advent invests $150M <a href="https://news.google.com/rss/articles/X" '
        'target="_blank">Mint</a>'
    )
    ok, _, bucket = unknown_industry_delete_allowed(
        "PE firm Advent",
        "Unknown",
        [_sig(html)],
    )
    assert not ok


def test_headline_unknown_deleted():
    ok, _, bucket = unknown_industry_delete_allowed(
        "Global M&A industry trends: 2026 outlook",
        "Unknown",
        [_sig("Global M&A industry trends: 2026 outlook - PwC")],
    )
    assert ok
    assert bucket == "fast_junk"


def test_known_brand_passes_buyer_gate_with_rss():
    co = SimpleNamespace(
        name="Starbucks",
        industry="Food Service",
        is_internal=True,
        employee_estimate=None,
    )
    html = (
        'Starbucks pilots delivery robots '
        '<a href="https://news.google.com/rss/articles/X">Starbucks pilots delivery robots</a>'
    )
    junk, reason, pri = classify_lead(co, None, [_sig(html)])
    assert not junk
    assert pri.tier in ("HOT", "WARM", "COLD")


def test_strip_signal_html_keeps_anchor():
    clean = strip_signal_html(
        'Title <a href="https://news.google.com/rss/articles/X">Real Headline Here</a>'
    )
    assert "Real Headline Here" in clean
    assert "<a" not in clean


def test_novartis_unknown_not_quarantined():
    html = (
        'Novartis reports progress '
        '<a href="https://news.google.com/rss/articles/X">Novartis reports progress</a>'
    )
    ok, _, bucket = unknown_rss_noise_quarantine_allowed(
        "Novartis",
        "Unknown",
        [_sig(html)],
        from_is_junk=(False, ""),
        from_classify=(False, "", None),
    )
    assert not ok


def test_market_report_unknown_quarantined():
    ok, reason, bucket = unknown_rss_noise_quarantine_allowed(
        "Global M&A industry trends: 2026 outlook",
        "Unknown",
        [_sig("Global M&A industry trends: 2026 outlook - PwC")],
        from_is_junk=is_junk("Global M&A industry trends: 2026 outlook"),
    )
    assert ok
    assert bucket == "junk_name"
