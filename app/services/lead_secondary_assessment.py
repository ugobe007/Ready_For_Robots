"""
Secondary logic assessment — five pillars applied after primary ingestion.

1. Missing data     — what fields are absent for a sales-ready record?
2. Optimize data    — normalize industry, identity, CRM descriptors
3. Quality gate     — junk vs real sales lead (rectifier + classifier)
4. Additional data  — ontology gaps, agent facts, procurement/timing cues
5. Opportunity rank — value of each data dimension for the sales motion

Persisted on ``companies.crm_metadata.secondary_assessment`` after each secondary pass.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.models.signal import Signal
from app.services.automation_profile import get_automation_profile_for_response
from app.services.gtm_readiness import compute_gtm_readiness
from app.services.lead_filter import classify_lead, pick_primary_score
from app.services.lead_gap_audit import LeadGapReport, audit_company_gaps
from app.services.lead_value import compute_lead_value
from app.services.text_classifier import classify as classify_name

# Pillar labels (stable API for ops / CRM consumers)
PILLAR_MISSING = "missing_data"
PILLAR_OPTIMIZE = "optimize_data"
PILLAR_QUALITY = "quality_gate"
PILLAR_ADDITIONAL = "additional_data"
PILLAR_RANK = "opportunity_rank"

PASS_VALUE_ASSESSMENT = "value_assessment"

_DATA_VALUE_WEIGHTS: Dict[str, float] = {
    "website": 0.12,
    "contact": 0.18,
    "industry": 0.08,
    "crm_descriptors": 0.14,
    "lead_inference": 0.16,
    "signals": 0.12,
    "quality_passed": 0.12,
    "agent_enrichment": 0.08,
}


def _completeness_score(gaps: Sequence[str]) -> float:
    """1.0 = no open gaps in audited dimensions."""
    if not gaps:
        return 1.0
    max_dims = 8
    return max(0.0, 1.0 - len(list(gaps)) / max_dims)


def _data_dimension_scores(
    gaps: Sequence[str],
    *,
    quality_passed: bool,
    has_agent: bool,
) -> Dict[str, float]:
    open_gaps = set(gaps)
    scores: Dict[str, float] = {}
    scores["website"] = 0.0 if "website" in open_gaps else 1.0
    scores["contact"] = 0.0 if "contact" in open_gaps else 1.0
    scores["industry"] = 0.0 if "industry" in open_gaps else 1.0
    scores["crm_descriptors"] = 0.0 if "crm_descriptors" in open_gaps else 1.0
    scores["lead_inference"] = 0.0 if "lead_inference" in open_gaps else 1.0
    scores["signals"] = 0.0 if "low_signals" in open_gaps else 1.0
    scores["quality_passed"] = 1.0 if quality_passed else 0.0
    scores["agent_enrichment"] = 1.0 if has_agent else 0.0
    return scores


def _weighted_data_value(dimension_scores: Dict[str, float]) -> float:
    total_w = sum(_DATA_VALUE_WEIGHTS.values())
    if total_w <= 0:
        return 0.0
    acc = sum(
        dimension_scores.get(k, 0.0) * w for k, w in _DATA_VALUE_WEIGHTS.items()
    )
    return round(100.0 * acc / total_w, 2)


def build_secondary_assessment(
    company: Company,
    signals: Sequence[Signal],
    contacts: Sequence[Contact],
    *,
    gaps_report: Optional[LeadGapReport] = None,
    pass_outcomes: Optional[Dict[str, str]] = None,
    fields_filled: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Synthesize the five secondary pillars for one lead after rescue passes.
    """
    score_row = pick_primary_score(company.scores)
    intent = float(score_row.overall_intent_score or 0) if score_row else 0.0

    gap_report = gaps_report or audit_company_gaps(
        company, signals, contacts, overall_score=intent
    )
    gaps = list(gap_report.gaps)
    meta = company.crm_metadata if isinstance(company.crm_metadata, dict) else {}
    ledger = meta.get("enrichment_ledger") if isinstance(meta.get("enrichment_ledger"), dict) else {}

    # ── Pillar 3: Quality gate (junk vs sales lead) ───────────────────────
    junk, junk_reason, pri = classify_lead(company, company.scores, list(signals))
    name_tc = classify_name(company.name or "")
    rect_passed = ledger.get("rectification", {}).get("status") == "passed"
    is_sales_lead = (
        not junk
        and company.is_internal is not False
        and rect_passed
        and pri.tier in {"HOT", "WARM", "COLD"}
    )

    quality = {
        "is_junk": junk,
        "junk_reason": junk_reason or None,
        "is_sales_lead": is_sales_lead,
        "tier": pri.tier,
        "tier_reasons": list(pri.reasons or [])[:6],
        "rectification_passed": rect_passed,
        "name_entity_type": name_tc.entity_type.value if name_tc else None,
        "name_confidence": round(float(name_tc.confidence), 3) if name_tc else None,
        "recommendation": (
            "quarantine" if junk or not rect_passed
            else "prioritize" if pri.tier == "HOT"
            else "nurture" if pri.tier == "WARM"
            else "monitor"
        ),
    }

    # ── Pillar 2: Optimize (what improved this run) ───────────────────────
    optimized = list(dict.fromkeys(fields_filled or []))
    if pass_outcomes:
        for pass_name, status in pass_outcomes.items():
            if status in ("filled", "passed") and pass_name not in optimized:
                optimized.append(pass_name)

    # ── Pillar 4: Additional data considered ────────────────────────────────
    agent = meta.get("agent_enrichment") if isinstance(meta.get("agent_enrichment"), dict) else {}
    inf = meta.get("lead_inference") if isinstance(meta.get("lead_inference"), dict) else {}
    automation_profile = get_automation_profile_for_response(company)
    lv = compute_lead_value(
        intent,
        company.employee_estimate,
        automation_profile,
        list(signals),
        extra_timeline_text=(meta.get("project_timing") or {}).get("label")
        if isinstance(meta.get("project_timing"), dict)
        else None,
    )
    gtm = compute_gtm_readiness(list(signals), pri.tier, pri.reasons)

    proc = inf.get("procurement")
    proc_hints: List[str] = list(agent.get("procurement_clues") or [])[:6]
    if isinstance(proc, dict) and proc.get("stage") and proc["stage"] not in proc_hints:
        proc_hints.insert(0, str(proc["stage"]))

    additional = {
        "ontology_gaps": list(agent.get("ontology_gaps") or [])[:6],
        "rich_facts_count": len(agent.get("rich_facts") or []),
        "procurement_clues": proc_hints[:6],
        "timing_clues": list(agent.get("timing_clues") or [])[:6],
        "robot_categories": list(inf.get("robot_categories") or [])[:4],
        "signal_types": list(
            dict.fromkeys(getattr(s, "signal_type", "") for s in signals if getattr(s, "signal_type", ""))
        )[:8],
        "gtm_stage": gtm.get("readiness_stage"),
        "gtm_why_now": list(gtm.get("why_now") or [])[:4],
    }

    # ── Pillar 5: Opportunity rank ──────────────────────────────────────────
    dim_scores = _data_dimension_scores(
        gaps,
        quality_passed=rect_passed and not junk,
        has_agent=bool(agent),
    )
    data_value = _weighted_data_value(dim_scores)
    lead_value = float(lv.get("lead_value_score") or 0)
    completeness = _completeness_score(gaps)

    # Sales opportunity rank: deal quality + intent + data completeness
    sales_opportunity_rank = round(
        0.45 * lead_value + 0.35 * intent + 0.20 * (data_value * completeness),
        2,
    )

    rank = {
        "sales_opportunity_rank": sales_opportunity_rank,
        "lead_value_score": lead_value,
        "lead_value_components": lv.get("components") or {},
        "intent_score": round(intent, 2),
        "data_value_score": data_value,
        "completeness_score": round(completeness, 3),
        "data_dimension_scores": dim_scores,
        "data_value_weights": dict(_DATA_VALUE_WEIGHTS),
        "tier": pri.tier,
    }

    return {
        "pillars": {
            PILLAR_MISSING: {
                "gaps": gaps,
                "suggested_passes": list(gap_report.passes),
                "priority": gap_report.priority,
            },
            PILLAR_OPTIMIZE: {
                "fields_improved": optimized,
                "pass_outcomes": dict(pass_outcomes or {}),
            },
            PILLAR_QUALITY: quality,
            PILLAR_ADDITIONAL: additional,
            PILLAR_RANK: rank,
        },
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "company_id": int(company.id),
        "company_name": company.name or "",
    }


def stamp_secondary_assessment(company: Company, assessment: Dict[str, Any]) -> None:
    """Persist assessment snapshot on crm_metadata."""
    meta = dict(company.crm_metadata or {})
    meta["secondary_assessment"] = assessment
    company.crm_metadata = meta


def read_sales_opportunity_rank(company: Company) -> Optional[float]:
    """Return persisted sales_opportunity_rank, if secondary pass has run."""
    meta = company.crm_metadata if isinstance(company.crm_metadata, dict) else {}
    assessment = meta.get("secondary_assessment")
    if not isinstance(assessment, dict):
        return None
    rank = (assessment.get("pillars") or {}).get(PILLAR_RANK) or {}
    val = rank.get("sales_opportunity_rank")
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def read_completeness_score(company: Company) -> float:
    meta = company.crm_metadata if isinstance(company.crm_metadata, dict) else {}
    assessment = meta.get("secondary_assessment")
    if not isinstance(assessment, dict):
        return 0.0
    rank = (assessment.get("pillars") or {}).get(PILLAR_RANK) or {}
    try:
        return float(rank.get("completeness_score") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def blend_pipeline_rank_score(company: Company, *, tier_score: float) -> float:
    """
    Prefer secondary-assessed leads on /pipeline when enrichment exists.
    Unassessed leads keep tier_score (no penalty before secondary pass runs).
    """
    sor = read_sales_opportunity_rank(company)
    if sor is None:
        return float(tier_score)
    completeness = read_completeness_score(company)
    return round(
        0.55 * sor + 0.35 * float(tier_score) + 0.10 * completeness * 100.0,
        4,
    )


def run_value_assessment_pass(
    company: Company,
    signals: Sequence[Signal],
    contacts: Sequence[Contact],
    *,
    pass_outcomes: Optional[Dict[str, str]] = None,
    fields_filled: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Final secondary step — always runs; returns assessment + rank."""
    gap_report = audit_company_gaps(
        company,
        signals,
        contacts,
        overall_score=float(
            (pick_primary_score(company.scores).overall_intent_score or 0)
            if pick_primary_score(company.scores)
            else 0
        ),
    )
    assessment = build_secondary_assessment(
        company,
        signals,
        contacts,
        gaps_report=gap_report,
        pass_outcomes=pass_outcomes,
        fields_filled=fields_filled,
    )
    stamp_secondary_assessment(company, assessment)
    rank = assessment["pillars"][PILLAR_RANK]["sales_opportunity_rank"]
    return assessment, rank
