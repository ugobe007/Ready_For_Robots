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
from datetime import datetime, timezone, date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, case
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

from app.database import get_db
from app.models.score import Score
from app.models.company import Company
from app.models.signal import Signal
from app.services.lead_filter import (
    classify_lead,
    is_junk,
    pick_primary_score,
    priority_tier,
    SIGNAL_TYPES_HOT,
    SIGNAL_TYPES_WARM,
)
from app.services.signal_ranker import compute_weighted_score
from app.services.industry_inference import effective_industry_for_lead, infer_industry_from_text
from app.services.scoring_public import get_scoring_system_public
from app.services.automation_profile import get_automation_profile_for_response

router = APIRouter()

# Embedded `signals` in JSON are capped + deduplicated by signal_type.
# Top-scoring representative per unique type; then top N overall.
# `signal_count` still holds the true DB total.
LEAD_RESPONSE_MAX_SIGNALS = 5

# Human-friendly labels for every signal type surfaced on cards
SIGNAL_TYPE_LABELS: dict[str, str] = {
    "strategic_hire":      "Leadership Hire",
    "capex":               "CapEx Budget",
    "quality_bottleneck":  "Quality Problem",
    "safety_incident":     "Safety Incident",
    "labor_shortage":      "Labor Shortage",
    "production_capacity": "At Capacity",
    "warehouse_throughput":"Warehouse Bottleneck",
    "packaging_automation":"Packaging Automation",
    "repetitive_process":  "Repetitive Tasks",
    "expansion":           "Expansion",
    "material_handling":   "Material Handling",
    "funding_round":       "Funding Round",
    "ma_activity":         "M&A Activity",
    "job_posting":         "Job Posting",
    "news":                "News Signal",
    "automation_interest": "Automation Interest",
    "automation_intent":   "Automation Intent",
    "robot_installation":  "Robot Install",
    "pilot_success":       "Pilot Success",
    "scale_expansion":     "Scale Expansion",
    "vendor_selection":    "Vendor Selection",
    "roi_documented":      "ROI Documented",
    "economics_driven":    "Economics Trigger",
    "competitive_response":"Competitive Pressure",
    "problem_solution":    "Problem/Solution",
    "government_contract": "Gov Contract",
    "rfp_posted":          "RFP Posted",
    "labor_pain":          "Labor Pain",
    "labor_signal":        "Labor Signal",
    "service_consistency": "Service Consistency",
    "equipment_integration":"Equipment Integration",
}

# Tuple for SQLAlchemy .in_() — must match classify_lead / SIGNAL_TYPES_* in lead_filter
_SQL_HOT_TYPES = tuple(SIGNAL_TYPES_HOT)
_SQL_WARM_TYPES = tuple(SIGNAL_TYPES_WARM)


def _primary_score_subquery(db: Session):
    """
    One score row per company. Multiple DB rows in `scores` for the same company_id used to
    duplicate GROUP BY rows and inflate /api/leads/summary totals vs reality.

    Tie-break: max(last_calculated_at), then max(id) — aligned with pick_primary_score().
    """
    max_ts = (
        db.query(Score.company_id, func.max(Score.last_calculated_at).label("md"))
        .group_by(Score.company_id)
        .subquery()
    )
    # Among rows at max timestamp, take highest id (stable tie-break).
    return (
        db.query(Score.company_id, func.max(Score.id).label("score_id"))
        .join(
            max_ts,
            (Score.company_id == max_ts.c.company_id)
            & (
                (Score.last_calculated_at == max_ts.c.md)
                | (max_ts.c.md.is_(None) & Score.last_calculated_at.is_(None))
            ),
        )
        .group_by(Score.company_id)
        .subquery()
    )


def _lead_rows_query(db: Session):
    """Lightweight aggregate query used by both list and summary endpoints."""
    hot_hits = func.sum(
        case((Signal.signal_type.in_(_SQL_HOT_TYPES), 1), else_=0)
    ).label("hot_hits")
    warm_hits = func.sum(
        case((Signal.signal_type.in_(_SQL_WARM_TYPES), 1), else_=0)
    ).label("warm_hits")

    ps = _primary_score_subquery(db)

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
        .outerjoin(ps, ps.c.company_id == Company.id)
        .outerjoin(Score, Score.id == ps.c.score_id)
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
    hot_hits = int(getattr(row, "hot_hits", 0) or 0)
    warm_hits = int(getattr(row, "warm_hits", 0) or 0)
    pseudo_signal_types = (["funding_round"] * hot_hits) + (["news"] * warm_hits)
    return priority_tier(
        float(row.overall_score or 0),
        row.industry,
        pseudo_signal_types,
        signal_count,
        row.employee_estimate,
    )


def _aggregate_lead_rows(rows, exclude_junk: bool):
    """
    Count tiers + industry + signal rows for the same companies included in `total`.

    `total_signals` sums per-company signal counts for those rows only (not a global
    SELECT COUNT(signals), which includes junk companies and drifted from pipeline totals).
    """
    total = hot = warm = cold = junk_count = 0
    total_signals = 0
    by_industry: dict = {}
    for row in rows:
        j, _ = _row_is_junk(row.name)
        if j:
            junk_count += 1
            if exclude_junk:
                continue
        pri = _row_priority(row)
        total += 1
        total_signals += int(row.signal_count or 0)
        if pri.tier == "HOT":
            hot += 1
        elif pri.tier == "WARM":
            warm += 1
        else:
            cold += 1
        raw = (row.industry or "").strip()
        industry_key = raw if raw and raw.lower() not in ("unknown", "other") else "New"
        by_industry[industry_key] = by_industry.get(industry_key, 0) + 1
    return total, hot, warm, cold, junk_count, by_industry, total_signals


HOMEPAGE_TIER_LEGEND = {
    "HOT": {
        "label": "Hot",
        "tagline": "Act this week",
        "description": (
            "Strong buying-intent signals—funding, leadership moves, capex, M&A, robotics pilots "
            "or installs, vendor selection, RFPs—and high automation fit. Prioritize direct outreach."
        ),
    },
    "WARM": {
        "label": "Warm",
        "tagline": "Nurture & sequence",
        "description": (
            "Solid operational signals: expansion, hiring, labor pressure, automation interest, "
            "newsflow, integrations. Worth a research pass and a structured follow-up sequence."
        ),
    },
    "COLD": {
        "label": "Emerging",
        "tagline": "Explore & watchlist",
        "description": (
            "Earlier or lighter signals in our model—still real opportunities. Add to watchlists, "
            "monitor for new signals; tier moves up as intent sharpens."
        ),
    },
}


def _utc_aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _latest_signal_ts(company: Company) -> float:
    best: Optional[datetime] = None
    for s in company.signals or []:
        ca = _utc_aware(getattr(s, "created_at", None))
        if ca and (best is None or ca > best):
            best = ca
    return best.timestamp() if best else 0.0


def _take_rotated(companies: List[Company], count: int, seed: int) -> List[Company]:
    """Circular slice: daily `seed` rotates which high-ranked rows surface first."""
    n = len(companies)
    if n == 0 or count <= 0:
        return []
    start = seed % n
    return [companies[(start + i) % n] for i in range(min(count, n))]


def _signal_label(signal_type: str) -> str:
    return SIGNAL_TYPE_LABELS.get(signal_type, signal_type.replace("_", " ").title())


def _dedup_top_signals(sigs: list, n: int = LEAD_RESPONSE_MAX_SIGNALS) -> list:
    """
    Return at most `n` signals, one per unique signal_type, strongest first.
    Guarantees zero duplicates by type — a lead with 200 `news` rows shows ONE.
    """
    seen_types: set = set()
    deduped = []
    for s in sorted(sigs, key=lambda x: float(getattr(x, "signal_strength", None) or 0), reverse=True):
        t = getattr(s, "signal_type", None) or "unknown"
        if t not in seen_types:
            seen_types.add(t)
            deduped.append(s)
        if len(deduped) >= n:
            break
    return deduped


# Industry-to-automation-context map (mirrors newsletter_service logic)
_INDUSTRY_AUTOMATION_CTX: dict[str, tuple[str, str]] = {
    "logistics": ("autonomous mobile robots and warehouse automation", "labor-intensive picking and last-mile delivery"),
    "supply chain": ("AMRs and warehouse orchestration software", "throughput bottlenecks and labor shortages"),
    "warehouse": ("AMRs, AS/RS, and goods-to-person systems", "picking efficiency and labor replacement"),
    "fulfillment": ("goods-to-person robots and automated conveyors", "order fulfillment speed and accuracy"),
    "hospitality": ("room service robots and housekeeping automation", "labor vacancies and service consistency"),
    "hotel": ("delivery robots and back-of-house automation", "housekeeping labor shortages and service consistency"),
    "healthcare": ("hospital logistics robots and disinfection bots", "staff walking time and infection control"),
    "hospital": ("logistics robots and UV disinfection systems", "staff redeployment and patient safety"),
    "food service": ("kitchen automation and order fulfillment systems", "labor shortages and food consistency"),
    "restaurant": ("kitchen automation and front-of-house robots", "staff turnover and order accuracy"),
    "manufacturing": ("collaborative robots (cobots) and assembly automation", "labor costs and quality control"),
    "food & beverage": ("packaging automation and processing robots", "labor costs and production throughput"),
}


def _automation_ctx(industry: str) -> tuple[str, str]:
    low = (industry or "").lower()
    for key, val in _INDUSTRY_AUTOMATION_CTX.items():
        if key in low:
            return val
    return ("robotic automation", "operational efficiency and labor costs")


def _company_size_word(emp: Optional[int]) -> str:
    if not emp:
        return ""
    if emp >= 10000:
        return "large enterprise "
    if emp >= 5000:
        return "enterprise "
    if emp >= 1000:
        return "mid-market "
    if emp >= 200:
        return "growth-stage "
    return ""


def _build_share_blurb(
    c: Company,
    pri,
    sigs: list,
    *,
    industry_for_copy: Optional[str] = None,
) -> tuple:
    """
    Returns (share_blurb ~220c for Twitter/copy, share_summary 4-5 sentence intelligence paragraph).
    Format: '[Company] is targeting automation for their [use_case] due to [pain_point]
    which aligns with our signals [types]. The timing of the project is [X] months.'
    """
    import re as _re
    raw_ind = (industry_for_copy if industry_for_copy is not None else (c.industry or "")).strip()
    ind = raw_ind if raw_ind and raw_ind.lower() not in ("unknown", "other") else "New"
    name = c.name or "Company"
    tier = pri.tier
    score = pri.score
    automation_type, pain_point = _automation_ctx(raw_ind)

    if not sigs:
        summary = (
            f"{name} is targeting automation for their {automation_type} "
            f"due to {pain_point}. Signals detected on Ready For Robots suggest early buying intent."
        )
        return summary[:220], summary

    deduped = _dedup_top_signals(sigs, 5)
    size_word = _company_size_word(c.employee_estimate)

    unique_types = list(dict.fromkeys([getattr(s, "signal_type", "") for s in deduped]))[:4]
    labels = [_signal_label(t) for t in unique_types if t]
    signals_str = ", ".join(labels[:3]) if labels else "automation interest"
    sig_count = len(sigs)

    buy_months = "60–90" if tier == "HOT" else "90–120"

    loc = ""
    if c.location_city and c.location_state:
        loc = f" based in {c.location_city}, {c.location_state},"
    elif c.location_state:
        loc = f" based in {c.location_state},"

    # S1 — intelligence-led hook (user's template)
    s1 = (
        f"{name} is targeting automation for their {automation_type} "
        f"due to {pain_point}, which aligns with our signals: {signals_str}. "
        f"The timing of this project is within {buy_months} days."
    )

    # S2 — company context
    s2 = f"{name} is a {size_word}{ind} company{loc} with {sig_count} active buying indicators in our database."

    # S3 — strongest evidence (HTML-stripped)
    top = deduped[0] if deduped else None
    s3 = ""
    if top:
        raw = (getattr(top, "signal_text", None) or "").replace("\n", " ").strip()
        raw = _re.sub(r"<[^>]+>", "", raw).strip()
        top_label = _signal_label(getattr(top, "signal_type", ""))
        if raw and len(raw) > 20:
            excerpt = raw[:180] + ("…" if len(raw) > 180 else "")
            s3 = f'Key evidence — {top_label}: "{excerpt}"'
        else:
            s3 = f"The leading indicator is a {top_label}, consistent with companies actively evaluating {automation_type}."

    # S4 — qualifying reasons
    reasons = pri.reasons or []
    s4 = f"Qualifying factors: {'; '.join(reasons[:2])}." if reasons else ""

    parts = [s1, s2]
    if s3:
        parts.append(s3)
    if s4:
        parts.append(s4)
    summary = " ".join(p for p in parts if p)

    # Short blurb for Twitter character limit
    blurb = (
        f"{name} is targeting automation for their {automation_type} "
        f"due to {pain_point}. Signals: {signals_str}. "
        f"Project window: {buy_months} days."
    )
    return blurb[:220], summary[:700]


def _fmt_company(c: Company, junk: bool, junk_reason: str, pri) -> dict:
    s = pick_primary_score(c.scores)
    sigs = c.signals or []
    signal_count_total = len(sigs)
    sigs_for_response = _dedup_top_signals(sigs, LEAD_RESPONSE_MAX_SIGNALS)
    # Public-facing: never expose "Unknown" — use "New" (unclassified)
    industry_display = effective_industry_for_lead(c.name, c.industry, c.signals)
    if not industry_display or industry_display.lower() in ("unknown", "other"):
        industry_display = "New"

    share_blurb, share_summary = _build_share_blurb(
        c, pri, sigs, industry_for_copy=industry_display
    )

    raw_stored = (c.industry or "").strip()
    ov = industry_display if industry_display != raw_stored else None
    automation_profile = get_automation_profile_for_response(c, industry_override=ov)

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
        "signal_count": signal_count_total,
        "created_at":   c.created_at.isoformat() if c.created_at else None,
        "updated_at":   c.updated_at.isoformat() if c.updated_at else None,
        "signals": [
            {
                "signal_type":     sig.signal_type,
                "signal_label":    _signal_label(sig.signal_type),
                "strength":        sig.signal_strength,
                "weighted_score":  compute_weighted_score(sig),
                "raw_text":        sig.signal_text,
                "source_url":      sig.source_url,
            }
            for sig in sigs_for_response
        ],
        "share_blurb": share_blurb,
        "share_summary": share_summary,
        "automation_profile": automation_profile,
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


@router.get("/by-id/{company_id}")
def get_lead_by_id(company_id: int, db: Session = Depends(get_db)):
    """Single lead payload (same shape as list rows) — for modals / deep links when `automation_profile` is needed."""
    c = (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .filter(Company.id == company_id)
        .first()
    )
    if not c:
        raise HTTPException(status_code=404, detail="Lead not found")
    junk, junk_reason, pri = classify_lead(c, c.scores, c.signals)
    return _fmt_company(c, junk, junk_reason, pri)


@router.get("/homepage")
def leads_homepage(response: Response, db: Session = Depends(get_db)):
    """
    Batched endpoint for homepage: summary + spotlight leads in one response.

    Spotlight uses classify_lead on full signals (aligned with list views).
    Selection: sort by newest signal time, then score; take 3 HOT + 2 WARM with a
    daily + hourly rotating window so the same top-score rows do not monopolize the list.
    Includes tierLegend for UI copy (COLD band documented as "Emerging").
    """
    # Dynamic DB counts — do not cache (was max-age=90; browsers kept stale totals after deploys)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"

    # 1. Summary — must use _lead_rows_query so hot_hits/warm_hits match list + classify_lead tier logic
    rows = _lead_rows_query(db).all()
    total, hot, warm, cold, junk_count, by_industry, total_signals = _aggregate_lead_rows(
        rows, exclude_junk=True
    )
    summary = {
        "total": total, "hot": hot, "warm": warm, "cold": cold,
        "junk_filtered": junk_count,
        "total_signals": total_signals,
        "by_industry": by_industry,
    }

    # 2. Spotlight: same ordering as high-intent pipeline, tier from classify_lead
    candidate_rows = (
        _lead_rows_query(db)
        .order_by(func.coalesce(Score.overall_intent_score, 0).desc())
        .limit(280)
        .all()
    )
    ordered_ids = []
    seen = set()
    for row in candidate_rows:
        if _row_is_junk(row.name)[0]:
            continue
        if row.id in seen:
            continue
        if int(row.signal_count or 0) < 1:
            continue
        seen.add(row.id)
        ordered_ids.append(row.id)

    if not ordered_ids:
        return {"summary": summary, "hotLeads": []}

    companies = (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .filter(Company.id.in_(ordered_ids[:220]))
        .all()
    )
    id_rank = {cid: i for i, cid in enumerate(ordered_ids)}
    companies.sort(key=lambda c: id_rank.get(c.id, 9999))

    hot_pool: List[tuple[float, float, Company]] = []
    warm_pool: List[tuple[float, float, Company]] = []
    for c in companies:
        junk, _, pri = classify_lead(c, c.scores, c.signals)
        if junk or not c.signals:
            continue
        ts = _latest_signal_ts(c)
        if pri.tier == "HOT":
            hot_pool.append((ts, pri.score, c))
        elif pri.tier == "WARM":
            warm_pool.append((ts, pri.score, c))

    hot_pool.sort(key=lambda x: (-x[0], -x[1]))
    warm_pool.sort(key=lambda x: (-x[0], -x[1]))
    hot_ordered = [t[2] for t in hot_pool]
    warm_ordered = [t[2] for t in warm_pool]

    spotlight_limit = 5
    hot_slots = 3
    warm_slots = 2
    now = datetime.now(timezone.utc)
    day_o = now.date().toordinal()
    hour = now.hour
    # Hour term shifts the window a few times per day so repeat visits are not frozen
    h_seed = day_o * 7919 + 203 + hour * 17
    w_seed = day_o * 9283 + 411 + hour * 23

    chosen: List[Company] = []
    used_ids = set()

    for c in _take_rotated(hot_ordered, hot_slots, h_seed):
        if c.id not in used_ids:
            chosen.append(c)
            used_ids.add(c.id)
    warm_avail = [c for c in warm_ordered if c.id not in used_ids]
    for c in _take_rotated(warm_avail, warm_slots, w_seed):
        if c.id not in used_ids:
            chosen.append(c)
            used_ids.add(c.id)

    if len(chosen) < spotlight_limit:
        for c in hot_ordered:
            if c.id not in used_ids:
                chosen.append(c)
                used_ids.add(c.id)
            if len(chosen) >= spotlight_limit:
                break
    if len(chosen) < spotlight_limit:
        for c in warm_ordered:
            if c.id not in used_ids:
                chosen.append(c)
                used_ids.add(c.id)
            if len(chosen) >= spotlight_limit:
                break

    chosen = chosen[:spotlight_limit]

    hot_leads = []
    for c in chosen:
        junk, junk_reason, pri = classify_lead(c, c.scores, c.signals)
        hot_leads.append(_fmt_company(c, junk, junk_reason, pri))

    return {
        "summary": summary,
        "hotLeads": hot_leads,
        "tierLegend": HOMEPAGE_TIER_LEGEND,
        "spotlightMix": {
            "hot_slots": hot_slots,
            "warm_slots": warm_slots,
            "rotation_day": str(now.date()),
            "rotation_hour_utc": hour,
        },
        "scoringSystem": get_scoring_system_public(),
    }


@router.get("/scoring-system")
def leads_scoring_system():
    """
    Full Hot/Warm/Emerging + per-signal weights (for UI copy and tuning).
    Same payload embedded in GET /api/leads/homepage under `scoringSystem`.
    """
    return get_scoring_system_public()


@router.get("/summary")
def leads_summary(
    response: Response,
    exclude_junk: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Pipeline counts for the dashboard stat cards and front-page ticker. Includes leads per industry."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    # Same row shape as GET /api/leads — hot_hits/warm_hits rollups required for _row_priority tiers
    rows = _lead_rows_query(db).all()
    total, hot, warm, cold, junk_count, by_industry, total_signals = _aggregate_lead_rows(
        rows, exclude_junk=exclude_junk
    )

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
            (Company.industry == None)
            | (Company.industry == "")
            | (func.lower(Company.industry) == "unknown")
            | (func.lower(Company.industry) == "other")
            | (func.lower(Company.industry) == "new")
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