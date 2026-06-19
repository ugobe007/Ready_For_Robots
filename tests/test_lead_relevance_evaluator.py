"""Lead relevance evaluator — name extraction + topic fit (not RSS guilt)."""
from types import SimpleNamespace

from app.services.signal_text_normalize import strip_signal_html
from app.services.lead_relevance_evaluator import (
    ExtractedName,
    _rename_is_safe,
    dedupe_word_strings,
    evaluate_lead_relevance,
    extract_candidate_names,
    should_delete_as_junk,
)


def _sig(text: str):
    return SimpleNamespace(signal_text=text)


def _co(name: str, industry: str = "Hospitality", cid: int = 1):
    return SimpleNamespace(id=cid, name=name, industry=industry)


RSS_HTML = (
    'Hilton Hotels expands housekeeping robot pilot '
    '<a href="https://news.google.com/rss/articles/ABC" target="_blank">'
    'Hilton Hotels expands housekeeping robot pilot</a>&nbsp;'
)


def test_strip_signal_html_keeps_anchor_text():
    clean = strip_signal_html(RSS_HTML)
    assert "Hilton Hotels" in clean
    assert "<a" not in clean
    assert "news.google.com" not in clean


def test_dedupe_word_strings_merges_duplicate_phrases():
    t1 = "Marriott deploys service robots across full-service hotels"
    t2 = "marriott deploys service robots across full-service hotels"
    blob, phrases, words = dedupe_word_strings([t1, t2, RSS_HTML])
    assert len(phrases) == 2
    assert "Marriott" in blob
    assert words >= 8


def test_hilton_rss_not_auto_junk():
    report = evaluate_lead_relevance(
        _co("Hilton Hotels", "Hospitality"),
        [_sig(RSS_HTML)],
    )
    assert report.disposition in ("keep", "enrich", "rename")
    assert report.topic_relevance_score >= 0.35
    assert not should_delete_as_junk(report)[0]


def test_headline_fragment_is_junk():
    report = evaluate_lead_relevance(
        _co("Global M&A industry trends: 2026 outlook", "Unknown"),
        [_sig("Global M&A industry trends: 2026 outlook - PwC")],
    )
    assert report.disposition == "junk"
    assert should_delete_as_junk(report)[0]


def test_extracts_better_name_from_rss_headline():
    report = evaluate_lead_relevance(
        _co("Amazon sees warehouse robots flattening labor costs", "Logistics"),
        [
            _sig(
                'Amazon Logistics <a href="https://news.google.com/rss/articles/X">'
                "Amazon Logistics opens new fulfillment center with AMR fleet</a>"
            )
        ],
    )
    names = [n.name for n in report.extracted_names]
    assert any("Amazon" in n for n in names)
    assert report.rss_html_ratio >= 0.9
    assert report.disposition != "junk"


def test_known_brand_unknown_industry_still_kept():
    report = evaluate_lead_relevance(
        _co("Wyndham", "Unknown"),
        [_sig(RSS_HTML.replace("Hilton", "Wyndham"))],
    )
    assert report.industry_from_text == "Hospitality"
    assert report.disposition in ("keep", "enrich", "rename")
    assert not should_delete_as_junk(report)[0]


def test_extract_candidate_names_dedupes_sources():
    phrases = [
        "CEVA Logistics deploys warehouse AMRs in European hubs",
        "CEVA Logistics deploys warehouse AMRs in European hubs",
    ]
    names = extract_candidate_names("CEVA Logistics", phrases)
    keys = {n.name.lower() for n in names}
    assert "ceva logistics" in keys
    assert len(names) <= 4


def test_rename_not_suggested_for_clean_brand_name():
    report = evaluate_lead_relevance(
        _co("Galaxy Entertainment Group", "Hospitality"),
        [
            _sig(
                'Norwegian Cruise Line Holdings <a href="https://news.google.com/rss/articles/X">'
                "Norwegian Cruise Line orders new ships</a>"
            )
        ],
    )
    assert report.suggested_name is None
    assert report.disposition in ("keep", "enrich", "review")


def test_rename_safe_only_for_headline_stored_name():
    cand = ExtractedName("Amazon Logistics", "article_extractor", 0.85)
    assert not _rename_is_safe("Galaxy Entertainment Group", cand)
    headline = (
        "Amazon sees warehouse robots flattening labor costs at scale "
        "across nationwide fulfillment network expansion program"
    )
    assert _rename_is_safe(headline, cand)
