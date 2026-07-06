"""
Vendor deployment design — validated ROI models + workflow layout for buyer-facing proposals.

Robot companies use this to correct malformed buyer economics and show where robots
integrate in the physical workflow.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Industry payback benchmarks (months) — from deployment intelligence corpus
INDUSTRY_BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "hospitality": {"payback_months": (12, 24), "labor_share_typical": 0.35, "label": "Hospitality"},
    "healthcare": {"payback_months": (12, 24), "labor_share_typical": 0.4, "label": "Healthcare"},
    "logistics": {"payback_months": (12, 24), "labor_share_typical": 0.45, "label": "Logistics / Warehouse"},
    "food_service": {"payback_months": (14, 28), "labor_share_typical": 0.38, "label": "Food Service"},
    "manufacturing": {"payback_months": (8, 18), "labor_share_typical": 0.5, "label": "Manufacturing"},
    "retail": {"payback_months": (14, 30), "labor_share_typical": 0.32, "label": "Retail"},
}


def _norm_industry(industry: str) -> str:
    raw = (industry or "").strip().lower()
    if "hotel" in raw or "hospitality" in raw or "casino" in raw:
        return "hospitality"
    if "health" in raw or "hospital" in raw or "clinic" in raw:
        return "healthcare"
    if "logistic" in raw or "warehouse" in raw or "3pl" in raw:
        return "logistics"
    if "food" in raw or "restaurant" in raw or "qsr" in raw or "kitchen" in raw:
        return "food_service"
    if "manufact" in raw or "factory" in raw:
        return "manufacturing"
    if "retail" in raw or "store" in raw:
        return "retail"
    return "logistics"


@dataclass
class RoiInputs:
    robot_unit_cost: float
    robot_count: int = 1
    deployment_cost: float = 0.0
    annual_maintenance_pct: float = 10.0
    labor_mode: str = "fte"  # fte | hourly
    fte_count_replaced: float = 0.0
    fte_fully_loaded_cost: float = 0.0
    hours_per_day: float = 0.0
    hourly_wage: float = 0.0
    labor_replaced_pct: float = 100.0
    industry: str = ""
    shift_days_per_year: int = 365
    buyer_stated_payback_months: Optional[float] = None
    buyer_stated_annual_savings: Optional[float] = None


@dataclass
class RoiValidationIssue:
    code: str
    severity: str  # error | warning | info
    message: str
    suggestion: str = ""


@dataclass
class RoiModelResult:
    annual_labor_baseline: float
    annual_labor_replaced: float
    annual_maintenance: float
    annual_net_savings: float
    total_capex: float
    payback_months: float
    roi_year_1_pct: float
    roi_year_3_pct: float
    net_savings_3yr: float
    issues: List[RoiValidationIssue] = field(default_factory=list)
    benchmark: Optional[Dict[str, Any]] = None
    corrected_from_buyer: bool = False


def validate_and_compute_roi(inputs: RoiInputs) -> RoiModelResult:
    """Validate economics, flag malformed buyer math, return corrected ROI."""
    issues: List[RoiValidationIssue] = []
    count = max(1, int(inputs.robot_count or 1))
    unit_cost = max(0.0, float(inputs.robot_unit_cost or 0))
    deploy = max(0.0, float(inputs.deployment_cost or 0))
    total_capex = unit_cost * count + deploy

    maint_pct = float(inputs.annual_maintenance_pct or 0)
    if maint_pct <= 0:
        issues.append(
            RoiValidationIssue(
                code="missing_maintenance",
                severity="warning",
                message="Maintenance / support cost is zero.",
                suggestion="Use 8–12% of robot capex per year for service contracts and parts.",
            )
        )
        maint_pct = 10.0

    labor_pct = min(100.0, max(0.0, float(inputs.labor_replaced_pct or 100)))
    if labor_pct > 100:
        issues.append(
            RoiValidationIssue(
                code="labor_pct_overflow",
                severity="error",
                message="Labor replaced exceeds 100% — common spreadsheet error.",
                suggestion="Cap redeployed labor at the FTE hours the robot actually covers.",
            )
        )

    annual_labor = 0.0
    mode = (inputs.labor_mode or "fte").strip().lower()
    if mode == "hourly":
        hrs = max(0.0, float(inputs.hours_per_day or 0))
        wage = max(0.0, float(inputs.hourly_wage or 0))
        days = max(1, int(inputs.shift_days_per_year or 365))
        annual_labor = hrs * wage * days * count
        if wage > 0 and wage < 12:
            issues.append(
                RoiValidationIssue(
                    code="wage_below_minimum",
                    severity="warning",
                    message=f"Hourly wage ${wage:.2f} looks below typical loaded labor cost.",
                    suggestion="Use fully loaded wage (base + benefits + overhead), not base pay only.",
                )
            )
    else:
        ftes = max(0.0, float(inputs.fte_count_replaced or 0))
        loaded = max(0.0, float(inputs.fte_fully_loaded_cost or 0))
        annual_labor = ftes * loaded
        if loaded > 0 and loaded < 35_000:
            issues.append(
                RoiValidationIssue(
                    code="fte_underloaded",
                    severity="warning",
                    message=f"FTE cost ${loaded:,.0f} may exclude benefits and turnover.",
                    suggestion="Add 25–40% for benefits, recruiting, and training on top of salary.",
                )
            )

    if annual_labor <= 0:
        issues.append(
            RoiValidationIssue(
                code="no_labor_baseline",
                severity="error",
                message="No labor baseline — ROI cannot be computed.",
                suggestion="Enter FTE count × loaded cost, or hourly wage × hours/day.",
            )
        )

    annual_labor_replaced = annual_labor * (labor_pct / 100.0)
    annual_maintenance = total_capex * (maint_pct / 100.0)
    annual_net = annual_labor_replaced - annual_maintenance

    payback = 999.0
    if annual_net > 0 and total_capex > 0:
        payback = (total_capex / annual_net) * 12.0
    elif total_capex > 0:
        issues.append(
            RoiValidationIssue(
                code="negative_savings",
                severity="error",
                message="Annual savings are negative — robot costs more than labor replaced.",
                suggestion="Reduce scope, increase labor hours replaced, or revisit robot count.",
            )
        )

    if payback < 6:
        issues.append(
            RoiValidationIssue(
                code="payback_too_fast",
                severity="warning",
                message=f"Payback {payback:.1f} mo is unusually fast — buyers may distrust the model.",
                suggestion="Include integration downtime, training, and partial FTE replacement.",
            )
        )
    if payback > 48:
        issues.append(
            RoiValidationIssue(
                code="payback_slow",
                severity="info",
                message=f"Payback {payback:.0f} mo is long for automation — justify with quality or scale benefits.",
                suggestion="Add throughput uplift or error-cost reduction beyond labor.",
            )
        )

    ind_key = _norm_industry(inputs.industry)
    benchmark = INDUSTRY_BENCHMARKS.get(ind_key)
    if benchmark and payback < 900:
        lo, hi = benchmark["payback_months"]
        if payback < lo * 0.7:
            issues.append(
                RoiValidationIssue(
                    code="below_benchmark",
                    severity="warning",
                    message=f"Payback is faster than typical {benchmark['label']} deployments ({lo}–{hi} mo).",
                    suggestion="Document non-labor benefits or pilot assumptions so buyers trust the model.",
                )
            )
        if payback > hi * 1.4:
            issues.append(
                RoiValidationIssue(
                    code="above_benchmark",
                    severity="info",
                    message=f"Payback exceeds typical {benchmark['label']} range ({lo}–{hi} mo).",
                    suggestion="Show phased rollout or multi-site scale to improve economics.",
                )
            )

    corrected = False
    if inputs.buyer_stated_payback_months and payback < 900:
        delta = abs(inputs.buyer_stated_payback_months - payback) / max(payback, 1)
        if delta > 0.25:
            issues.append(
                RoiValidationIssue(
                    code="buyer_payback_mismatch",
                    severity="error",
                    message=(
                        f"Buyer stated {inputs.buyer_stated_payback_months:.0f} mo payback; "
                        f"corrected model shows {payback:.1f} mo."
                    ),
                    suggestion="Buyer likely omitted maintenance, used base wage only, or double-counted labor.",
                )
            )
            corrected = True

    if inputs.buyer_stated_annual_savings and annual_net > 0:
        delta_s = abs(inputs.buyer_stated_annual_savings - annual_net) / annual_net
        if delta_s > 0.2:
            issues.append(
                RoiValidationIssue(
                    code="buyer_savings_mismatch",
                    severity="error",
                    message=(
                        f"Buyer stated ${inputs.buyer_stated_annual_savings:,.0f}/yr savings; "
                        f"corrected model shows ${annual_net:,.0f}/yr."
                    ),
                    suggestion="Reconcile FTE overlap, shift coverage, and ongoing service costs.",
                )
            )
            corrected = True

    roi_y1 = ((annual_net - total_capex) / total_capex * 100) if total_capex > 0 else 0.0
    roi_y3 = (((annual_net * 3) - total_capex) / total_capex * 100) if total_capex > 0 else 0.0
    net_3 = annual_net * 3 - total_capex

    return RoiModelResult(
        annual_labor_baseline=round(annual_labor, 2),
        annual_labor_replaced=round(annual_labor_replaced, 2),
        annual_maintenance=round(annual_maintenance, 2),
        annual_net_savings=round(annual_net, 2),
        total_capex=round(total_capex, 2),
        payback_months=round(payback, 1) if payback < 900 else 0.0,
        roi_year_1_pct=round(roi_y1, 1),
        roi_year_3_pct=round(roi_y3, 1),
        net_savings_3yr=round(net_3, 2),
        issues=issues,
        benchmark=benchmark,
        corrected_from_buyer=corrected,
    )


def default_workflow_layout(industry: str = "") -> Dict[str, Any]:
    """Starter floor plan — vendor edits zones, robots, and flows."""
    ind = _norm_industry(industry)
    if ind == "hospitality":
        zones = [
            {"id": "lobby", "label": "Lobby / Check-in", "x": 40, "y": 40, "w": 180, "h": 100, "kind": "human"},
            {"id": "corridor", "label": "Guest corridors", "x": 240, "y": 40, "w": 200, "h": 100, "kind": "handoff"},
            {"id": "rooms", "label": "Guest floors", "x": 460, "y": 40, "w": 180, "h": 100, "kind": "process"},
            {"id": "stock", "label": "Housekeeping stock", "x": 40, "y": 180, "w": 160, "h": 90, "kind": "storage"},
        ]
        robots = [
            {
                "id": "r1",
                "robot_label": "Delivery AMR",
                "zone_id": "corridor",
                "x": 320,
                "y": 90,
                "tasks": ["Linens", "amenities", "room service"],
                "impact": {"labor_hours_saved_per_week": 28, "throughput_delta_pct": 15},
            }
        ]
        flows = [
            {"id": "f1", "from_zone_id": "stock", "to_zone_id": "corridor", "label": "Stock refill", "automated": True},
            {"id": "f2", "from_zone_id": "corridor", "to_zone_id": "rooms", "label": "Guest delivery", "automated": True},
        ]
    elif ind == "logistics":
        zones = [
            {"id": "inbound", "label": "Inbound dock", "x": 30, "y": 50, "w": 150, "h": 90, "kind": "human"},
            {"id": "pick", "label": "Pick zone", "x": 200, "y": 50, "w": 180, "h": 90, "kind": "process"},
            {"id": "pack", "label": "Pack / ship", "x": 400, "y": 50, "w": 160, "h": 90, "kind": "process"},
            {"id": "staging", "label": "AMR staging", "x": 200, "y": 170, "w": 200, "h": 80, "kind": "storage"},
        ]
        robots = [
            {
                "id": "r1",
                "robot_label": "Pallet AMR",
                "zone_id": "staging",
                "x": 300,
                "y": 210,
                "tasks": ["Pallet move", "dock-to-pick"],
                "impact": {"labor_hours_saved_per_week": 45, "throughput_delta_pct": 22},
            }
        ]
        flows = [
            {"id": "f1", "from_zone_id": "inbound", "to_zone_id": "pick", "label": "Replenishment", "automated": True},
            {"id": "f2", "from_zone_id": "pick", "to_zone_id": "pack", "label": "Order flow", "automated": False},
        ]
    else:
        zones = [
            {"id": "z1", "label": "Manual process", "x": 40, "y": 60, "w": 200, "h": 100, "kind": "human"},
            {"id": "z2", "label": "Automation zone", "x": 280, "y": 60, "w": 200, "h": 100, "kind": "robot"},
            {"id": "z3", "label": "Output / QC", "x": 520, "y": 60, "w": 160, "h": 100, "kind": "process"},
        ]
        robots = [
            {
                "id": "r1",
                "robot_label": "Robot cell",
                "zone_id": "z2",
                "x": 380,
                "y": 110,
                "tasks": ["Primary task"],
                "impact": {"labor_hours_saved_per_week": 20, "throughput_delta_pct": 10},
            }
        ]
        flows = [
            {"id": "f1", "from_zone_id": "z1", "to_zone_id": "z2", "label": "Handoff", "automated": True},
            {"id": "f2", "from_zone_id": "z2", "to_zone_id": "z3", "label": "Finish", "automated": True},
        ]

    return {
        "width": 720,
        "height": 320,
        "zones": zones,
        "robots": robots,
        "flows": flows,
    }


def summarize_workflow_impact(layout: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate robot impact from layout for buyer summary."""
    robots = layout.get("robots") or []
    hrs = 0.0
    throughput = 0.0
    for r in robots:
        imp = r.get("impact") or {}
        hrs += float(imp.get("labor_hours_saved_per_week") or 0)
        throughput = max(throughput, float(imp.get("throughput_delta_pct") or 0))
    automated_flows = sum(1 for f in (layout.get("flows") or []) if f.get("automated"))
    return {
        "robot_count": len(robots),
        "labor_hours_saved_per_week": round(hrs, 1),
        "peak_throughput_delta_pct": round(throughput, 1),
        "automated_handoffs": automated_flows,
    }


def new_share_id() -> str:
    return secrets.token_urlsafe(6).replace("-", "")[:10]
