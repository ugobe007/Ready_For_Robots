"""Project timing resolution for sales leads."""
from app.services.lead_project_timing import resolve_project_timing


def test_crm_top_window_wins():
    t = resolve_project_timing(
        tier="HOT",
        crm_metadata={"timing": {"top_window": "within 6 months"}},
    )
    assert t.source == "extracted"
    assert "6 months" in t.label.lower() or "month" in t.label.lower()
    assert t.day_min is not None and t.day_max is not None


def test_inference_timetable_window():
    t = resolve_project_timing(
        tier="WARM",
        crm_metadata={},
        lead_inference={"timetable": {"window": "Q3 2026"}},
    )
    assert t.source == "extracted"
    assert "Q3" in t.label


def test_signal_blob_extracts_day_range():
    t = resolve_project_timing(
        tier="COLD",
        signal_blob="Pilot expected to go live in 45 to 60 days at the DC.",
        signal_types=["pilot"],
    )
    assert t.day_min == 45
    assert t.day_max == 60


def test_estimate_varies_by_signal_not_flat_hot_default():
    hot_rfp = resolve_project_timing(
        tier="HOT",
        signal_types=["rfp"],
        procurement_hints=["rfp_procurement"],
        intent_score=92,
    )
    hot_explore = resolve_project_timing(
        tier="HOT",
        signal_types=["news"],
        intent_score=92,
    )
    assert hot_rfp.day_max != hot_explore.day_max or hot_rfp.label != hot_explore.label
    assert "procurement" in hot_rfp.label.lower() or hot_rfp.day_max <= 90
