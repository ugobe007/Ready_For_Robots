"""Pipeline junk filter tests."""
from types import SimpleNamespace

from scripts.cleanup_pipeline_junk import (
    _has_clean_signal_text,
    _pipeline_junk_bucket,
    _signals_are_all_rss_html,
)


def _sig(text: str, signal_type: str = "news"):
    return SimpleNamespace(signal_text=text, signal_type=signal_type)


def test_all_rss_detects_html_only_rows():
    html = 'Story <a href="https://news.google.com/rss/articles/X" target="_blank">x</a>&nbsp;'
    assert _signals_are_all_rss_html([_sig(html), _sig(html)])


def test_mixed_rss_not_all_rss():
    html = 'Story <a href="https://news.google.com/rss/articles/X">x</a>'
    clean = "Marriott expands housekeeping robot pilot across full-service brands"
    assert not _signals_are_all_rss_html([_sig(html), _sig(clean)])


def test_jll_like_account_not_deleted_with_clean_signals():
    class Co:
        name = "Jones Lang LaSalle (JLL)"
        industry = "Real Estate & Facilities"
        is_internal = True
        scores = []
        signals = [
            _sig("JLL deploys autonomous cleaning robots across managed properties", "news"),
            _sig('Funding <a href="https://news.google.com/rss/articles/X">x</a>', "funding_round"),
        ]

    ok, reason, bucket = _pipeline_junk_bucket(Co())
    assert not ok
