"""
Scraper Health API
==================
Exposes watchdog status, circuit breaker controls, and run history.

Endpoints:
  GET  /scraper-health              — full health report
  GET  /scraper-health/circuits     — only open circuit breakers
  POST /scraper-health/reset/{url}  — manually reset a circuit breaker
  POST /scraper-health/reset-all    — reset all circuit breakers
  GET  /pipeline-stats              — live DB stats for the pipeline health page
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from urllib.parse import unquote

from app.database import get_db
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.scrapers.scraper_watchdog import get_watchdog

router = APIRouter()


@router.get("/scraper-health")
def scraper_health():
    """Full watchdog health report — run history, circuit breakers, active runs."""
    watchdog = get_watchdog()
    watchdog.reload_from_disk()
    data = watchdog.status()
    # Summarise for quick dashboard widget
    total_urls    = len(data["url_health"])
    open_circuits = len(data["circuit_open_urls"])
    recent        = data["recent_runs"][-1] if data["recent_runs"] else None
    data["summary"] = {
        "total_urls_tracked":   total_urls,
        "open_circuits":        open_circuits,
        "healthy_urls":         total_urls - open_circuits,
        "last_run_status":      recent["status"] if recent else "no runs yet",
        "last_run_scraper":     recent["scraper_name"] if recent else None,
        "last_run_finished_at": recent["finished_at"] if recent else None,
    }
    return data


@router.get("/scraper-health/circuits")
def open_circuits():
    """List URLs currently blocked by open circuit breakers."""
    watchdog = get_watchdog()
    watchdog.reload_from_disk()
    status = watchdog.status()
    return {
        "open_circuits": status["circuit_open_urls"],
        "count": len(status["circuit_open_urls"]),
    }


@router.post("/scraper-health/reset/{url:path}")
def reset_circuit(url: str):
    """
    Manually reset the circuit breaker for a specific URL.
    URL must be URL-encoded in the path, e.g.:
      POST /scraper-health/reset/https%3A%2F%2Fexample.com
    """
    decoded_url = unquote(url)
    watchdog = get_watchdog()
    watchdog.reload_from_disk()
    found = watchdog.reset_circuit(decoded_url)
    if found:
        return {"status": "reset", "url": decoded_url}
    return JSONResponse(status_code=404,
                        content={"error": f"URL not found in watchdog: {decoded_url}"})


@router.post("/scraper-health/reset-all")
def reset_all_circuits():
    """Reset ALL open circuit breakers. Use after fixing a broken scraper."""
    watchdog = get_watchdog()
    watchdog.reload_from_disk()
    watchdog.reset_all_circuits()
    return {"status": "all circuits reset"}


@router.get("/pipeline-stats")
def pipeline_stats(db: Session = Depends(get_db)):
    """
    Live pipeline stats pulled directly from the database.
    Used by the Pipeline Health page — never stale, survives redeploys.
    """
    now = datetime.now(timezone.utc)
    day_ago  = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)

    total_companies = db.query(func.count(Company.id)).scalar() or 0
    total_signals   = db.query(func.count(Signal.id)).scalar() or 0
    scored_leads    = db.query(func.count(Score.id)).scalar() or 0

    # Recent additions — use created_at if available, else fall back to id ordering
    try:
        new_24h = db.query(func.count(Company.id)).filter(
            Company.created_at >= day_ago
        ).scalar() or 0
        new_7d = db.query(func.count(Company.id)).filter(
            Company.created_at >= week_ago
        ).scalar() or 0
    except Exception:
        new_24h = new_7d = None

    # Most recent signal timestamp
    try:
        latest_signal_ts = db.query(func.max(Signal.created_at)).scalar()
        latest_signal_ts = latest_signal_ts.isoformat() if latest_signal_ts else None
    except Exception:
        latest_signal_ts = None

    # Signal type breakdown
    try:
        sig_rows = (
            db.query(Signal.signal_type, func.count(Signal.id).label("n"))
            .group_by(Signal.signal_type)
            .order_by(func.count(Signal.id).desc())
            .all()
        )
        signal_breakdown = {r.signal_type: r.n for r in sig_rows}
    except Exception:
        signal_breakdown = {}

    # Industry breakdown (top 10)
    try:
        ind_rows = (
            db.query(Company.industry, func.count(Company.id).label("n"))
            .filter(Company.industry.isnot(None))
            .group_by(Company.industry)
            .order_by(func.count(Company.id).desc())
            .limit(10)
            .all()
        )
        industry_breakdown = {r.industry: r.n for r in ind_rows}
    except Exception:
        industry_breakdown = {}

    # HOT / WARM / COLD counts via score table
    try:
        from app.services.lead_filter import PRIORITY_HOT_COMPOSITE_MIN, PRIORITY_WARM_COMPOSITE_MIN
        hot_count  = db.query(func.count(Score.id)).filter(Score.overall_intent_score >= PRIORITY_HOT_COMPOSITE_MIN).scalar() or 0
        warm_count = db.query(func.count(Score.id)).filter(
            Score.overall_intent_score >= PRIORITY_WARM_COMPOSITE_MIN,
            Score.overall_intent_score < PRIORITY_HOT_COMPOSITE_MIN
        ).scalar() or 0
        cold_count = total_companies - hot_count - warm_count
    except Exception:
        hot_count = warm_count = cold_count = None

    # Scraper watchdog (best-effort — may be empty after redeploy)
    try:
        watchdog = get_watchdog()
        watchdog.reload_from_disk()
        wd = watchdog.status()
        recent_run = wd["recent_runs"][-1] if wd["recent_runs"] else None
    except Exception:
        wd = {}
        recent_run = None

    return {
        "database": {
            "total_companies":  total_companies,
            "total_signals":    total_signals,
            "scored_leads":     scored_leads,
            "new_last_24h":     new_24h,
            "new_last_7d":      new_7d,
            "latest_signal_at": latest_signal_ts,
            "hot":  hot_count,
            "warm": warm_count,
            "cold": cold_count,
        },
        "signal_breakdown":   signal_breakdown,
        "industry_breakdown": industry_breakdown,
        "scraper_watchdog": {
            "urls_tracked":    len(wd.get("url_health", {})),
            "open_circuits":   len(wd.get("circuit_open_urls", [])),
            "recent_run":      recent_run,
            "note": "Watchdog log resets on each redeploy. DB stats above are always live.",
        },
    }
