"""Natural-language sales lead intelligence copy."""
from app.services.lead_sales_copy import (
    build_lead_intelligence_copy,
    humanize_robot_types,
    is_low_quality_sales_text,
)


def test_share_summary_natural_language_not_robotic():
    blurb, summary = build_lead_intelligence_copy(
        company_name="Acme Logistics",
        industry="Logistics",
        tier="WARM",
        signal_labels=["Labor Shortage", "CapEx"],
        signal_types=["labor_shortage", "capex"],
        automation_type="warehouse automation",
        pain_point="labor costs",
        automation_profile={
            "robot_categories": ["amr_amr_forklift"],
            "application_areas": ["pick_and_place"],
        },
        crm_metadata=None,
        signal_blob="Acme announced a warehouse automation program and labor shortage.",
    )
    assert "Signals observed:" in summary
    assert "Acme Logistics is looking for automation" in summary
    assert "90 to 120 days" in summary
    assert "Robot types that fit" in summary
    assert "mobile robots" in summary.lower()
    assert "active buying indicators" not in summary.lower()
    assert "Qualifying factors" not in summary
    assert len(blurb) <= 220


def test_humanize_robot_types_from_profile():
    types = humanize_robot_types(
        {"robot_categories": ["humanoid", "service_robot"], "application_areas": []},
        industry="Hospitality",
    )
    assert "humanoid robots" in types
    assert "service robots" in types


def test_is_low_quality_sales_text():
    assert is_low_quality_sales_text("Qualifying factors: foo; bar.")
    assert is_low_quality_sales_text("")
    assert not is_low_quality_sales_text(
        "Marriott is piloting service robots at two hotels to address housekeeping gaps."
    )
