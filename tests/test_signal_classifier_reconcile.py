"""Ingest-time reconciliation: exec-appointment press should not stay typed as expansion-only."""

from app.services.signal_classifier import (
    classify_signals_with_fallback,
    reconcile_signal_types_for_text,
    text_indicates_executive_appointment,
)


def test_text_indicates_executive_appointment_pm_hotel_headline():
    t = (
        "PM Hotel Group names Kirk Pederson chief operating officer. "
        "PM Hotel Group names Kirk Pederson chief operating officer Hotel Dive"
    )
    assert text_indicates_executive_appointment(t) is True


def test_reconcile_drops_expansion_without_facility_anchor():
    text = "PM Hotel Group names Kirk Pederson chief operating officer."
    assert reconcile_signal_types_for_text(text, ["expansion", "strategic_hire"]) == [
        "strategic_hire",
    ]


def test_reconcile_inserts_strategic_hire_when_only_expansion():
    text = "Trailborn Hotels & Resorts Appoints Paul Eckert as Chief Operations Officer"
    assert reconcile_signal_types_for_text(text, ["expansion"]) == ["strategic_hire"]


def test_reconcile_keeps_expansion_when_facility_context_present():
    text = (
        "PM Hotel Group names Kirk Pederson chief operating officer while "
        "breaking ground on a new 400000 square feet distribution center"
    )
    out = reconcile_signal_types_for_text(text, ["expansion", "strategic_hire"])
    assert "expansion" in out
    assert "strategic_hire" in out
    assert out[0] == "strategic_hire"


def test_reconcile_drops_expansion_for_qsr_store_opening():
    text = "Imo's Pizza Opens First Store in Nashville Area"
    assert reconcile_signal_types_for_text(text, ["expansion"]) == ["news"]


def test_reconcile_keeps_expansion_for_warehouse_opening():
    text = "Acme Logistics opens new 400000 square foot distribution center in Indiana"
    out = reconcile_signal_types_for_text(text, ["expansion"])
    assert "expansion" in out


def test_classify_signals_with_fallback_strips_weak_expansion_for_pizza_store():
    text = "Imo's Pizza Opens First Store in Nashville Area"
    types = classify_signals_with_fallback(text, article_url="", rss_source_name="")
    assert "expansion" not in types


def test_classify_signals_with_fallback_strips_weak_expansion_for_coo_story():
    text = "PM Hotel Group names Kirk Pederson chief operating officer. Hotel Dive"
    types = classify_signals_with_fallback(text, article_url="", rss_source_name="")
    assert "expansion" not in types
    assert "strategic_hire" in types
