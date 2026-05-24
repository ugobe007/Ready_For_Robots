"""
Scraper control API - Manual trigger and monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, cast, Date
from app.database import get_db, SessionLocal
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.signal import Signal

router = APIRouter(prefix="/api/scraper", tags=["scraper-control"])


def _run_intelligence_scraper_sync(
    articles_per_query: int = 15,
    max_queries: Optional[int] = None,
    enrich: bool = True,
):
    """Run intelligence scraper in-process (no Celery/Redis needed). Writes to same DB as app."""
    import logging
    log = logging.getLogger(__name__)
    from app.scrapers.intelligence_news_scraper import IntelligenceNewsScraper
    db = SessionLocal()
    try:
        scraper = IntelligenceNewsScraper(db=db)
        stats = scraper.discover_leads(
            max_articles_per_query=articles_per_query,
            max_queries=max_queries,
        )
        if enrich:
            enrich_stats = scraper.enrich_existing_companies(limit=20)
            stats["companies_enriched"] = enrich_stats.get("companies_enriched", 0)
            stats["signals_created"] = stats.get("signals_created", 0) + enrich_stats.get("signals_created", 0)
        log.info(
            "Intelligence scraper completed: discovered=%s enriched=%s signals=%s",
            stats.get("companies_discovered", 0),
            stats.get("companies_enriched", 0),
            stats.get("signals_created", 0),
        )
        return stats
    except Exception as e:
        log.exception("Intelligence scraper failed: %s", e)
        raise
    finally:
        db.close()


@router.get("/cron/run-intelligence")
async def cron_run_intelligence(
    background_tasks: BackgroundTasks,
    token: str = Query("", description="Secret token (set SCRAPER_CRON_TOKEN)"),
) -> Dict[str, Any]:
    """
    Cron-trigger endpoint for external schedulers (cron-job.org, GitHub Actions).
    GET /api/scraper/cron/run-intelligence?token=YOUR_SECRET
    Set SCRAPER_CRON_TOKEN in Fly secrets. Runs quick scrape (20 queries, ~3 min).
    """
    import os
    expected = os.getenv("SCRAPER_CRON_TOKEN")
    if expected and token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")
    background_tasks.add_task(
        _run_intelligence_scraper_sync,
        articles_per_query=15,
        max_queries=20,
        enrich=True,
    )
    return {"status": "started", "message": "Quick scrape running (20 queries)"}


@router.post("/run-intelligence")
async def run_intelligence_scraper(
    background_tasks: BackgroundTasks,
    articles_per_query: int = 15,
) -> Dict[str, Any]:
    """
    Run the intelligence news scraper (discovers new leads from news).
    Runs in the background so the request returns immediately.
    No Redis/Celery required - writes directly to the app database.
    """
    def _task():
        _run_intelligence_scraper_sync(articles_per_query=articles_per_query)

    background_tasks.add_task(_task)
    return {
        "status": "intelligence_scraper_started",
        "message": "Intelligence scraper running in background (discovers new leads from 183 news queries). Check /api/leads/summary in 10–20 min.",
        "articles_per_query": articles_per_query,
        "check_leads": "/api/leads/summary",
    }


@router.post("/run-oem")
async def run_oem_discovery(
    background_tasks: BackgroundTasks,
    max_queries: int = 30,
) -> Dict[str, Any]:
    """Run XBOT/StageGate OEM prospect discovery in-process."""
    def _task():
        from app.database import SessionLocal
        from app.services.oem_discovery import run_oem_discovery
        db = SessionLocal()
        try:
            run_oem_discovery(db, max_queries=max_queries)
        finally:
            db.close()

    background_tasks.add_task(_task)
    return {
        "status": "oem_discovery_started",
        "message": "OEM/XBOT pipeline running (StageGate robot OEM prospects).",
        "max_queries": max_queries,
    }


@router.post("/sync-stagegate-crm")
async def sync_stagegate_crm_bridge(
    background_tasks: BackgroundTasks,
    refresh_draft: bool = False,
    min_score: int = 45,
) -> Dict[str, Any]:
    """Backfill StageGate robot_companies into Cal Admin (companies + Score + CrmAccount)."""

    def _task():
        from app.database import SessionLocal
        from app.services.stagegate_crm_bridge import sync_all_stagegate_prospects

        db = SessionLocal()
        try:
            return sync_all_stagegate_prospects(db, refresh_draft=refresh_draft, min_score=min_score)
        finally:
            db.close()

    background_tasks.add_task(_task)
    return {
        "status": "stagegate_crm_sync_started",
        "message": "Bridging StageGate prospects to Cal Admin CRM.",
        "min_score": min_score,
        "refresh_draft": refresh_draft,
    }


@router.post("/run-all")
async def run_all_scrapers(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Manually trigger all scrapers to run immediately.
    ALWAYS runs intelligence scraper in-process (no Redis needed) — guarantees new leads.
    Also queues Celery tasks for job boards, news, RSS, company→news, enrich, etc.
    """
    # 1. ALWAYS run intelligence scraper in-process — quick mode (20 queries, ~3 min)
    background_tasks.add_task(
        _run_intelligence_scraper_sync,
        articles_per_query=15,
        max_queries=20,
        enrich=True,
    )

    def _run_oem_sync():
        from app.database import SessionLocal
        from app.services.oem_discovery import run_oem_discovery
        db = SessionLocal()
        try:
            run_oem_discovery(db, max_queries=20)
        finally:
            db.close()

    background_tasks.add_task(_run_oem_sync)

    # 2. Queue Celery tasks (job boards, news, RSS, company→news, enrich, etc.)
    tasks = {}
    try:
        from worker.tasks import (
            run_job_scraper_task,
            run_hotel_scraper_task,
            run_news_scraper_task,
            run_rss_scraper_task,
            run_company_news_task,
            run_enrich_companies_task,
            run_serp_scraper_task,
            run_logistics_scraper_task,
            run_rfp_marketplace_scraper_task,
            run_intelligence_scraper_task,
            generate_newsletter_edition_task,
        )
        tasks = {
            "intelligence": run_intelligence_scraper_task.delay().id,
            "company_news": run_company_news_task.delay(limit=80).id,
            "enrich_companies": run_enrich_companies_task.delay(limit=80).id,
            "job_boards": run_job_scraper_task.delay().id,
            "hotel_directories": run_hotel_scraper_task.delay().id,
            "news_feeds": run_news_scraper_task.delay().id,
            "rss_feeds": run_rss_scraper_task.delay().id,
            "search_engines": run_serp_scraper_task.delay().id,
            "logistics_directories": run_logistics_scraper_task.delay().id,
            "rfp_marketplaces": run_rfp_marketplace_scraper_task.delay().id,
            "newsletter": generate_newsletter_edition_task.delay(limit=8).id,
        }
    except Exception:
        # Celery/Redis may be down — intelligence still runs in-process
        tasks = {"celery": "unavailable"}

    return {
        "status": "scrapers_started",
        "intelligence": "running_in_process",
        "tasks": tasks,
        "estimated_completion": "20-30 minutes",
        "check_status": "/api/scraper/status",
        "check_leads": "/api/leads/summary",
    }


@router.post("/run/{scraper_type}")
async def run_specific_scraper(
    scraper_type: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Run a specific scraper: intelligence, job_boards, hotels, news, serp, logistics, rfp_marketplace.
    For 'intelligence' runs in-process (no Redis). Others queue to Celery.
    """
    if scraper_type == "intelligence":
        background_tasks.add_task(_run_intelligence_scraper_sync, 15)
        return {
            "status": "scraper_started",
            "scraper_type": "intelligence",
            "message": "Intelligence scraper running in background. Check /api/leads/summary in 10–20 min.",
            "check_leads": "/api/leads/summary",
        }
    try:
        from worker.tasks import (
            run_job_scraper_task,
            run_hotel_scraper_task,
            run_news_scraper_task,
            run_serp_scraper_task,
            run_logistics_scraper_task,
            run_rfp_marketplace_scraper_task,
        )
        from worker.tasks import (
            run_company_news_task,
            run_enrich_companies_task,
            generate_newsletter_edition_task,
        )
        task_map = {
            "job_boards": (run_job_scraper_task, {}),
            "hotels": (run_hotel_scraper_task, {}),
            "news": (run_news_scraper_task, {}),
            "company_news": (run_company_news_task, {"limit": 80}),
            "enrich_companies": (run_enrich_companies_task, {"limit": 80}),
            "newsletter": (generate_newsletter_edition_task, {"limit": 8}),
            "serp": (run_serp_scraper_task, {}),
            "logistics": (run_logistics_scraper_task, {}),
            "rfp_marketplace": (run_rfp_marketplace_scraper_task, {}),
        }
        if scraper_type not in task_map:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown scraper type: {scraper_type}. Use: intelligence, job_boards, hotels, news, company_news, enrich_companies, newsletter, serp, logistics, rfp_marketplace",
            )
        task_fn, kwargs = task_map[scraper_type]
        task = task_fn.delay(**kwargs)
        return {
            "status": "scraper_started",
            "scraper_type": scraper_type,
            "task_id": task.id,
            "estimated_completion": "5-10 minutes",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scraper: {str(e)}")


@router.get("/stats/daily")
async def get_daily_stats(days: int = 7, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get daily lead and signal statistics for the last N days
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Daily company counts
    daily_companies = db.query(
        cast(Company.created_at, Date).label('date'),
        func.count(Company.id).label('count')
    ).filter(
        Company.created_at >= cutoff
    ).group_by(
        cast(Company.created_at, Date)
    ).order_by(
        cast(Company.created_at, Date).desc()
    ).all()
    
    # Daily signal counts
    daily_signals = db.query(
        cast(Signal.created_at, Date).label('date'),
        func.count(Signal.id).label('count')
    ).filter(
        Signal.created_at >= cutoff
    ).group_by(
        cast(Signal.created_at, Date)
    ).order_by(
        cast(Signal.created_at, Date).desc()
    ).all()
    
    # Total stats
    total_companies = db.query(func.count(Company.id)).scalar()
    total_signals = db.query(func.count(Signal.id)).scalar()
    companies_last_24h = db.query(func.count(Company.id)).filter(
        Company.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).scalar()
    signals_last_24h = db.query(func.count(Signal.id)).filter(
        Signal.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).scalar()
    
    return {
        "period_days": days,
        "summary": {
            "total_companies": total_companies,
            "total_signals": total_signals,
            "companies_last_24h": companies_last_24h,
            "signals_last_24h": signals_last_24h,
            "avg_daily_companies": round(companies_last_24h / max(days, 1), 1) if companies_last_24h else 0,
            "avg_daily_signals": round(signals_last_24h / max(days, 1), 1) if signals_last_24h else 0,
        },
        "daily_breakdown": {
            "companies": [{"date": str(d.date), "count": d.count} for d in daily_companies],
            "signals": [{"date": str(d.date), "count": d.count} for d in daily_signals],
        }
    }


@router.get("/status")
async def get_scraper_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get current scraper status and health
    """
    from app.scrapers.scraper_watchdog import get_watchdog
    
    watchdog = get_watchdog()
    watchdog.reload_from_disk()
    health = watchdog.status()
    
    # Calculate daily rate
    companies_last_24h = db.query(func.count(Company.id)).filter(
        Company.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).scalar()
    
    return {
        "health": health,
        "performance": {
            "leads_last_24h": companies_last_24h,
            "target_daily_leads": 150,
            "on_track": companies_last_24h >= 100,
            "percentage_of_target": round((companies_last_24h / 150) * 100, 1) if companies_last_24h else 0,
        },
        "recommendation": (
            "✅ On track for 100-200 leads/day" if companies_last_24h >= 100 
            else "⚠️ Below target - consider running manual scrape or checking scraper health"
        )
    }
