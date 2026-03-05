"""
Scraper control API - Manual trigger and monitoring
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, cast, Date
from app.database import get_db
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.signal import Signal

router = APIRouter(prefix="/api/scraper", tags=["scraper-control"])


@router.post("/run-all")
async def run_all_scrapers(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Manually trigger all scrapers to run immediately.
    Returns task IDs and estimated completion time.
    """
    try:
        from worker.tasks import (
            run_job_scraper_task,
            run_hotel_scraper_task,
            run_news_scraper_task,
            run_serp_scraper_task,
            run_logistics_scraper_task,
        )
        
        # Trigger all scraper tasks
        job_task = run_job_scraper_task.delay()
        hotel_task = run_hotel_scraper_task.delay()
        news_task = run_news_scraper_task.delay()
        serp_task = run_serp_scraper_task.delay()
        logistics_task = run_logistics_scraper_task.delay()
        
        return {
            "status": "scrapers_started",
            "tasks": {
                "job_boards": job_task.id,
                "hotel_directories": hotel_task.id,
                "news_feeds": news_task.id,
                "search_engines": serp_task.id,
                "logistics_directories": logistics_task.id,
            },
            "estimated_completion": "20-30 minutes",
            "check_status": "/api/scraper/status",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scrapers: {str(e)}")


@router.post("/run/{scraper_type}")
async def run_specific_scraper(scraper_type: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Run a specific scraper type: job_boards, hotels, news, serp, logistics
    """
    try:
        from worker.tasks import (
            run_job_scraper_task,
            run_hotel_scraper_task,
            run_news_scraper_task,
            run_serp_scraper_task,
            run_logistics_scraper_task,
        )
        
        task_map = {
            "job_boards": run_job_scraper_task,
            "hotels": run_hotel_scraper_task,
            "news": run_news_scraper_task,
            "serp": run_serp_scraper_task,
            "logistics": run_logistics_scraper_task,
        }
        
        if scraper_type not in task_map:
            raise HTTPException(status_code=400, detail=f"Unknown scraper type: {scraper_type}")
        
        task = task_map[scraper_type].delay()
        
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
        cast(Signal.detected_at, Date).label('date'),
        func.count(Signal.id).label('count')
    ).filter(
        Signal.detected_at >= cutoff
    ).group_by(
        cast(Signal.detected_at, Date)
    ).order_by(
        cast(Signal.detected_at, Date).desc()
    ).all()
    
    # Total stats
    total_companies = db.query(func.count(Company.id)).scalar()
    total_signals = db.query(func.count(Signal.id)).scalar()
    companies_last_24h = db.query(func.count(Company.id)).filter(
        Company.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).scalar()
    signals_last_24h = db.query(func.count(Signal.id)).filter(
        Signal.detected_at >= datetime.utcnow() - timedelta(hours=24)
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
