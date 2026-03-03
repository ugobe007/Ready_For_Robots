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
import time
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import Optional
from app.database import get_db
from app.models.score import Score
from app.models.company import Company
from app.models.signal import Signal
from app.services.lead_filter import classify_lead, is_junk, clean_signals, qualify_hot_lead, strip_html, clean_source_url
from app.services.signal_ranker import compute_weighted_score

router = APIRouter()

# ── In-process TTL cache ──────────────────────────────────────────────────────
# Classifying 2000 companies is expensive; cache the full formatted list
# and re-use it across both get_leads and leads_summary.
_CACHE: dict = {}           # "full" -> (timestamp_float, list[dict])
_CACHE_TTL = 120            # seconds — scrapers run every 4 h, 2 min is safe

def _invalidate_cache():
    _CACHE.clear()

def _full_leads_cached(db: Session) -> list:
    """Load + classify + format ALL companies, returning cached result if fresh."""
    entry = _CACHE.get("full")
    if entry and time.time() - entry[0] < _CACHE_TTL:
        return entry[1]
    companies = (
        db.query(Company)
        .options(joinedload(Company.scores), selectinload(Company.signals))
        .limit(2000)
        .all()
    )
    formatted = [_fmt_company(c, *classify_lead(c, c.scores, c.signals))
                 for c in companies]
    _CACHE["full"] = (time.time(), formatted)
    return formatted


def _fmt_company(c: Company, junk: bool, junk_reason: str, pri) -> dict:
    s = c.scores
    sigs = clean_signals(c.signals or [])   # strip listicle / junk headlines
    sorted_sigs = sorted(sigs, key=lambda x: x.signal_strength, reverse=True)

    # HOT lead qualification — buying window, intent confidence, action
    hot_qual = None
    if pri.tier == "HOT":
        q = qualify_hot_lead(sigs)
        hot_qual = {
            "buying_window":       q.buying_window,
            "intent_confidence":   q.intent_confidence,
            "recommended_action":  q.recommended_action,
            "window_evidence":     q.window_evidence,
            "confidence_drivers":  q.confidence_drivers,
            "freshest_signal_days": q.freshest_signal_days,
        }

    # Keep ALL signal types for server-side filtering; send only top-5 to reduce payload.
    # Full signals are available via GET /api/leads/signals/{id} (loaded on card expand).
    _SIGNAL_PREVIEW = 5
    return {
        "id":             c.id,
        "company_name":   c.name,
        "website":        c.website,
        "industry":       c.industry,
        "location_city":  c.location_city,
        "location_state": c.location_state,
        "employee_estimate": c.employee_estimate,
        "source":         c.source,
        "priority_tier":    pri.tier,
        "priority_score":   round(pri.score, 1),
        "priority_reasons": pri.reasons,
        "is_junk":          junk,
        "junk_reason":      junk_reason,
        "hot_qualification": hot_qual,
        "score": {
            "overall_score":    round((s.overall_intent_score  if s else 0), 1),
            "automation_score": round((s.automation_score      if s else 0), 1),
            "labor_pain_score": round((s.labor_pain_score      if s else 0), 1),
            "expansion_score":  round((s.expansion_score       if s else 0), 1),
            "market_fit_score": round((s.robotics_fit_score    if s else 0), 1),
        },
        "signal_count": len(sigs),
        # All signal types (used for server-side signal_type filter) — lightweight
        "_signal_types": list({sig.signal_type for sig in sigs}),
        # Top-5 signals only — keeps the list-view payload small (~10× reduction)
        "signals": [
            {
                "signal_type":    sig.signal_type,
                "strength":       sig.signal_strength,
                "weighted_score": compute_weighted_score(sig),
                "raw_text":       strip_html(sig.signal_text),
                "source_url":     sig.source.url if sig.source else clean_source_url(sig.source_url, sig.signal_text),
            }
            for sig in sorted_sigs[:_SIGNAL_PREVIEW]
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
    # Serve from TTL cache — avoids re-classifying 2000 companies every request.
    # Cache is populated once and reused for _CACHE_TTL seconds (default 120 s).
    all_leads = _full_leads_cached(db)

    results = []
    for r in all_leads:
        if r["is_junk"] and exclude_junk:
            continue

        # score range filter
        raw = r["score"]["overall_score"]
        if raw < min_score or raw > max_score:
            continue

        # tier filter
        if tier and tier.upper() != "ALL" and r["priority_tier"] != tier.upper():
            continue

        # industry filter
        if industry and (not r["industry"] or industry.lower() not in (r["industry"] or "").lower()):
            continue

        # signal type filter — use _signal_types which covers ALL signals, not just preview top-5
        if signal_type and signal_type not in r.get("_signal_types", []):
            continue

        results.append(r)

    # sort
    if sort == "name":
        results.sort(key=lambda x: (x["company_name"] or "").lower())
    elif sort == "signals":
        results.sort(key=lambda x: x["signal_count"], reverse=True)
    else:
        results.sort(key=lambda x: x["priority_score"], reverse=True)

    return results[:limit]   # plain list — dashboard iterates it directly


# Buying-window sort order: NOW is most urgent
_WINDOW_ORDER = {"NOW": 0, "NEAR": 1, "PIPELINE": 2, "UNCLEAR": 3}
_CONF_ORDER   = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


@router.get("/hot")
def get_hot_leads(
    industry: Optional[str] = Query(None, description="Partial industry filter"),
    window:   Optional[str] = Query(None, description="NOW | NEAR | PIPELINE | UNCLEAR"),
    confidence: Optional[str] = Query(None, description="HIGH | MEDIUM | LOW"),
    limit: int = Query(100),
    db: Session = Depends(get_db),
):
    """
    HOT leads only, sorted by buying urgency:
      1. Buying window  (NOW → NEAR → PIPELINE → UNCLEAR)
      2. Intent confidence  (HIGH → MEDIUM → LOW)
      3. Priority score  (desc)

    Each result includes a `hot_qualification` block with:
      - buying_window, intent_confidence, recommended_action
      - window_evidence (quoted signal phrases)
      - confidence_drivers (signal types)
      - freshest_signal_days
    """
    companies = (
        db.query(Company)
        .options(joinedload(Company.scores), selectinload(Company.signals))
        .all()
    )

    results = []
    for c in companies:
        junk, junk_reason, pri = classify_lead(c, c.scores, c.signals)
        if junk or pri.tier != "HOT":
            continue
        if industry and (not c.industry or industry.lower() not in c.industry.lower()):
            continue

        fmt = _fmt_company(c, junk, junk_reason, pri)
        hq  = fmt.get("hot_qualification") or {}
        w   = hq.get("buying_window", "UNCLEAR")
        cf  = hq.get("intent_confidence", "LOW")

        if window and w != window.upper():
            continue
        if confidence and cf != confidence.upper():
            continue

        fmt["_sort_key"] = (_WINDOW_ORDER.get(w, 9), _CONF_ORDER.get(cf, 9), -pri.score)
        results.append(fmt)

    results.sort(key=lambda x: x.pop("_sort_key"))
    results = results[:limit]

    # Summary counts by window
    by_window = {}
    for r in results:
        w = (r.get("hot_qualification") or {}).get("buying_window", "UNCLEAR")
        by_window[w] = by_window.get(w, 0) + 1

    return {
        "total_hot": len(results),
        "by_window": by_window,
        "leads": results,
    }


@router.get("/summary")
def leads_summary(
    exclude_junk: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Pipeline counts for the dashboard stat cards — served from TTL cache."""
    all_leads = _full_leads_cached(db)
    total = hot = warm = cold = junk_count = 0
    for r in all_leads:
        if r["is_junk"]:
            junk_count += 1
            if exclude_junk:
                continue
        total += 1
        if r["priority_tier"] == "HOT":    hot  += 1
        elif r["priority_tier"] == "WARM": warm += 1
        else:                              cold += 1

    return {
        "total": total, "hot": hot, "warm": warm, "cold": cold,
        "junk_filtered": junk_count,
    }


@router.get("/signals/{company_id}")
def get_signals(company_id: int, db: Session = Depends(get_db)):
    signals = db.query(Signal).filter(Signal.company_id == company_id).all()
    return [
        {
            "id": s.id,
            "signal_type": s.signal_type,
            "strength": s.signal_strength,
            "raw_text": strip_html(s.signal_text),
            "source_url": s.source.url if s.source else clean_source_url(s.source_url, s.signal_text),
        }
        for s in signals
    ]


@router.post("/recalculate/{company_id}")
def recalculate(company_id: int):
    return {"status": "queued", "company_id": company_id}