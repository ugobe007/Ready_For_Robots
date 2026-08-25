"""Jobs CRM sanitizer for Hermes overlay dumps."""

from app.services.hermes_job_evidence import (
    humanize_overlay_rationale,
    is_real_vendor_name,
    sanitize_hermes_pipeline_overlay,
)


def test_drops_robot_type_slugs_and_keeps_real_vendors():
    assert is_real_vendor_name("amr") is False
    assert is_real_vendor_name("amr_amr_forklift") is False
    assert is_real_vendor_name("cobot") is False
    assert is_real_vendor_name("mobile_manipulator") is False
    assert is_real_vendor_name("Boston Dynamics") is True
    assert is_real_vendor_name("Agility Robotics") is True


def test_humanize_overlay_rationale_keeps_one_human_line():
    raw = (
        "[rfr_inference_v1] Labor shortage / staffing gap; Labor shortage / staffing gap; "
        "high-fit industry (Hospitality); 8 hot-type signals (labor_shortage, capex, "
        "strategic_hire, expansion, funding_round, ...); 12 signals; work family: unknown"
    )
    assert humanize_overlay_rationale(raw) == "Labor shortage / staffing gap"


def test_sanitize_hides_signal_only_overlay():
    overlay = {
        "automation_fit": 98,
        "labor_intensity": "high",
        "facility_clarity": "named_site",
        "truth_state": "HERMES_OVERLAY",
        "rationale": (
            "[rfr_inference_v1] Labor shortage / staffing gap; 12 signals; "
            "work family: unknown"
        ),
        "vendor_shortlist": [
            {"vendor": "amr_amr_forklift"},
            {"vendor": "cobot"},
            {"vendor": "mobile_manipulator"},
        ],
    }
    assert sanitize_hermes_pipeline_overlay(overlay) is None


def test_sanitize_keeps_named_vendors():
    cleaned = sanitize_hermes_pipeline_overlay(
        {
            "automation_fit": 70,
            "rationale": "[rfr_inference_v1] 12 signals",
            "vendor_shortlist": [
                {"vendor": "cobot"},
                {"vendor": "Boston Dynamics", "model": "Spot"},
            ],
        }
    )
    assert cleaned is not None
    assert cleaned["vendor_shortlist"] == [
        {"vendor": "Boston Dynamics", "model": "Spot", "why": None}
    ]
    assert "automation_fit" not in cleaned
    assert "truth_state" not in cleaned
    overlay = {
        "automation_fit": 98,
        "rationale": "12 signals; work family: unknown",
        "vendor_shortlist": ["amr", "cobot"],
    }
    assert sanitize_hermes_pipeline_overlay(overlay) is None
