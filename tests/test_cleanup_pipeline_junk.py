"""Pipeline junk audit tests — policy-aligned hard delete only."""
from types import SimpleNamespace

from scripts.cleanup_pipeline_junk import _pipeline_junk_bucket


def _sig(text: str, signal_type: str = "news"):
    return SimpleNamespace(signal_text=text, signal_type=signal_type)


def test_jll_like_account_not_hard_deleted():
    class Co:
        name = "Jones Lang LaSalle (JLL)"
        industry = "Real Estate & Facilities"
        is_internal = True
        scores = []
        signals = [
            _sig("JLL deploys autonomous cleaning robots across managed properties", "news"),
            _sig('Funding <a href="https://news.google.com/rss/articles/X">x</a>', "funding_round"),
        ]

    ok, reason, bucket, note = _pipeline_junk_bucket(Co())
    assert not ok


def test_hilton_rss_only_not_hard_deleted():
    class Co:
        name = "Hilton Hotels"
        industry = "Hospitality"
        is_internal = True
        scores = []
        signals = [
            _sig(
                'Hilton Hotels expands robot pilot '
                '<a href="https://news.google.com/rss/articles/X" target="_blank">'
                "Hilton Hotels expands robot pilot</a>&nbsp;"
            ),
        ]

    ok, reason, bucket, note = _pipeline_junk_bucket(Co())
    assert not ok


def test_quarantined_not_hard_deleted():
    class Co:
        name = "Marriott Hotels"
        industry = "Hospitality"
        is_internal = False
        scores = []
        signals = [_sig("Marriott expands robot pilot")]

    ok, reason, bucket, note = _pipeline_junk_bucket(Co())
    assert not ok
    assert "quarantine" in note.lower()


def test_headline_fragment_may_hard_delete():
    class Co:
        name = "Global M&A industry trends: 2026 outlook"
        industry = "Unknown"
        is_internal = True
        scores = []
        signals = [_sig("Global M&A industry trends: 2026 outlook - PwC")]

    ok, reason, bucket, note = _pipeline_junk_bucket(Co())
    assert ok
    assert bucket == "invalid_name"
