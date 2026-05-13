"""
Leads API
=========
GET /api/leads
  POST /api/leads/{company_id}/feedback — rep feedback (optional Bearer)
  Query params:
    min_score     float  default 0   — minimum overall_intent_score
    max_score     float  default 100 — (for cold-lead views)
    tier          str    HOT|WARM|COLD|ALL  default ALL
    industry      str    partial match, e.g. "hospitality"
    signal_type   str    filter to leads that have this signal type
    exclude_junk  bool   default true  — remove garbage-named leads
    limit         int    default 50 (max 50; pool rotates every 5 minutes)
    sort          str    score|name|signals  default score
"""
import logging
import os
import random
import re
import threading
import time
from datetime import datetime, timezone, date

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List, Literal

from app.database import get_db
from app.api.auth_deps import optional_user
from app.models.score import Score
from app.models.company import Company
from app.models.signal import Signal
from app.models.lead_rep_feedback import LeadRepFeedback
from app.models.lead_research import LeadResearchUpdate
from app.models.waitlist import WaitlistSignup
from app.services.resend_email import ResendEmailError, send_email_via_resend
from app.services.lead_filter import (
    classify_lead,
    is_junk,
    pick_primary_score,
    priority_tier,
    SIGNAL_TYPES_HOT,
    SIGNAL_TYPES_WARM,
)
from app.services.signal_ranker import compute_weighted_score, compute_lead_aggregate_signal_score
from app.services.industry_inference import effective_industry_for_lead, infer_industry_from_text
from app.services.scoring_public import get_scoring_system_public
from app.services.automation_profile import get_automation_profile_for_response
from app.services.lead_value import compute_lead_value
from app.services.gtm_readiness import compute_gtm_readiness
from app.services.lead_primary_link import enrich_lead_link_fields
from app.services.lead_signal_display import format_signal_for_sales, strip_extraction_artifacts
from app.services.company_url_openai import resolve_homepage_urls_for_companies
from app.services.company_domain import (
    dedupe_companies_ordered,
    dedupe_staged_lead_tuples,
    normalize_website_domain,
    pick_canonical_company,
)

router = APIRouter()


class ReportDownloadIn(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    name: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=240)
    robot_category: Optional[str] = Field(None, alias="robotCategory", max_length=160)


def _valid_capture_email(email: str) -> bool:
    return "@" in email and "." in email.rsplit("@", 1)[-1]


def _send_report_email(email: str) -> dict:
    try:
        result = send_email_via_resend(
            to_email=email,
            subject="Your 2026 Automation Imperative Report",
            from_display_name="ReadyForRobots",
            body_text=(
                "Thanks for requesting The Automation Imperative report.\n\n"
                "The report is based on ReadyForRobots signal data from 158 enterprises "
                "and 437 detected buying signals.\n\n"
                "Read the report online here:\n"
                "https://readyforrobots.com/intelligence\n\n"
                "You can also activate SCOUT against live sales leads here:\n"
                "https://readyforrobots.com/results?url=\n"
            ),
        )
        return {"sent": True, **result}
    except ResendEmailError as exc:
        return {"sent": False, "reason": str(exc)}


def _notify_report_owner(row: WaitlistSignup) -> dict:
    owner_email = (
        os.getenv("REPORT_DOWNLOAD_NOTIFY_EMAIL")
        or os.getenv("OWNER_EMAIL")
        or (os.getenv("ADMIN_EMAILS", "").split(",")[0].strip() if os.getenv("ADMIN_EMAILS") else "")
    ).strip()
    if not owner_email:
        return {"sent": False, "reason": "No owner notification email configured"}
    try:
        result = send_email_via_resend(
            to_email=owner_email,
            subject="New Automation Imperative report lead",
            from_display_name="ReadyForRobots",
            body_text=(
                f"New report download lead:\n\n"
                f"Name: {row.name or '-'}\n"
                f"Email: {row.email}\n"
                f"Company: {row.company or '-'}\n"
                f"Robot category: {row.use_case or '-'}\n"
                f"Source: {row.source or '-'}\n"
            ),
        )
        return {"sent": True, **result}
    except ResendEmailError as exc:
        return {"sent": False, "reason": str(exc)}


@router.post("/report-download")
def capture_report_download(body: ReportDownloadIn, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    if not _valid_capture_email(email):
        raise HTTPException(status_code=400, detail="Valid email is required")

    row = db.query(WaitlistSignup).filter(WaitlistSignup.email == email).first()
    if row is None:
        row = WaitlistSignup(email=email)
        db.add(row)
    row.name = body.name or row.name or None
    row.company = body.company or row.company or None
    row.use_case = body.robot_category or row.use_case or None
    row.source = "report_download"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        row = db.query(WaitlistSignup).filter(WaitlistSignup.email == email).first()
        if row is None:
            raise HTTPException(status_code=409, detail="Report download conflict, please retry")
        row.name = body.name or row.name or None
        row.company = body.company or row.company or None
        row.use_case = body.robot_category or row.use_case or None
        row.source = "report_download"
        db.commit()
    db.refresh(row)
    return {
        "ok": True,
        "lead": {
            "id": row.id,
            "email": row.email,
            "name": row.name,
            "company": row.company,
            "robotCategory": row.use_case,
            "source": row.source,
        },
        "email": _send_report_email(row.email),
        "ownerNotification": _notify_report_owner(row),
    }


def _entity_resolution_payload(db: Session, c: Company) -> Optional[dict]:
    """
    When multiple company rows share the same registrable domain, expose IDs and
    the canonical row (highest intent + signal evidence) for clients that merge in UI.
    """
    dom = getattr(c, "website_domain", None) or normalize_website_domain(c.website)
    if not dom:
        return None
    peers = (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .filter(Company.website_domain == dom)
        .all()
    )
    if len(peers) <= 1:
        return None
    canonical = pick_canonical_company(peers)
    if not canonical:
        return None
    return {
        "website_domain": dom,
        "company_ids_sharing_domain": sorted(p.id for p in peers),
        "canonical_company_id": canonical.id,
        "requested_is_canonical": c.id == canonical.id,
    }


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


# Cap how many grouped company rows we load for summaries / homepage (not full-table scans).
# Default 50 — override with PIPELINE_SUMMARY_ROW_CAP only for internal ops.
_PIPELINE_SUMMARY_ROW_CAP = int(os.getenv("PIPELINE_SUMMARY_ROW_CAP", "100000"))

# Public list endpoint: never return more than this; pool rotates on a 5-minute clock.
LEADS_PUBLIC_MAX = 50
LEADS_SQL_POOL_CAP = 200
LEADS_ROTATION_SEC = 300


def _lead_rows_query_limited(db: Session, limit: int):
    """
    Same rollups as _lead_rows_query, but only the top `limit` rows by intent score.
    Tier counts match the full pipeline for the scored head; very low-score cold leads
    beyond this cap are omitted from summary totals (acceptable for UI cards).
    """
    lim = max(1, min(int(limit), 100_000))
    sq = _lead_rows_query(db).subquery()
    return db.query(sq).order_by(sq.c.overall_score.desc()).limit(lim)


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
            total += 1
            cold += 1
            total_signals += int(row.signal_count or 0)
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


def _shuffle_spotlight_order(leads: List[Company], h_seed: int, w_seed: int) -> List[Company]:
    """Deterministic shuffle — same five picks can feel fresh when card order changes."""
    if len(leads) <= 1:
        return leads
    out = leads[:]
    rnd = random.Random((h_seed ^ w_seed) & 0xFFFFFFFF or 1)
    rnd.shuffle(out)
    return out


def _spotlight_rotation_seeds(now: datetime) -> tuple[int, int, int]:
    """
    Deterministic seeds for HOT vs WARM circular picks on the homepage spotlight.
    Changes every LEADS_ROTATION_SEC (5 minutes) so the spotlight batch rotates, not every minute.
    """
    day_o = int(now.date().toordinal())
    slot = int(now.timestamp() // LEADS_ROTATION_SEC)
    h_seed = day_o * 7919 + slot * 9176 + 203
    w_seed = day_o * 9283 + slot * 5843 + 411
    return h_seed, w_seed, slot


def _signal_label(signal_type: str) -> str:
    return SIGNAL_TYPE_LABELS.get(signal_type, signal_type.replace("_", " ").title())


def _dedup_top_signals(sigs: list, n: int = LEAD_RESPONSE_MAX_SIGNALS) -> list:
    """
    Return at most `n` signals, strongest first, without repeating the same
    signal type or the same underlying article text.
    """
    seen_types: set = set()
    seen_texts: set = set()
    deduped = []
    for s in sorted(sigs, key=lambda x: float(getattr(x, "signal_strength", None) or 0), reverse=True):
        t = getattr(s, "signal_type", None) or "unknown"
        text_key = re.sub(r"\s+", " ", (getattr(s, "signal_text", None) or "").strip().lower())
        if t in seen_types or (text_key and text_key in seen_texts):
            continue
        seen_types.add(t)
        if text_key:
            seen_texts.add(text_key)
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
    "casino": ("commercial cleaning robots, delivery robots, and housekeeping automation", "housekeeping labor pressure and guest-service consistency"),
    "gaming": ("commercial cleaning robots, delivery robots, and housekeeping automation", "high-traffic facilities and service consistency"),
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
        raw = strip_extraction_artifacts(getattr(top, "signal_text", None))
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


def _fmt_company(
    c: Company,
    junk: bool,
    junk_reason: str,
    pri,
    llm_homepage_url: Optional[str] = None,
    include_research: bool = False,
    db: Optional[Session] = None,
) -> dict:
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

    overall_100 = float(s.overall_intent_score) if s else 0.0
    lv = compute_lead_value(
        overall_100,
        c.employee_estimate,
        automation_profile,
        sigs,
    )
    signal_score = compute_lead_aggregate_signal_score(sigs)

    gtm = compute_gtm_readiness(sigs, pri.tier, pri.reasons)

    link_extras = enrich_lead_link_fields(
        website=c.website,
        signals=sigs,
        overall_score=overall_100,
        signal_count=signal_count_total,
        llm_resolved_url=llm_homepage_url,
    )

    payload = {
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
        # scores — DB stores 0–100; lead_value_score ranks deal quality (intent + scale + spec + freshness)
        "score": {
            "overall_score":    round((s.overall_intent_score  if s else 0), 1),
            "automation_score": round((s.automation_score      if s else 0), 1),
            "labor_pain_score": round((s.labor_pain_score      if s else 0), 1),
            "expansion_score":  round((s.expansion_score       if s else 0), 1),
            "market_fit_score": round((s.robotics_fit_score    if s else 0), 1),
            "lead_value_score": lv["lead_value_score"],
            "lead_value_components": lv["components"],
            "lead_value_weights": lv["weights"],
            "procurement_hints": lv.get("procurement_hints") or [],
            "signal_score": signal_score,
        },
        "procurement_hints": lv.get("procurement_hints") or [],
        "signal_count": signal_count_total,
        "created_at":   c.created_at.isoformat() if c.created_at else None,
        "updated_at":   c.updated_at.isoformat() if c.updated_at else None,
        "signals": [
            {
                "signal_type":     sig.signal_type,
                "signal_label":    _signal_label(sig.signal_type),
                "strength":        sig.signal_strength,
                "weighted_score":  compute_weighted_score(sig),
                "display_text":     format_signal_for_sales(sig.signal_text),
                "raw_text":        strip_extraction_artifacts(sig.signal_text),
                "source_url":      sig.source_url,
            }
            for sig in sigs_for_response
        ],
        "share_blurb": share_blurb,
        "share_summary": share_summary,
        "automation_profile": automation_profile,
        "gtm": gtm,
        **link_extras,
    }
    if include_research and db is not None:
        research_updates = _lead_research_payload(db, c.id)
        payload["research_updates"] = research_updates
        payload["last_researched_at"] = _last_researched_at(c, research_updates)
        payload["latest_material_update"] = research_updates[0] if research_updates else None
    return payload


def _research_update_row(row: LeadResearchUpdate) -> dict:
    return {
        "id": row.id,
        "company_id": row.company_id,
        "update_type": row.update_type,
        "title": row.title,
        "summary": row.summary,
        "source_url": row.source_url,
        "source_domain": row.source_domain,
        "detected_at": row.detected_at.isoformat() if row.detected_at else None,
        "significance_score": round(float(row.significance_score or 0), 3),
        "status": row.status,
    }


def _lead_research_payload(db: Session, company_id: int, limit: int = 6) -> list[dict]:
    rows = (
        db.query(LeadResearchUpdate)
        .filter(LeadResearchUpdate.company_id == company_id)
        .order_by(LeadResearchUpdate.significance_score.desc(), LeadResearchUpdate.detected_at.desc())
        .limit(max(1, min(limit, 25)))
        .all()
    )
    return [_research_update_row(row) for row in rows]


def _last_researched_at(c: Company, research_updates: list[dict]) -> Optional[str]:
    meta = c.crm_metadata or {}
    research_meta = meta.get("research_agent") if isinstance(meta, dict) else None
    if isinstance(research_meta, dict) and research_meta.get("last_researched_at"):
        return research_meta["last_researched_at"]
    dates = [item.get("detected_at") for item in research_updates if item.get("detected_at")]
    return max(dates) if dates else None


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
    limit: int            = Query(
        50,
        ge=1,
        description="Requested page size; server clamps to LEADS_PUBLIC_MAX (50) — older clients may send 150+",
    ),
    sort: str             = Query("score", description="score | name | signals"),
    rotation_slot: Optional[int] = Query(
        None,
        description="Optional 5-minute slot index for testing; default uses server clock",
    ),
    db: Session           = Depends(get_db),
):
    # Clamp so cached JS / bookmarked ?limit=150 does not 422 while policy stays ≤50 rows.
    limit = min(max(limit, 1), LEADS_PUBLIC_MAX)
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

    # Keep the SQL candidate set bounded — never scan the full grouped table.
    candidate_limit = min(LEADS_SQL_POOL_CAP, max(limit * 4, 50))
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

    # Extra headroom so domain/name dedupe can still yield `limit` distinct entities after rotation.
    pre_limit = min(250, max(limit * 5, 80))
    results = results[:pre_limit]

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

    staged = []
    for r in results:
        c = company_map.get(r["id"])
        if not c:
            continue
        junk, junk_reason, pri = classify_lead(c, c.scores, c.signals)
        if junk and exclude_junk:
            continue
        staged.append((c, junk, junk_reason, pri))

    staged = dedupe_staged_lead_tuples(staged)
    slot = rotation_slot if rotation_slot is not None else int(time.time() // LEADS_ROTATION_SEC)
    if len(staged) > limit:
        span = len(staged) - limit
        start = (slot * 1103515245) % (span + 1)
        staged = staged[start : start + limit]
    else:
        staged = staged[:limit]

    llm_hints = resolve_homepage_urls_for_companies([t[0] for t in staged])
    return [
        _fmt_company(c, junk, junk_reason, pri, llm_homepage_url=llm_hints.get(c.id))
        for c, junk, junk_reason, pri in staged
    ]


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
    llm_hints = resolve_homepage_urls_for_companies([c])
    payload = _fmt_company(
        c,
        junk,
        junk_reason,
        pri,
        llm_homepage_url=llm_hints.get(c.id),
        include_research=True,
        db=db,
    )
    er = _entity_resolution_payload(db, c)
    if er:
        payload["entity_resolution"] = er
    return payload


@router.get("/{company_id}/research")
def get_lead_research(company_id: int, limit: int = Query(10, ge=1, le=25), db: Session = Depends(get_db)):
    exists = db.query(Company.id).filter(Company.id == company_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"company_id": company_id, "research_updates": _lead_research_payload(db, company_id, limit=limit)}


class RepFeedbackIn(BaseModel):
    vote: Literal["up", "down"]
    reason_code: Optional[Literal["wrong_company", "not_ready", "spam", "other"]] = None
    note: Optional[str] = Field(None, max_length=2000)


@router.post("/{company_id}/feedback")
def post_lead_rep_feedback(
    company_id: int,
    body: RepFeedbackIn,
    db: Session = Depends(get_db),
    user: Optional[dict] = Depends(optional_user),
):
    """
    Rep feedback loop: thumbs up/down plus optional reason (wrong company, not ready, spam).
    Anonymous submissions allowed; Bearer token attaches user_id when present.
    """
    c = db.query(Company).filter(Company.id == company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Company not found")
    uid = None
    if user and user.get("uid"):
        uid = str(user["uid"])
    row = LeadRepFeedback(
        company_id=company_id,
        vote=body.vote,
        reason_code=body.reason_code,
        note=body.note,
        user_id=uid,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"ok": True, "id": row.id}


# ── Homepage TTL cache ────────────────────────────────────────────────────────
# Aggregate query is expensive. We keep a short logical TTL but **serve stale
# payloads immediately** when it expires and refresh in a background thread, so
# clients do not block on a slow rebuild. Cold miss (empty cache) still runs
# synchronously. Each Fly machine has its own RAM cache; stale serving avoids
# thundering herds when TTLs expire.
_HOMEPAGE_CACHE_TTL = 300  # 5 minutes — aligned with LEADS_ROTATION_SEC
_homepage_cache: dict = {}
_homepage_build_lock = threading.Lock()
_homepage_bg_refresh_lock = threading.Lock()
_homepage_bg_refresh_in_progress = False


def _set_homepage_cache(data: dict) -> None:
    _homepage_cache["v1"] = {"ts": time.monotonic(), "data": data}


def _compute_pipeline_summary(db: Session, exclude_junk: bool) -> dict:
    """Tier counts from a capped, score-ordered slice — not a full-table scan."""
    rows = _lead_rows_query_limited(db, _PIPELINE_SUMMARY_ROW_CAP).all()
    total, hot, warm, cold, junk_count, by_industry, total_signals = _aggregate_lead_rows(
        rows, exclude_junk=exclude_junk
    )
    companies_in_database = db.query(func.count(Company.id)).scalar() or 0
    signals_in_database = db.query(func.count(Signal.id)).scalar() or 0
    return {
        "total": total,
        "hot": hot,
        "warm": warm,
        "cold": cold,
        "junk_filtered": junk_count,
        "total_signals": total_signals,
        "by_industry": by_industry,
        "companies_in_database": int(companies_in_database),
        "signals_in_database": int(signals_in_database),
        "summary_tier_slice_size": len(rows),
        "leads_list_max_per_request": LEADS_PUBLIC_MAX,
    }


def _build_homepage_payload(db: Session) -> dict:
    """Homepage: capped SQL slice (50 scored rows) + spotlight (≤50 leads), 5-minute rotation."""
    rows = _lead_rows_query_limited(db, _PIPELINE_SUMMARY_ROW_CAP).all()
    total, hot, warm, cold, junk_count, by_industry, total_signals = _aggregate_lead_rows(
        rows, exclude_junk=True
    )
    summary = {
        "total": total,
        "hot": hot,
        "warm": warm,
        "cold": cold,
        "junk_filtered": junk_count,
        "total_signals": total_signals,
        "by_industry": by_industry,
    }
    # Rows are already ordered by score DESC; walk in order — no Python sort of 10k+ rows.
    ordered_ids: List[int] = []
    seen: set = set()
    for row in rows:
        if _row_is_junk(row.name)[0]:
            continue
        if row.id in seen:
            continue
        if int(row.signal_count or 0) < 1:
            continue
        seen.add(row.id)
        ordered_ids.append(row.id)
        if len(ordered_ids) >= 50:
            break

    if not ordered_ids:
        now = datetime.now(timezone.utc)
        slot = int(now.timestamp() // LEADS_ROTATION_SEC)
        return {
            "summary": summary,
            "hotLeads": [],
            "tierLegend": HOMEPAGE_TIER_LEGEND,
            "spotlightMix": {
                "hot_slots": 35,
                "warm_slots": 15,
                "feed_limit": 50,
                "rotation_period_sec": LEADS_ROTATION_SEC,
                "rotation_slot": slot,
                "rotation_day": str(now.date()),
                "rotation_hour_utc": now.hour,
                "rotation_minute_utc": now.minute,
            },
            "scoringSystem": get_scoring_system_public(),
        }

    companies = (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .filter(Company.id.in_(ordered_ids[:50]))
        .all()
    )
    id_rank = {cid: i for i, cid in enumerate(ordered_ids)}
    companies.sort(key=lambda c: id_rank.get(c.id, 9999))

    cl_cache: dict = {}

    def _classify(c: Company):
        cid = c.id
        if cid not in cl_cache:
            cl_cache[cid] = classify_lead(c, c.scores, c.signals)
        return cl_cache[cid]

    hot_pool: List[tuple[float, float, Company]] = []
    warm_pool: List[tuple[float, float, Company]] = []
    for c in companies:
        junk, _, pri = _classify(c)
        if junk or not c.signals:
            continue
        ts = _latest_signal_ts(c)
        if pri.tier == "HOT":
            hot_pool.append((ts, pri.score, c))
        elif pri.tier == "WARM":
            warm_pool.append((ts, pri.score, c))

    hot_pool.sort(key=lambda x: (-x[0], -x[1]))
    warm_pool.sort(key=lambda x: (-x[0], -x[1]))
    hot_ordered = dedupe_companies_ordered([t[2] for t in hot_pool])
    warm_ordered = dedupe_companies_ordered([t[2] for t in warm_pool])

    feed_limit = 50
    hot_slots = 35
    warm_slots = 15
    now = datetime.now(timezone.utc)
    h_seed, w_seed, rot_slot = _spotlight_rotation_seeds(now)
    hour = now.hour

    chosen: List[Company] = []
    used_ids: set = set()

    for c in _take_rotated(hot_ordered, hot_slots, h_seed):
        if c.id not in used_ids:
            chosen.append(c)
            used_ids.add(c.id)
    warm_avail = [c for c in warm_ordered if c.id not in used_ids]
    for c in _take_rotated(warm_avail, warm_slots, w_seed):
        if c.id not in used_ids:
            chosen.append(c)
            used_ids.add(c.id)
    for c in hot_ordered + warm_ordered:
        if len(chosen) >= feed_limit:
            break
        if c.id not in used_ids:
            chosen.append(c)
            used_ids.add(c.id)

    def _pool_sort_key(c: Company):
        junk, _, pri = _classify(c)
        tier_rank = 0 if pri.tier == "HOT" else 1
        return (tier_rank, -_latest_signal_ts(c))

    chosen = sorted(chosen[:feed_limit], key=_pool_sort_key)

    llm_hints = resolve_homepage_urls_for_companies(chosen)
    hot_leads = []
    for c in chosen:
        junk, junk_reason, pri = _classify(c)
        hot_leads.append(
            _fmt_company(c, junk, junk_reason, pri, llm_homepage_url=llm_hints.get(c.id))
        )

    return {
        "summary": summary,
        "hotLeads": hot_leads,
        "tierLegend": HOMEPAGE_TIER_LEGEND,
        "spotlightMix": {
            "hot_slots": hot_slots,
            "warm_slots": warm_slots,
            "feed_limit": feed_limit,
            "rotation_period_sec": LEADS_ROTATION_SEC,
            "rotation_slot": rot_slot,
            "rotation_day": str(now.date()),
            "rotation_hour_utc": hour,
            "rotation_minute_utc": now.minute,
        },
        "scoringSystem": get_scoring_system_public(),
    }


def _schedule_homepage_background_refresh() -> None:
    """Single-flight async rebuild; callers already returned stale JSON."""
    global _homepage_bg_refresh_in_progress
    with _homepage_bg_refresh_lock:
        if _homepage_bg_refresh_in_progress:
            return
        _homepage_bg_refresh_in_progress = True

    def _run():
        global _homepage_bg_refresh_in_progress
        try:
            from app.database import SessionLocal

            db = SessionLocal()
            try:
                payload = _build_homepage_payload(db)
                with _homepage_build_lock:
                    _set_homepage_cache(payload)
                    _set_summary_cache(True, payload["summary"])
            finally:
                db.close()
        except Exception as exc:
            logger.warning("Homepage background refresh failed: %s", exc)
        finally:
            with _homepage_bg_refresh_lock:
                _homepage_bg_refresh_in_progress = False

    threading.Thread(target=_run, daemon=True, name="homepage-cache-refresh").start()


def warm_homepage_cache() -> None:
    """
    Pre-populate the homepage cache in a background thread at startup so the
    first real user request is not blocked on the cold aggregate query.
    """

    def _warm():
        try:
            from app.database import SessionLocal

            db = SessionLocal()
            try:
                payload = _build_homepage_payload(db)
                with _homepage_build_lock:
                    if _homepage_cache.get("v1"):
                        return
                    _set_homepage_cache(payload)
                    _set_summary_cache(True, payload["summary"])
                    logger.info(
                        "Homepage cache warmed at startup: %d total, %d hot",
                        payload["summary"].get("total", 0),
                        payload["summary"].get("hot", 0),
                    )
            finally:
                db.close()
        except Exception as exc:
            logger.warning("Homepage cache warm-up failed (non-fatal): %s", exc)

    threading.Thread(target=_warm, daemon=True, name="homepage-cache-warmer").start()


@router.get("/homepage")
def leads_homepage(response: Response, db: Session = Depends(get_db)):
    """
    Batched endpoint for homepage: summary + spotlight leads in one response.

    Spotlight uses classify_lead on full signals (aligned with list views).
    Selection: sort by newest signal time, then score; take 3 HOT + 2 WARM with a
    daily + hourly rotating window so the same top-score rows do not monopolize the list.
    Includes tierLegend for UI copy (COLD band documented as "Emerging").

    Performance: one aggregate query + Python sort; in-memory cache with stale-while-
    revalidate so expired TTL does not block clients on a slow rebuild.
    """
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"

    entry = _homepage_cache.get("v1")
    if entry is not None:
        age = time.monotonic() - entry["ts"]
        if age < _HOMEPAGE_CACHE_TTL:
            return entry["data"]
        _schedule_homepage_background_refresh()
        return entry["data"]

    # Cold miss: build **outside** the lock so other requests are not blocked for minutes on
    # slow Postgres (lock only protects cache dict writes).
    payload = _build_homepage_payload(db)
    with _homepage_build_lock:
        entry = _homepage_cache.get("v1")
        if entry is not None:
            return entry["data"]
        _set_homepage_cache(payload)
        _set_summary_cache(True, payload["summary"])
        return payload


@router.get("/scoring-system")
def leads_scoring_system():
    """
    Full Hot/Warm/Emerging + per-signal weights (for UI copy and tuning).
    Same payload embedded in GET /api/leads/homepage under `scoringSystem`.
    """
    return get_scoring_system_public()


_SUMMARY_CACHE_TTL = 600  # 10 minutes
_summary_cache: dict = {}
_summary_bg_lock = threading.Lock()
_summary_bg_in_progress: set = set()


def _set_summary_cache(exclude_junk: bool, data: dict) -> None:
    _summary_cache[f"v1_{exclude_junk}"] = {"ts": time.monotonic(), "data": data}


def _schedule_summary_background_refresh(exclude_junk: bool) -> None:
    """Refresh stale summary without blocking the HTTP response."""
    key = f"v1_{exclude_junk}"
    with _summary_bg_lock:
        if key in _summary_bg_in_progress:
            return
        _summary_bg_in_progress.add(key)

    def _run():
        try:
            from app.database import SessionLocal

            db = SessionLocal()
            try:
                data = _compute_pipeline_summary(db, exclude_junk)
                _set_summary_cache(exclude_junk, data)
            finally:
                db.close()
        except Exception as exc:
            logger.warning("Summary background refresh failed: %s", exc)
        finally:
            with _summary_bg_lock:
                _summary_bg_in_progress.discard(key)

    threading.Thread(
        target=_run,
        daemon=True,
        name=f"summary-cache-refresh-{exclude_junk}",
    ).start()


@router.get("/summary")
def leads_summary(
    response: Response,
    exclude_junk: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Pipeline counts for dashboard cards — capped query, stale-while-revalidate when TTL expires."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"

    cache_key = f"v1_{exclude_junk}"
    entry = _summary_cache.get(cache_key)
    if entry is not None:
        age = time.monotonic() - entry["ts"]
        if age < _SUMMARY_CACHE_TTL:
            return entry["data"]
        _schedule_summary_background_refresh(exclude_junk)
        return entry["data"]

    result = _compute_pipeline_summary(db, exclude_junk)
    _set_summary_cache(exclude_junk, result)
    return result


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