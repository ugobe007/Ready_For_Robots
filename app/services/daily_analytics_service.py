"""
Daily Analytics Report — Opportunity Intelligence from Signals
==============================================================
Answers: What automation is inferred? What robots/specs are needed?
ROI expectations? Common tasks to automate? Industry/geography trends?
"""
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.models.robot import Robot
from app.models.shared_calculation import SharedCalculation


# ── Signal Type → Automation Category (what type of automation is inferred) ──
SIGNAL_TO_AUTOMATION_TYPE: Dict[str, str] = {
    "robot_installation": "deployment",
    "pilot_success": "deployment",
    "scale_expansion": "deployment",
    "vendor_selection": "procurement",
    "automation_interest": "evaluation",
    "capex": "budget_allocated",
    "expansion": "new_facility",
    "labor_shortage": "labor_replacement",
    "labor_pain": "labor_replacement",
    "strategic_hire": "decision_maker_change",
    "funding_round": "capital_available",
    "ma_activity": "integration_or_consolidation",
    "roi_documented": "roi_proven",
    "economics_driven": "cost_justification",
    "competitive_response": "competitive_pressure",
    "problem_solution": "problem_solution",
    "rfp_posted": "active_procurement",
    "government_contract": "procurement",
    "news": "general_awareness",
}


# ── Signal Type → Likely Robot Types (from opportunity context) ──
SIGNAL_TO_ROBOT_TYPES: Dict[str, List[str]] = {
    "robot_installation": ["delivery", "disinfection", "cleaning", "logistics", "service"],
    "pilot_success": ["delivery", "disinfection", "cleaning", "logistics", "service"],
    "automation_interest": ["delivery", "disinfection", "cleaning", "logistics", "service", "bartender"],
    "labor_shortage": ["delivery", "cleaning", "logistics", "service"],
    "labor_pain": ["delivery", "cleaning", "logistics", "service"],
    "expansion": ["logistics", "cleaning", "delivery"],
    "capex": ["logistics", "cleaning", "delivery", "disinfection"],
}


# ── Task keywords to extract from signal_text (what tasks are being automated) ──
TASK_KEYWORDS: Dict[str, List[str]] = {
    "floor_cleaning": ["floor cleaning", "floor scrubber", "autonomous scrubber", "mopping", "sweeping"],
    "disinfection": ["disinfection", "uv-c", "uvc", "sanitiz", "germ", "pathogen"],
    "delivery": ["delivery", "room service", "medication delivery", "food delivery", "linen delivery"],
    "housekeeping": ["housekeeping", "housekeeper", "room attendant", "room cleaning", "turndown"],
    "warehouse_picking": ["picking", "order fulfillment", "order picking", "warehouse picking", "putaway"],
    "material_handling": ["material handling", "agv", "amr", "forklift", "pallet", "conveyor"],
    "inventory": ["inventory", "stock counting", "cycle count", "warehouse management"],
    "patient_transport": ["patient transport", "linen transport", "specimen transport", "hospital logistics"],
    "food_prep": ["food prep", "cooking robot", "kitchen automation", "fryer", "grill"],
    "food_serving": ["food serving", "server robot", "waiter", "dining room"],
    "security_patrol": ["security", "patrol", "knightscope", "surveillance"],
    "front_desk": ["front desk", "concierge", "check-in", "greeting"],
}


# ── ROI / Trial / Payback keywords ──
ROI_KEYWORDS = [
    "roi", "return on investment", "payback", "payback period", "break-even",
    "cost savings", "labor savings", "saves $", "reduced costs", "efficiency gains",
    "productivity increase", "% faster", "% reduction", "months to payback",
]
TRIAL_KEYWORDS = [
    "pilot", "trial", "proof of concept", "poc", "testing", "evaluation",
    "pilot program", "trial period", "pilot expansion", "rollout",
]
SPEC_KEYWORDS = {
    "payload": [r"payload\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:kg|lb)", r"(\d+)\s*(?:kg|lb)\s*(?:payload|capacity)"],
    "battery": [r"battery\s*(?:life|:)?\s*(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)", r"(\d+)\s*(?:hours?|hrs?)\s*(?:battery|runtime)"],
    "speed": [r"speed\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:mps|mph|km/h)", r"(\d+)\s*(?:mps|mph)\s*(?:max)?"],
    "payback_months": [r"payback\s*(?:in|of)?\s*(\d+)\s*months?", r"(\d+)\s*month\s*payback", r"roi\s*(?:in|within)?\s*(\d+)\s*months?"],
}


def _extract_from_text(text: str, keywords: List[str]) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def _extract_tasks(text: str) -> List[str]:
    """Extract task types mentioned in signal text."""
    found = []
    lower = (text or "").lower()
    for task, kws in TASK_KEYWORDS.items():
        if any(kw in lower for kw in kws):
            found.append(task)
    return found


def _extract_roi_mentions(text: str) -> bool:
    return _extract_from_text(text, ROI_KEYWORDS)


def _extract_trial_mentions(text: str) -> bool:
    return _extract_from_text(text, TRIAL_KEYWORDS)


def _extract_specs(text: str) -> Dict[str, Any]:
    """Extract numeric specs from signal text."""
    if not text:
        return {}
    specs = {}
    for spec_name, patterns in SPEC_KEYWORDS.items():
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    specs[spec_name] = float(m.group(1))
                    break
                except (ValueError, IndexError):
                    pass
    return specs


def _infer_robot_types_from_text(text: str) -> List[str]:
    """Infer robot types from task keywords and common robot mentions."""
    inferred = []
    lower = (text or "").lower()
    # Map tasks to robot types
    if any(kw in lower for kw in ["delivery", "room service", "medication"]):
        inferred.append("delivery")
    if any(kw in lower for kw in ["disinfection", "uv-c", "uvc", "sanitiz"]):
        inferred.append("disinfection")
    if any(kw in lower for kw in ["cleaning", "scrubber", "floor", "housekeeping"]):
        inferred.append("cleaning")
    if any(kw in lower for kw in ["agv", "amr", "warehouse", "picking", "logistics", "forklift"]):
        inferred.append("logistics")
    if any(kw in lower for kw in ["service robot", "hospitality", "concierge"]):
        inferred.append("service")
    if any(kw in lower for kw in ["bartender", "beverage", "drink"]):
        inferred.append("bartender")
    return list(dict.fromkeys(inferred))  # dedupe preserving order


def get_daily_analytics(db: Session, days: int = 1) -> Dict[str, Any]:
    """
    Generate daily analytics report from opportunity signals.
    
    Returns structured data for:
    - Automation types inferred
    - Robot types needed
    - Specs mentioned
    - ROI/trial expectations
    - Common tasks to automate
    - Industry/geography/trends
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    signals = (
        db.query(Signal)
        .join(Company)
        .filter(Signal.created_at >= cutoff)
        .order_by(desc(Signal.created_at))
        .all()
    )
    
    companies_with_signals = (
        db.query(Company)
        .join(Signal)
        .filter(Signal.created_at >= cutoff)
        .distinct()
        .all()
    )
    
    # ── 1. Automation types inferred ──
    automation_type_counts: Counter = Counter()
    for s in signals:
        at = SIGNAL_TO_AUTOMATION_TYPE.get(s.signal_type, s.signal_type)
        automation_type_counts[at] += 1
    
    # ── 2. Robot types needed ──
    robot_type_counts: Counter = Counter()
    for s in signals:
        types_from_signal = SIGNAL_TO_ROBOT_TYPES.get(s.signal_type, [])
        types_from_text = _infer_robot_types_from_text(s.signal_text)
        for t in types_from_signal + types_from_text:
            robot_type_counts[t] += 1
    
    # ── 3. Specs mentioned in signals ──
    specs_mentioned: Dict[str, List[float]] = {}
    for s in signals:
        extracted = _extract_specs(s.signal_text)
        for k, v in extracted.items():
            specs_mentioned.setdefault(k, []).append(v)
    
    avg_specs = {k: round(sum(v) / len(v), 2) for k, v in specs_mentioned.items() if v}
    
    # ── 4. ROI & trial expectations ──
    roi_mention_count = sum(1 for s in signals if _extract_roi_mentions(s.signal_text))
    trial_mention_count = sum(1 for s in signals if _extract_trial_mentions(s.signal_text))
    
    # SharedCalculation ROI data (calculator usage)
    try:
        calc_stats = db.query(
            func.avg(SharedCalculation.payback_months).label("avg_payback"),
            func.avg(SharedCalculation.roi_1_year).label("avg_roi_1y"),
            func.count(SharedCalculation.id).label("count"),
        ).filter(SharedCalculation.created_at >= cutoff).first()
    except Exception:
        calc_stats = None
    
    # ── 5. Common tasks to automate ──
    task_counts: Counter = Counter()
    for s in signals:
        for task in _extract_tasks(s.signal_text):
            task_counts[task] += 1
    
    # ── 6. Signal type breakdown ──
    signal_type_counts = Counter(s.signal_type for s in signals)
    
    # ── 7. Industry breakdown ──
    industry_counts = Counter()
    for c in companies_with_signals:
        ind = c.industry or "Unknown"
        industry_counts[ind] += 1
    
    # ── 8. Top companies by signal count ──
    company_signal_counts = (
        db.query(Company.name, func.count(Signal.id).label("cnt"))
        .join(Signal)
        .filter(Signal.created_at >= cutoff)
        .group_by(Company.id, Company.name)
        .order_by(desc("cnt"))
        .limit(10)
        .all()
    )
    
    # ── 9. Geography (state/country) ──
    state_counts = Counter(c.location_state for c in companies_with_signals if c.location_state)
    country_counts = Counter(c.location_country for c in companies_with_signals if c.location_country)
    
    # ── 10. Robot catalog reference (available types + specs) ──
    robots = db.query(Robot).filter(Robot.is_active == True).all()
    robot_catalog_summary = [
        {
            "name": r.name,
            "vendor": r.vendor,
            "type": r.robot_type,
            "payload_kg": r.payload_capacity_kg,
            "battery_hours": r.battery_life_hours,
            "roi_stat": r.roi_stat,
        }
        for r in robots[:20]
    ]
    
    return {
        "period_days": days,
        "cutoff": cutoff.isoformat(),
        "totals": {
            "signals": len(signals),
            "companies_with_signals": len(companies_with_signals),
        },
        "automation_types_inferred": dict(automation_type_counts.most_common(15)),
        "robot_types_needed": dict(robot_type_counts.most_common(10)),
        "specs_mentioned_in_signals": avg_specs,
        "spec_raw_counts": {k: len(v) for k, v in specs_mentioned.items()},
        "roi_mentions": roi_mention_count,
        "trial_pilot_mentions": trial_mention_count,
        "common_tasks_to_automate": dict(task_counts.most_common(15)),
        "signal_types": dict(signal_type_counts.most_common(15)),
        "industries": dict(industry_counts.most_common(15)),
        "top_companies_by_signals": [{"name": n, "signals": c} for n, c in company_signal_counts],
        "top_states": dict(state_counts.most_common(10)),
        "top_countries": dict(country_counts.most_common(10)),
        "calculator_roi_summary": {
            "avg_payback_months": round(calc_stats.avg_payback, 1) if calc_stats and calc_stats.avg_payback else None,
            "avg_roi_1_year_pct": round(calc_stats.avg_roi_1y, 1) if calc_stats and calc_stats.avg_roi_1y else None,
            "calculations_count": calc_stats.count if calc_stats else 0,
        } if calc_stats else {},
        "robot_catalog_sample": robot_catalog_summary,
    }


def format_report_markdown(analytics: Dict[str, Any]) -> str:
    """Format analytics as a human-readable markdown report."""
    lines = []
    lines.append("# Daily Opportunity Analytics Report")
    lines.append(f"**Period:** Last {analytics['period_days']} day(s)")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    
    totals = analytics["totals"]
    lines.append("## Summary")
    lines.append(f"- **Signals analyzed:** {totals['signals']}")
    lines.append(f"- **Companies with opportunities:** {totals['companies_with_signals']}")
    lines.append("")
    
    lines.append("## Automation Types Inferred")
    lines.append("What type of automation is required or inferred from opportunity postings:")
    for atype, count in list(analytics.get("automation_types_inferred", {}).items())[:10]:
        pct = (count / totals["signals"] * 100) if totals["signals"] else 0
        lines.append(f"- **{atype.replace('_', ' ').title()}:** {count} ({pct:.1f}%)")
    lines.append("")
    
    lines.append("## Robot Types Needed")
    lines.append("What type of robots are implied by the opportunities:")
    for rtype, count in list(analytics.get("robot_types_needed", {}).items())[:10]:
        pct = (count / totals["signals"] * 100) if totals["signals"] else 0
        lines.append(f"- **{rtype}:** {count} ({pct:.1f}%)")
    lines.append("")
    
    specs = analytics.get("specs_mentioned_in_signals", {})
    if specs:
        lines.append("## Specs Mentioned in Opportunities")
        for spec, val in specs.items():
            lines.append(f"- **{spec.replace('_', ' ').title()}:** avg {val} (from {analytics.get('spec_raw_counts', {}).get(spec, 0)} mentions)")
        lines.append("")
    
    lines.append("## ROI & Trial Expectations")
    lines.append(f"- **Signals mentioning ROI/payback:** {analytics.get('roi_mentions', 0)}")
    lines.append(f"- **Signals mentioning pilot/trial:** {analytics.get('trial_pilot_mentions', 0)}")
    calc = analytics.get("calculator_roi_summary", {})
    if calc.get("avg_payback_months"):
        lines.append(f"- **Avg payback (from calculator):** {calc['avg_payback_months']} months")
    if calc.get("avg_roi_1_year_pct"):
        lines.append(f"- **Avg 1-year ROI (from calculator):** {calc['avg_roi_1_year_pct']}%")
    lines.append("")
    
    lines.append("## Most Common Tasks to Automate")
    for task, count in list(analytics.get("common_tasks_to_automate", {}).items())[:10]:
        pct = (count / totals["signals"] * 100) if totals["signals"] else 0
        lines.append(f"- **{task.replace('_', ' ').title()}:** {count} ({pct:.1f}%)")
    lines.append("")
    
    lines.append("## Signal Types (Buying Intent)")
    for stype, count in list(analytics.get("signal_types", {}).items())[:10]:
        pct = (count / totals["signals"] * 100) if totals["signals"] else 0
        lines.append(f"- **{stype}:** {count} ({pct:.1f}%)")
    lines.append("")
    
    lines.append("## Industries")
    for ind, count in list(analytics.get("industries", {}).items())[:10]:
        lines.append(f"- **{ind}:** {count}")
    lines.append("")
    
    lines.append("## Top Companies by Signal Count")
    for c in analytics.get("top_companies_by_signals", [])[:5]:
        lines.append(f"- **{c['name']}:** {c['signals']} signals")
    lines.append("")
    
    if analytics.get("top_states"):
        lines.append("## Top States")
        for state, count in list(analytics["top_states"].items())[:5]:
            lines.append(f"- **{state}:** {count}")
        lines.append("")
    
    return "\n".join(lines)
