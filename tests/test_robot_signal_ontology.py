"""Robot Automation Signal Ontology markdown integration."""
from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.robot_signal_ontology import (
    load_robot_signal_ontology,
    match_ontology_features,
    ontology_signal_points,
    signal_types_from_ontology_matches,
)
from app.services.signal_ranker import compute_weighted_score


def test_ontology_loader_extracts_core_feature_sets():
    features = load_robot_signal_ontology()

    assert "understaffed" in features.pain_words
    assert "automation investment" in features.buying_phrases
    assert "we have allocated budget for automation projects." in features.trigger_expressions
    assert "director of automation" in features.job_title_signals


def test_ontology_exact_trigger_is_high_confidence_signal():
    text = "We have allocated budget for automation projects."
    matches = match_ontology_features(text)

    assert matches.trigger_expressions
    assert signal_types_from_ontology_matches(text)[0] == "automation_intent"
    assert ontology_signal_points(text, source_channel="press_release") >= 45


def test_ontology_phrase_and_pain_word_cooccurrence_scores():
    text = "The warehouse is understaffed and announced a warehouse automation strategy."
    signals = signal_types_from_ontology_matches(text)

    assert "warehouse_throughput" in signals
    assert "labor_shortage" in signals
    assert ontology_signal_points(text) >= 20


def test_signal_ranker_uses_ontology_scoring_floor():
    signal = SimpleNamespace(
        signal_type="automation_intent",
        signal_text="We have allocated budget for automation projects.",
        signal_strength=0.1,
        source_url="https://www.prnewswire.com/news/test",
        created_at=datetime.now(timezone.utc),
    )

    assert compute_weighted_score(signal) >= 40
