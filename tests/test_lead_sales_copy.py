"""Natural-language sales lead intelligence copy."""
from app.services.lead_sales_copy import (
    build_lead_intelligence_copy,
    humanize_robot_types,
    is_low_quality_sales_text,
    preview_sentences,
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
    assert "Acme Logistics" in summary
    assert "Signals observed:" not in summary
    assert "Robot types that fit" not in summary
    assert "aligns with our signals" not in summary.lower()
    assert "active buying indicators" not in summary.lower()
    assert "mobile robots" in summary.lower() or "warehouse automation" in summary.lower()
    assert "days" in summary.lower() or "vendor" in summary.lower() or "partner" in summary.lower()
    assert len(blurb) <= 220


def test_humanize_robot_types_from_profile():
    types = humanize_robot_types(
        {"robot_categories": ["humanoid", "service_robot"], "application_areas": []},
        industry="Hospitality",
    )
    assert "humanoid robots" in types
    assert "service robots" in types


def test_preview_sentences_no_mid_word_cut():
    long = (
        "Omni Fort Lauderdale Hotel is targeting automation for their room service robots "
        "due to labor vacancies, which aligns with our signals: labor shortage. "
        "The timing of the project is 90 to 120 days."
    )
    out = preview_sentences(long, max_sentences=2, max_chars=220)
    assert not out.rstrip().endswith("w")
    assert not out.rstrip().endswith("aligns w")
    assert out.endswith(".")
    assert "labor" in out.lower()


def test_is_low_quality_sales_text():
    assert is_low_quality_sales_text("Qualifying factors: foo; bar.")
    assert is_low_quality_sales_text("")
    assert not is_low_quality_sales_text(
        "Marriott is piloting service robots at two hotels to address housekeeping gaps."
    )


def test_headline_led_opening():
    _, summary = build_lead_intelligence_copy(
        company_name="Marriott International",
        industry="Hospitality",
        tier="HOT",
        signal_labels=["Expansion"],
        signal_types=["expansion"],
        automation_type="service robots",
        pain_point="housekeeping labor",
        automation_profile={"robot_categories": ["service_robot"], "application_areas": []},
        crm_metadata=None,
        signal_blob=(
            "Marriott pilots service robots at two flagship hotels to ease housekeeping load - "
            "Hospitality Dive. Marriott pilots service robots at two flagship hotels."
        ),
    )
    assert "Marriott" in summary
    assert "Signals observed:" not in summary
    assert "pilot" in summary.lower() or "service robot" in summary.lower()
