"""RSS / headline noise detection for Phase 4 cleanup."""
from types import SimpleNamespace

from app.services.lead_filter import is_junk
from app.services.rss_noise_lead import (
    is_rss_noise_delete_candidate,
    signals_contain_google_rss_html,
)


def _sig(text: str):
    return SimpleNamespace(signal_text=text)


def test_google_rss_html_detected():
    text = (
        'PE firm Advent invests $150M <a href="https://news.google.com/rss/articles/ABC" '
        'target="_blank">story</a>&nbsp;&nbsp;<font color="#6f6f6f">Mint</font>'
    )
    assert signals_contain_google_rss_html([_sig(text)])


def test_real_company_not_deleted_without_noise():
    ok, _, _ = is_rss_noise_delete_candidate(
        "Hancock Health",
        "Unknown",
        [
            _sig(
                "Successful Initial Deployment Drives Arrive Point Expansion at Hancock Health"
            )
        ],
        from_is_junk=is_junk("Hancock Health"),
    )
    assert not ok


def test_headline_fragment_junk_deleted():
    ok, reason, bucket = is_rss_noise_delete_candidate(
        "Global M&A industry trends: 2026 outlook",
        "Unknown",
        [_sig("Global M&A industry trends: 2026 outlook - PwC")],
        from_is_junk=is_junk("Global M&A industry trends: 2026 outlook"),
    )
    assert ok
    assert bucket == "fast_junk"


def test_rss_unknown_deleted():
    ok, reason, bucket = is_rss_noise_delete_candidate(
        "PE firm Advent",
        "Unknown",
        [
            _sig(
                'PE firm Advent invests $150M <a href="https://news.google.com/rss/articles/X" '
                'target="_blank">Mint</a>'
            )
        ],
        from_is_junk=is_junk("PE firm Advent"),
    )
    assert ok
    assert bucket == "rss_html_noise"


def test_known_industry_not_deleted_even_with_rss():
    ok, _, _ = is_rss_noise_delete_candidate(
        "Acme Corp",
        "Logistics",
        [_sig('News <a href="https://news.google.com/rss/articles/X">x</a>')],
        from_is_junk=is_junk("Acme Corp"),
    )
    assert not ok
