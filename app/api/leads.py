"""
Leads API
=========
GET /api/leads
  Query params:
    min_score     float  default 0   — minimum overall_intent_score
    max_score     float  default 100 — (for cold-lead views)
    tier          str    HOT|WARM|COLD|ALL  default ALL
    industry      str    partial match, e.g. "hospitality"
    signal_type   str    filter to leads that have this signal type
    exclude_junk  bool   default true  — remove garbage-named leads
    limit         int    default 200
    sort          str    score|name|signals  default score
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app.database import get_db
from app.models.score import Score
from app.models.company import Company
from app.models.signal import Signal
from app.services.lead_filter import classify_lead, is_junk, priority_tier
from app.services.signal_ranker import compute_weighted_score
from app.services.industry_inference import infer_industry_from_text

router = APIRouter()

_HOT_SIGNAL_TYPES = [
    "funding_round",
    "strategic_hire",
    "capex",
    "ma_activity",
    "labor_pain",
    "automation_intent",
    "quality_bottleneck",
    "safety_incident",
    "production_capacity",
    "warehouse_throughput",
    "packaging_automation",
    "repetitive_process",
]

_WARM_SIGNAL_TYPES = [
    "expansion",
    "job_posting",
    "labor_shortage",
    "news",
    "service_consistency",
    "equipment_integration",
    "material_handling",
]


def _lead_rows_query(db: Session):
    """Lightweight aggregate query used by both list and summary endpoints."""
    hot_hits = func.sum(
        case((Signal.signal_type.in_(_HOT_SIGNAL_TYPES), 1), else_=0)
    ).label("hot_hits")
    warm_hits = func.sum(
        case((Signal.signal_type.in_(_WARM_SIGNAL_TYPES), 1), else_=0)
    ).label("warm_hits")

    return (
        db.query(
            Company.id.label("id"),
            Company.name.label("name"),
            Company.website.label("website"),
            Company.industry.label("industry"),
            Company.employee_estimate.label("employee_estimate"),
            Company.location_city.label("location_city"),
            Company.location_state.label("location_state"),
            Company.source.label("source"),
            func.coalesce(Score.overall_intent_score, 0).label("overall_score"),
            func.count(Signal.id).label("signal_count"),
            hot_hits,
            warm_hits,
        )
        .outerjoin(Score, Score.company_id == Company.id)
        .outerjoin(Signal, Signal.company_id == Company.id)
        .group_by(
            Company.id,
            Company.name,
            Company.website,
            Company.industry,
            Company.employee_estimate,
            Company.location_city,
            Company.location_state,
            Company.source,
            Score.overall_intent_score,
        )
    )


def _row_is_junk(name: Optional[str]) -> tuple[bool, str]:
    junk, reason = is_junk(name)
    if junk:
        return junk, reason
    if (name or "").strip().lower() == "target":
        return True, "target false positive (common-word in funding headlines)"
    return False, ""


def _row_priority(row) -> object:
    signal_count = int(row.signal_count or 0)
    hot_hits = int(row.hot_hits or 0)
    warm_hits = int(row.warm_hits or 0)
    pseudo_signal_types = (["funding_round"] * hot_hits) + (["news"] * warm_hits)
    return priority_tier(
        float(row.overall_score or 0),
        row.industry,
        pseudo_signal_types,
        signal_count,
        row.employee_estimate,
    )


def _fmt_company(c: Company, junk: bool, junk_reason: str, pri) -> dict:
    s = c.scores
    sigs = c.signals or []
    # Public-facing: never expose "Unknown" — use "Other"
    industry_display = (c.industry or "").strip()
    if not industry_display or industry_display.lower() == "unknown":
        industry_display = "Other"

    return {
        "id":             c.id,
        "company_name":   c.name,
        "website":        c.website,
        "industry":       industry_display,
        "location_city":  c.location_city,
        "location_state": c.location_state,
        "employee_estimate": c.employee_estimate,
        "source":         c.source,
        # priority classification
        "priority_tier":    pri.tier,
        "priority_score":   round(pri.score, 1),
        "priority_reasons": pri.reasons,
        "is_junk":          junk,
        "junk_reason":      junk_reason,
        # scores — DB already stores 0-100
        "score": {
            "overall_score":    round((s.overall_intent_score  if s else 0), 1),
            "automation_score": round((s.automation_score      if s else 0), 1),
            "labor_pain_score": round((s.labor_pain_score      if s else 0), 1),
            "expansion_score":  round((s.expansion_score       if s else 0), 1),
            "market_fit_score": round((s.robotics_fit_score    if s else 0), 1),
        },
        "signal_count": len(sigs),
        "created_at":   c.created_at.isoformat() if c.created_at else None,
        "updated_at":   c.updated_at.isoformat() if c.updated_at else None,
        "signals": [
            {
                "signal_type":     sig.signal_type,
                "strength":        sig.signal_strength,
                "weighted_score":  compute_weighted_score(sig),
                "raw_text":        sig.signal_text,
                "source_url":      sig.source_url,
            }
            for sig in sorted(sigs, key=lambda x: x.signal_strength, reverse=True)
        ],
    }


@router.get("")
@router.get("/")
@router.get("/leads")
def get_leads(
    min_score: float      = Query(0.0,   description="Min overall score 0-100"),
    max_score: float      = Query(100.0, description="Max overall score 0-100"),
    tier: Optional[str]   = Query(None,  description="HOT | WARM | COLD"),
    industry: Optional[str] = Query(None, description="Partial industry match"),
    signal_type: Optional[str] = Query(None, description="Must have this signal type"),
    exclude_junk: bool    = Query(True,  description="Hide junk-named leads"),
    limit: int            = Query(200,   description="Max results"),
    sort: str             = Query("score", description="score | name | signals"),
    db: Session           = Depends(get_db),
):
    candidates = _lead_rows_query(db)

    if min_score is not None:
        candidates = candidates.filter(func.coalesce(Score.overall_intent_score, 0) >= min_score)
    if max_score is not None:
        candidates = candidates.filter(func.coalesce(Score.overall_intent_score, 0) <= max_score)
    if industry:
        candidates = candidates.filter(Company.industry.ilike(f"%{industry}%"))
    if signal_type:
        candidates = candidates.having(
            func.sum(case((Signal.signal_type == signal_type, 1), else_=0)) > 0
        )

    # Keep the candidate set small and sorted by score for quick classification.
    candidate_limit = min(max(limit * 10, 120), 800)
    if sort == "name":
        candidates = candidates.order_by(Company.name.asc())
    elif sort == "signals":
        candidates = candidates.order_by(func.count(Signal.id).desc())
    else:
        candidates = candidates.order_by(func.coalesce(Score.overall_intent_score, 0).desc())

    rows = candidates.limit(candidate_limit).all()

    results = []
    junk_count = 0
    for row in rows:
        junk, junk_reason = _row_is_junk(row.name)
        if junk:
            junk_count += 1
            if exclude_junk:
                continue

        pri = _row_priority(row)
        if tier and tier.upper() != "ALL" and pri.tier != tier.upper():
            continue

        results.append(
            {
                "id": row.id,
                "company_name": row.name,
                "priority_tier": pri.tier,
                "priority_score": round(pri.score, 1),
                "priority_reasons": pri.reasons,
                "is_junk": junk,
                "junk_reason": junk_reason,
                "signal_count": int(row.signal_count or 0),
            }
        )

    if sort == "name":
        results.sort(key=lambda x: (x["company_name"] or "").lower())
    elif sort == "signals":
        results.sort(key=lambda x: x["signal_count"], reverse=True)
    else:
        results.sort(key=lambda x: x["priority_score"], reverse=True)

    results = results[:limit]

    if not results:
        return []

    ids = [r["id"] for r in results]
    companies = (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .filter(Company.id.in_(ids))
        .all()
    )
    company_map = {c.id: c for c in companies}

    final = []
    for r in results:
        c = company_map.get(r["id"])
        if not c:
            continue
        # Re-classify only the final visible rows so the response stays exact.
        junk, junk_reason, pri = classify_lead(c, c.scores, c.signals)
        if junk and exclude_junk:
            continue
        final.append(_fmt_company(c, junk, junk_reason, pri))

    return final   # plain list — dashboard iterates it directly


@router.get("/summary")
def leads_summary(
    exclude_junk: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Pipeline counts for the dashboard stat cards and front-page ticker. Includes leads per industry."""
    rows = (
        db.query(
            Company.name.label("name"),
            Company.industry.label("industry"),
            Company.employee_estimate.label("employee_estimate"),
            func.coalesce(Score.overall_intent_score, 0).label("overall_score"),
        )
        .outerjoin(Score, Score.company_id == Company.id)
        .all()
    )
    total = hot = warm = cold = junk_count = 0
    by_industry = {}
    for row in rows:
        j, _ = _row_is_junk(row.name)
        if j:
            junk_count += 1
            if exclude_junk:
                continue
        pri = _row_priority(row)
        total += 1
        if pri.tier == "HOT":  hot  += 1
        elif pri.tier == "WARM": warm += 1
        else: cold += 1
        # Public-facing: never show "Unknown" — use "Other" so the site doesn't look broken
        raw = (row.industry or "").strip()
        industry_key = raw if raw and raw.lower() != "unknown" else "Other"
        by_industry[industry_key] = by_industry.get(industry_key, 0) + 1

    total_signals = db.query(func.count(Signal.id)).scalar() or 0

    return {
        "total": total, "hot": hot, "warm": warm, "cold": cold,
        "junk_filtered": junk_count,
        "total_signals": total_signals,
        "by_industry": by_industry,
    }


@router.post("/reclassify-unknown")
def reclassify_unknown_industries(db: Session = Depends(get_db)):
    """
    Reclassify leads with industry Unknown: infer industry from company name + signal text, update DB.
    Returns counts of updated and unchanged.
    """
    companies = (
        db.query(Company)
        .options(joinedload(Company.signals))
        .filter(
            (Company.industry == None) | (Company.industry == "") | (func.lower(Company.industry) == "unknown")
        )
        .all()
    )
    updated = 0
    by_industry = {}
    for c in companies:
        text_parts = [c.name or ""]
        for sig in (c.signals or []):
            if getattr(sig, "signal_text", None):
                text_parts.append(sig.signal_text)
        text = " ".join(text_parts)
        inferred = infer_industry_from_text(text)
        if inferred != "Unknown":
            c.industry = inferred
            updated += 1
            by_industry[inferred] = by_industry.get(inferred, 0) + 1
    if updated:
        db.commit()
    unchanged = len(companies) - updated
    return {
        "reclassified": updated,
        "unchanged": unchanged,
        "total_unknown": len(companies),
        "by_industry": by_industry,
    }


@router.get("/signals/{company_id}")
def get_signals(company_id: int, db: Session = Depends(get_db)):
    signals = db.query(Signal).filter(Signal.company_id == company_id).all()
    return [
        {
            "id": s.id,
            "signal_type": s.signal_type,
            "strength": s.signal_strength,
            "raw_text": s.signal_text,
            "source_url": s.source_url,
        }
        for s in signals
    ]


@router.post("/recalculate/{company_id}")
def recalculate(company_id: int):
    return {"status": "queued", "company_id": company_id}