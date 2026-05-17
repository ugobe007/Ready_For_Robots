import time
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, and_, or_, desc, text, case
from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.services.daily_analytics_service import get_daily_analytics, format_report_markdown
from app.services.industry_brief_service import build_industry_brief_payload
from typing import Optional
from datetime import datetime, timedelta, timezone

router = APIRouter()

# In-process TTL cache for analytics (2 min TTL — DB query is expensive)
_ANALYTICS_CACHE: dict[str, tuple[float, dict]] = {}
_ANALYTICS_TTL = 120.0

# Track calculator usage
calculator_usage = []
robot_searches = []
site_visits = []


@router.post("/track/visit")
async def track_visit(data: dict):
    """Track site visits (page views)"""
    site_visits.append({
        **data,
        "timestamp": datetime.now().isoformat(),
    })
    return {"status": "tracked"}


@router.post("/track/roi-calculation")
async def track_roi_calculation(data: dict):
    """Track ROI calculator usage"""
    calculator_usage.append({
        **data,
        'timestamp': datetime.now().isoformat()
    })
    return {"status": "tracked"}

@router.post("/track/robot-search")
async def track_robot_search(data: dict):
    """Track robot search usage"""
    robot_searches.append({
        **data,
        'timestamp': datetime.now().isoformat()
    })
    return {"status": "tracked"}

@router.get("/analytics")
async def get_analytics(range: str = Query('7d', pattern='^(7d|30d|90d|all)$')):
    """
    Get platform analytics — sourced from live database (signals, companies, scores).
    In-memory tracking (calculator_usage, robot_searches, site_visits) supplements with
    user-interaction events for the current server process; database rows are the primary
    persistent data source.
    Cached in-process for 2 minutes to avoid repeated full-table scans on every admin load.
    """
    cached = _ANALYTICS_CACHE.get(range)
    if cached is not None:
        ts, data = cached
        if time.monotonic() - ts < _ANALYTICS_TTL:
            return data

    now = datetime.now(timezone.utc)
    if range == '7d':
        cutoff = now - timedelta(days=7)
        prev_cutoff = now - timedelta(days=14)
    elif range == '30d':
        cutoff = now - timedelta(days=30)
        prev_cutoff = now - timedelta(days=60)
    elif range == '90d':
        cutoff = now - timedelta(days=90)
        prev_cutoff = now - timedelta(days=180)
    else:
        cutoff = datetime(2000, 1, 1, tzinfo=timezone.utc)
        prev_cutoff = datetime(2000, 1, 1, tzinfo=timezone.utc)

    db = SessionLocal()
    try:
        # ── Query 1: All company stats in a single pass ────────────────────────
        # Replaces 4 separate COUNT queries on the companies table.
        co_row = db.query(
            func.count(Company.id).label("total"),
            func.sum(case((Company.created_at >= cutoff, 1), else_=0)).label("new_count"),
            func.sum(case(
                (and_(Company.created_at >= prev_cutoff, Company.created_at < cutoff), 1),
                else_=0,
            )).label("prev_count"),
        ).one()
        total_companies = int(co_row.total or 0)
        new_companies   = int(co_row.new_count or 0)
        prev_companies  = int(co_row.prev_count or 0)
        company_growth  = (
            round(((new_companies - prev_companies) / prev_companies) * 100) if prev_companies
            else (100 if new_companies else 0)
        )

        # ── Query 2: All signal stats + type breakdown in a single pass ────────
        # Replaces 5 separate queries on the signals table.
        # Conditional aggregation counts total / new / prev in one scan.
        sig_scalar = db.query(
            func.count(Signal.id).label("total"),
            func.sum(case((Signal.created_at >= cutoff, 1), else_=0)).label("new_count"),
            func.sum(case(
                (and_(Signal.created_at >= prev_cutoff, Signal.created_at < cutoff), 1),
                else_=0,
            )).label("prev_count"),
        ).one()
        total_signals = int(sig_scalar.total or 0)
        new_signals   = int(sig_scalar.new_count or 0)
        prev_signals  = int(sig_scalar.prev_count or 0)
        signal_growth = (
            round(((new_signals - prev_signals) / prev_signals) * 100) if prev_signals
            else (100 if new_signals else 0)
        )

        # Signal type breakdown — one GROUP BY covers both "all-time" and "recent" cuts.
        sig_type_rows = (
            db.query(
                Signal.signal_type,
                func.count(Signal.id).label("cnt"),
                func.sum(case((Signal.created_at >= cutoff, 1), else_=0)).label("recent_cnt"),
            )
            .group_by(Signal.signal_type)
            .order_by(func.count(Signal.id).desc())
            .limit(8)
            .all()
        )
        signal_type_breakdown = []
        recent_hot_type = None
        if sig_type_rows:
            max_cnt = sig_type_rows[0].cnt or 1
            # Pick the signal type with the most recent hits for the "hottest trend" insight.
            recent_sorted = sorted(sig_type_rows, key=lambda r: int(r.recent_cnt or 0), reverse=True)
            if recent_sorted and recent_sorted[0].recent_cnt:
                recent_hot_type = (recent_sorted[0].signal_type or "unknown").replace("_", " ").title()
            for row in sig_type_rows:
                signal_type_breakdown.append({
                    "type": (row.signal_type or "unknown").replace("_", " ").title(),
                    "count": row.cnt,
                    "percentage": round((row.cnt / max_cnt) * 100),
                })

        # ── Query 3: All score stats in a single pass ──────────────────────────
        # Replaces 4 separate COUNT queries on the scores table.
        sc_row = db.query(
            func.count(Score.id).label("total"),
            func.sum(case((Score.overall_intent_score >= 70, 1), else_=0)).label("hot"),
            func.sum(case(
                (and_(Score.overall_intent_score >= 40, Score.overall_intent_score < 70), 1),
                else_=0,
            )).label("warm"),
            func.sum(case((Score.overall_intent_score < 40, 1), else_=0)).label("cold"),
        ).one()
        total_scored = int(sc_row.total or 0)
        hot_count    = int(sc_row.hot  or 0)
        warm_count   = int(sc_row.warm or 0)
        cold_count   = int(sc_row.cold or 0)

        score_dist = [
            {"range": "HOT (70–100)", "count": hot_count,  "color": "red"},
            {"range": "WARM (40–69)", "count": warm_count, "color": "amber"},
            {"range": "COLD (0–39)",  "count": cold_count, "color": "cyan"},
        ]

        # ── Query 4: Industry breakdown (companies table, single GROUP BY) ──────
        industry_rows = (
            db.query(Company.industry, func.count(Company.id).label("cnt"))
            .filter(
                Company.industry.isnot(None),
                Company.industry != "",
                Company.industry != "Unknown",
            )
            .group_by(Company.industry)
            .order_by(func.count(Company.id).desc())
            .limit(10)
            .all()
        )
        top_industries = []
        if industry_rows:
            max_cnt = industry_rows[0].cnt or 1
            for row in industry_rows:
                top_industries.append({
                    "name": row.industry,
                    "count": row.cnt,
                    "percentage": round((row.cnt / max_cnt) * 100),
                })

        # ── Query 5: Top HOT leads (indexed join on score column) ──────────────
        top_hot = (
            db.query(Company.name, Company.industry, Score.overall_intent_score)
            .join(Score, Company.id == Score.company_id)
            .filter(Score.overall_intent_score >= 70)
            .order_by(Score.overall_intent_score.desc())
            .limit(5)
            .all()
        )
        top_hot_leads = [
            {"name": r.name, "industry": r.industry or "Unknown", "score": round(float(r.overall_intent_score or 0), 1)}
            for r in top_hot
        ]

        # ── In-memory tracking (non-persistent; supplemental) ─────────────────
        # Convert cutoff to naive for in-memory list comparison (stored as isoformat without tz)
        cutoff_naive = cutoff.replace(tzinfo=None)
        prev_cutoff_naive = prev_cutoff.replace(tzinfo=None)
        filtered_calcs = [c for c in calculator_usage
                          if datetime.fromisoformat(c["timestamp"]) >= cutoff_naive]
        filtered_searches = [s for s in robot_searches
                              if datetime.fromisoformat(s["timestamp"]) >= cutoff_naive]
        filtered_visits = [v for v in site_visits
                           if datetime.fromisoformat(v["timestamp"]) >= cutoff_naive]
        prev_calcs = [c for c in calculator_usage
                      if prev_cutoff_naive <= datetime.fromisoformat(c["timestamp"]) < cutoff_naive]

        total_calculations = len(filtered_calcs)
        calculation_growth = 0
        if prev_calcs:
            calculation_growth = round(((total_calculations - len(prev_calcs)) / len(prev_calcs)) * 100)
        elif total_calculations > 0:
            calculation_growth = 100

        avg_payback_months = 0
        avg_robot_cost = 0
        if filtered_calcs:
            paybacks = [c.get("payback_months", 0) for c in filtered_calcs if c.get("payback_months")]
            costs = [c.get("robot_cost", 0) for c in filtered_calcs if c.get("robot_cost")]
            avg_payback_months = round(sum(paybacks) / len(paybacks), 1) if paybacks else 0
            avg_robot_cost = round(sum(costs) / len(costs)) if costs else 0

        email_captures = len([c for c in filtered_calcs if c.get("email")])
        conversion_rate = round((email_captures / total_calculations) * 100) if total_calculations else 0

        # ── Insights ──────────────────────────────────────────────────────────
        insights = {
            "hottest_trend": f"{recent_hot_type} is the top signal type in the last {range}" if recent_hot_type else "Collecting signal data…",
            "opportunity": f"{top_industries[0]['name']} has {top_industries[0]['count']} tracked companies" if top_industries else "Industry data loading",
            "growth_area": f"{new_companies:,} new companies added in the last {range} (+{company_growth}%)" if company_growth >= 0 else f"{new_companies:,} new companies in the last {range}",
            "action_item": f"{hot_count} HOT leads ready for outreach — {warm_count} WARM in pipeline",
        }

    finally:
        db.close()

    result = {
        # DB-backed pipeline metrics
        "total_companies": total_companies,
        "total_signals": total_signals,
        "total_scored": total_scored,
        "new_signals": new_signals,
        "signal_growth": signal_growth,
        "new_companies": new_companies,
        "company_growth": company_growth,
        "hot_count": hot_count,
        "warm_count": warm_count,
        "cold_count": cold_count,
        "top_industries": top_industries,
        "signal_type_breakdown": signal_type_breakdown,
        "score_distribution": score_dist,
        "top_hot_leads": top_hot_leads,
        # In-session user interaction metrics (non-persistent)
        "total_calculations": total_calculations,
        "calculation_growth": calculation_growth,
        "robot_searches": len(filtered_searches),
        "site_visits": len(filtered_visits),
        "avg_payback_months": avg_payback_months,
        "avg_robot_cost": avg_robot_cost,
        "email_captures": email_captures,
        "conversion_rate": conversion_rate,
        "insights": insights,
    }
    _ANALYTICS_CACHE[range] = (time.monotonic(), result)
    return result


@router.get("/daily-report")
async def get_daily_opportunity_report(
    days: int = Query(1, ge=1, le=90, description="Number of days to analyze"),
    format: str = Query("json", pattern="^(json|markdown)$"),
):
    """
    Daily analytics report from opportunity postings.
    
    Answers:
    - What type of automation is required or inferred?
    - What type of robots are needed and what specs?
    - Is there expected ROI or schedule for running trials?
    - What are the most common tasks to automate?
    - Industry, geography, top companies, signal breakdown.
    """
    db = SessionLocal()
    try:
        analytics = get_daily_analytics(db, days=days)
        analytics["industry_brief"] = build_industry_brief_payload(
            db,
            days=days,
            analytics=analytics,
            use_cache=True,
            force_refresh=False,
        )
        if format == "markdown":
            return PlainTextResponse(
                format_report_markdown(analytics),
                media_type="text/markdown",
            )
        return analytics
    finally:
        db.close()
