"""Pythh-style rules engine — triggers, negation, merge-ready RFR types."""
from app.services.signal_rules_engine import (
    extract_signal_drafts,
    infer_source_channel,
    rules_engine_signal_types,
    split_clauses,
    split_sentences,
)
from app.services.signal_classifier import classify_signals_with_fallback


def test_negation_suppresses_fundraising_trigger():
    drafts = extract_signal_drafts("We are not actively raising capital this year.")
    fundraising = [d for d in drafts if d.internal_action == "fundraising_signal" and not d.negated]
    assert not fundraising


def test_rfp_maps_to_vendor_selection():
    types = rules_engine_signal_types("The team issued an RFP for warehouse automation.")
    assert "vendor_selection" in types


def test_multi_sentence_split():
    sents = split_sentences("First sentence. Second sentence here!")
    assert len(sents) == 2


def test_after_split_clauses():
    parts = split_clauses("After closing our seed round, we are hiring engineers.")
    assert len(parts) >= 1


def test_infer_source_channel_sec_and_press_wire():
    assert infer_source_channel("https://www.sec.gov/Archives/edgar/data/1/") == "sec_filing"
    assert infer_source_channel("https://www.prnewswire.com/news/foo") == "press_release"


def test_infer_source_channel_unwraps_google_news_url():
    wrapped = (
        "https://news.google.com/rss/articles/"
        "CBMia0FVX3lxTFBNTnNMRm9YbFI0Sm5SbGRtVnllWEIwYVdOb0NnTnZiblJsYm5Se"
        "WRYTmxkQS4u?oc=5&url=https%3A%2F%2Fwww.businesswire.com%2Fnews%2Fhome%2F202601010"
    )
    assert infer_source_channel(wrapped) == "press_release"


def test_classify_merges_rules_with_fallback_path():
    # Short text unlikely to fire ontology; rules + keyword fallback still run
    t = "Regional 3PL expanding warehouse capacity and issuing RFP for AMR systems."
    out = classify_signals_with_fallback(t)
    assert isinstance(out, list)
    assert len(out) >= 1
