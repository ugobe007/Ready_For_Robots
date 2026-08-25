"""Tests for Cal Seller Brief — OEM-facing conversion artifact."""
from app.services.cal_seller_brief import build_cal_seller_brief, format_cal_seller_brief_text


def test_seller_brief_is_oem_facing():
    brief = build_cal_seller_brief(
        company_name="Accor",
        industry="Hospitality",
        signal_text="Hiring overnight housekeeping managers across 12 properties",
        signal_type="labor_shortage",
        pipeline_action="Lead with overnight cleaning automation ROI",
        robot_types=["service cleaning", "delivery"],
        hermes_job_title="Overnight Housekeeping Manager",
    )
    assert brief["for_whom"] == "oem"
    assert "Accor" in brief["headline"]
    assert "Jobs" in brief["headline"]
    assert "Housekeeping" in brief["why_now"] or "Robot Job" in brief["why_now"]
    assert "task model" in brief["pitch"].lower() or "overnight cleaning" in brief["pitch"].lower()
    assert "service cleaning" in brief["robot_fit"]
    assert "Job Card" in brief["next_step"]
    assert not brief["why_now"].lower().startswith("hi ")
    assert "dear" not in brief["pitch"].lower()


def test_seller_brief_falls_back_without_hermes():
    brief = build_cal_seller_brief(
        company_name="Ryder",
        industry="Logistics",
        share_summary="Opening two DCs while posting automation engineer roles.",
        robot_types=["AMR", "forklift"],
    )
    assert "Ryder" in brief["headline"]
    assert "Opening two DCs" in brief["why_now"]
    assert "AMR" in brief["robot_fit"]
    text = format_cal_seller_brief_text(brief)
    assert "Why now:" in text
    assert "Pitch:" in text
