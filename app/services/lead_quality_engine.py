"""Lead quality scorecard for buyer-intent pipeline quality.

This module provides:
1) A five-dimension lead quality schema.
2) Confidence band + evidence traces.
3) Outcome-aware reweight recommendations from rep feedback.
4) Monitoring snapshot fields for admin tuning.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.lead_rep_feedback import LeadRepFeedback


BASE_QUALITY_WEIGHTS: dict[str, float] = {
    "buyer_authenticity": 0.27,
    "urgency_window": 0.24,
    "robot_fit_confidence": 0.2,
    "decision_maker_confidence": 0.16,
    "contactability_confidence": 0.13,
}


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(v or 0.0)) for v in weights.values())
    if total <= 0:
        return dict(BASE_QUALITY_WEIGHTS)
    return {k: round(max(0.0, float(v or 0.0)) / total, 4) for k, v in weights.items()}


def _timing_confidence(project_timing: Optional[dict]) -> float:
    if not isinstance(project_timing, dict):
        return 0.0
    raw = float(project_timing.get("confidence") or 0.0)
    return _clamp(raw * 100.0 if raw <= 1.0 else raw)


def compute_lead_quality_profile(
    *,
    priority_tier: str,
    priority_score: float,
    is_junk: bool,
    junk_reason: Optional[str],
    overall_score: float,
    signal_count: int,
    crm_evidence: Optional[dict],
    project_timing: Optional[dict],
    robot_types_needed: Optional[list[str]],
    has_contact_path: bool,
    weights: Optional[dict[str, float]] = None,
    weight_source: str = "baseline_v1",
) -> dict[str, Any]:
    """Compute 5-dimension quality score + confidence + evidence traces."""
    w = _normalize_weights(weights or BASE_QUALITY_WEIGHTS)
    evidence = crm_evidence if isinstance(crm_evidence, dict) else {}
    missing_fields = evidence.get("missing_fields") if isinstance(evidence.get("missing_fields"), list) else []
    decision_makers = evidence.get("decision_makers") if isinstance(evidence.get("decision_makers"), list) else []
    similar_deployments = evidence.get("similar_deployments") if isinstance(evidence.get("similar_deployments"), list) else []
    robot_type_block = evidence.get("robot_type") if isinstance(evidence.get("robot_type"), dict) else {}

    tier = (priority_tier or "").upper()
    tier_score = 95.0 if tier == "HOT" else 72.0 if tier == "WARM" else 44.0

    buyer_auth = 10.0 if is_junk else _clamp(78.0 + min(22.0, max(0.0, priority_score) * 0.2))
    urgency = _clamp((tier_score * 0.55) + (overall_score * 0.25) + (_timing_confidence(project_timing) * 0.2))

    robot_items = [x for x in (robot_types_needed or []) if x]
    fit_depth = len(robot_items) + (1 if robot_type_block.get("label") else 0) + min(2, len(similar_deployments))
    robot_fit = _clamp(35.0 + (fit_depth * 15.0) + min(20.0, signal_count * 1.5))

    dm_count = len(decision_makers)
    decision_conf = _clamp(20.0 + (dm_count * 22.0))

    contactability = 92.0 if has_contact_path else 38.0

    dimensions = {
        "buyer_authenticity": round(buyer_auth, 1),
        "urgency_window": round(urgency, 1),
        "robot_fit_confidence": round(robot_fit, 1),
        "decision_maker_confidence": round(decision_conf, 1),
        "contactability_confidence": round(contactability, 1),
    }

    raw = sum(dimensions[k] * w.get(k, 0.0) for k in dimensions)

    present_signals = 0
    if not is_junk:
        present_signals += 1
    if _timing_confidence(project_timing) > 0:
        present_signals += 1
    if robot_items:
        present_signals += 1
    if dm_count > 0:
        present_signals += 1
    if has_contact_path:
        present_signals += 1

    if present_signals >= 4 and len(missing_fields) <= 1:
        band = "high"
        penalty = 1.0
    elif present_signals >= 2:
        band = "medium"
        penalty = 0.92
    else:
        band = "low"
        penalty = 0.8

    overall_quality = round(_clamp(raw * penalty), 1)

    traces = [
        {
            "dimension": "buyer_authenticity",
            "score": dimensions["buyer_authenticity"],
            "evidence": "Junk gate passed" if not is_junk else f"Flagged as junk ({junk_reason or 'unknown reason'})",
        },
        {
            "dimension": "urgency_window",
            "score": dimensions["urgency_window"],
            "evidence": f"Tier {tier or 'COLD'} with timing confidence {_timing_confidence(project_timing):.1f}",
        },
        {
            "dimension": "robot_fit_confidence",
            "score": dimensions["robot_fit_confidence"],
            "evidence": f"Robot matches: {len(robot_items)}; deployment examples: {len(similar_deployments)}",
        },
        {
            "dimension": "decision_maker_confidence",
            "score": dimensions["decision_maker_confidence"],
            "evidence": f"Decision makers identified: {dm_count}",
        },
        {
            "dimension": "contactability_confidence",
            "score": dimensions["contactability_confidence"],
            "evidence": "Contact path available" if has_contact_path else "No verified contact path yet",
        },
    ]

    return {
        "schema": "lead_quality_v1",
        "overall_score": overall_quality,
        "confidence_band": band,
        "dimension_scores": dimensions,
        "weights": w,
        "weight_source": weight_source,
        "missing_fields_count": len(missing_fields),
        "evidence_traces": traces,
        "quality_gate": {
            "passed": band != "low",
            "reason": "insufficient evidence" if band == "low" else "evidence sufficient",
        },
    }


def build_outcome_reweight_snapshot(
    db: Session,
    *,
    lookback_days: int = 14,
) -> dict[str, Any]:
    """Aggregate feedback outcomes and suggest weight adjustments.

    This is a lightweight reweighting loop starter using rep feedback outcomes.
    """
    since = datetime.now(timezone.utc) - timedelta(days=max(1, int(lookback_days)))
    rows = (
        db.query(LeadRepFeedback.vote, LeadRepFeedback.reason_code, func.count(LeadRepFeedback.id))
        .filter(LeadRepFeedback.created_at >= since)
        .group_by(LeadRepFeedback.vote, LeadRepFeedback.reason_code)
        .all()
    )

    totals = {"up": 0, "down": 0}
    reasons: dict[str, int] = {}
    for vote, reason_code, count in rows:
        v = (vote or "").lower()
        n = int(count or 0)
        if v in totals:
            totals[v] += n
        if reason_code:
            reasons[str(reason_code)] = reasons.get(str(reason_code), 0) + n

    total = totals["up"] + totals["down"]
    down = totals["down"]
    up = totals["up"]
    wrong_company = reasons.get("wrong_company", 0)
    not_ready = reasons.get("not_ready", 0)
    spam = reasons.get("spam", 0)

    down_den = max(1, down)
    contamination_rate = round((wrong_company + spam) / down_den * 100.0, 1) if down > 0 else 0.0
    timing_mismatch_rate = round(not_ready / down_den * 100.0, 1) if down > 0 else 0.0
    up_rate = round((up / max(1, total)) * 100.0, 1)

    deltas = {
        "buyer_authenticity": 0.0,
        "urgency_window": 0.0,
        "robot_fit_confidence": 0.0,
        "decision_maker_confidence": 0.0,
        "contactability_confidence": 0.0,
    }

    notes: list[str] = []
    if contamination_rate >= 25.0:
        deltas["buyer_authenticity"] += 0.06
        notes.append("High contamination feedback — increase buyer_authenticity weight.")
    if timing_mismatch_rate >= 25.0:
        deltas["urgency_window"] += 0.05
        notes.append("Frequent not_ready feedback — increase urgency_window weight.")
    if up_rate < 35.0 and total >= 10:
        deltas["decision_maker_confidence"] += 0.03
        deltas["contactability_confidence"] += 0.03
        notes.append("Low positive feedback rate — increase decision-maker/contactability emphasis.")

    adjusted = {k: BASE_QUALITY_WEIGHTS[k] + deltas.get(k, 0.0) for k in BASE_QUALITY_WEIGHTS}
    adjusted = _normalize_weights(adjusted)

    return {
        "lookback_days": int(lookback_days),
        "window_since": since.isoformat(),
        "feedback_totals": {
            "total": total,
            "up": up,
            "down": down,
            "up_rate": up_rate,
        },
        "reason_counts": reasons,
        "quality_signals": {
            "contamination_rate": contamination_rate,
            "timing_mismatch_rate": timing_mismatch_rate,
        },
        "base_weights": dict(BASE_QUALITY_WEIGHTS),
        "recommended_weights": adjusted,
        "notes": notes,
        "source": "rep_feedback_loop_v1",
    }


def build_lead_quality_monitoring_snapshot(db: Session, *, lookback_days: int = 14) -> dict[str, Any]:
    """Dashboard-facing summary fields for weekly quality tuning."""
    outcome = build_outcome_reweight_snapshot(db, lookback_days=lookback_days)

    since = datetime.now(timezone.utc) - timedelta(days=max(1, int(lookback_days)))
    recent_feedback = (
        db.query(LeadRepFeedback.company_id, func.count(LeadRepFeedback.id))
        .filter(LeadRepFeedback.created_at >= since)
        .group_by(LeadRepFeedback.company_id)
        .all()
    )
    covered_companies = len(recent_feedback)

    top_feedback_companies = []
    if recent_feedback:
        top_ids = [cid for cid, _ in sorted(recent_feedback, key=lambda x: int(x[1] or 0), reverse=True)[:10]]
        if top_ids:
            names = {
                c.id: c.name
                for c in db.query(Company.id, Company.name).filter(Company.id.in_(top_ids)).all()
            }
            for cid, n in sorted(recent_feedback, key=lambda x: int(x[1] or 0), reverse=True)[:5]:
                top_feedback_companies.append(
                    {
                        "company_id": int(cid),
                        "company_name": names.get(cid) or f"Company {cid}",
                        "feedback_count": int(n or 0),
                    }
                )

    return {
        "schema": "lead_quality_monitoring_v1",
        "lookback_days": int(lookback_days),
        "feedback_coverage_companies": covered_companies,
        "top_feedback_companies": top_feedback_companies,
        "outcome_reweight": outcome,
    }
