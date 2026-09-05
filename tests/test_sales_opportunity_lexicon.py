"""Sales opportunity lexicon — editorial filter, pain-in-vertical, weak triggers."""
from app.services.robot_signal_ontology import signal_types_from_ontology_matches
from app.services.signal_classifier import classify_signals_with_fallback
from app.services.signal_rules_engine import rules_engine_signal_types


def test_editorial_trigger_does_not_fire_automation_intent():
    text = (
        "This article explores how the hospitality industry uses automation to control costs. "
        "78% of hotel chains have already integrated AI solutions."
    )
    types = signal_types_from_ontology_matches(text)
    assert "automation_intent" not in types


def test_pain_words_in_hospitality_vertical():
    text = (
        "Marriott understaffed hotels face high turnover and seasonal labor gaps "
        "across housekeeping and front desk teams in Florida."
    )
    types = signal_types_from_ontology_matches(text)
    assert "labor_shortage" in types


def test_weak_robot_token_suppressed_without_context():
    text = "Robot makers continue to innovate with new models this quarter."
    types = rules_engine_signal_types(text)
    assert "automation_interest" not in types


def test_vendor_funding_story_filtered_at_classify():
    text = "Robotics startup raises $40M Series B to scale humanoid platform for warehouses."
    types = classify_signals_with_fallback(text)
    assert "automation_interest" not in types
    assert "funding_round" not in types
