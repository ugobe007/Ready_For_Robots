"""Vendor deployment design — ROI validation and workflow layout."""
from app.services.vendor_deployment_design import (
    RoiInputs,
    validate_and_compute_roi,
    default_workflow_layout,
    summarize_workflow_impact,
)


def test_roi_detects_missing_maintenance():
    result = validate_and_compute_roi(
        RoiInputs(
            robot_unit_cost=40_000,
            fte_count_replaced=1,
            fte_fully_loaded_cost=58_000,
            annual_maintenance_pct=0,
            industry="logistics",
        )
    )
    codes = [i.code for i in result.issues]
    assert "missing_maintenance" in codes
    assert result.payback_months > 0
    assert result.annual_net_savings > 0


def test_roi_flags_buyer_payback_mismatch():
    result = validate_and_compute_roi(
        RoiInputs(
            robot_unit_cost=40_000,
            fte_count_replaced=1,
            fte_fully_loaded_cost=58_000,
            industry="hospitality",
            buyer_stated_payback_months=6,
        )
    )
    codes = [i.code for i in result.issues]
    assert "buyer_payback_mismatch" in codes
    assert result.corrected_from_buyer


def test_default_layout_has_robots_and_flows():
    layout = default_workflow_layout("hospitality")
    assert layout["zones"]
    assert layout["robots"]
    assert layout["flows"]
    impact = summarize_workflow_impact(layout)
    assert impact["robot_count"] >= 1
    assert impact["labor_hours_saved_per_week"] > 0
