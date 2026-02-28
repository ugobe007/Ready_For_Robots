"""
Admin API
=========
Endpoints for the Ready for Robots admin panel.

  GET  /api/admin/stats              — system counts + recent activity
  POST /api/admin/import/urls        — bulk-import URLs as scrape targets
  POST /api/admin/import/companies   — bulk-import company records (JSON)
  GET  /api/admin/scrape/targets     — list all registered scrape targets
  POST /api/admin/scrape/trigger     — manually trigger a scraper run
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score

router = APIRouter()


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """System-wide counts and recent activity."""
    companies = db.query(func.count(Company.id)).scalar() or 0
    signals   = db.query(func.count(Signal.id)).scalar()  or 0
    scored    = db.query(func.count(Score.id)).scalar()    or 0

    industries = (
        db.query(Company.industry, func.count(Company.id).label("count"))
        .group_by(Company.industry)
        .order_by(desc("count"))
        .limit(8)
        .all()
    )

    sig_types = (
        db.query(Signal.signal_type, func.count(Signal.id).label("count"))
        .group_by(Signal.signal_type)
        .order_by(desc("count"))
        .all()
    )

    recent = (
        db.query(Company)
        .order_by(desc(Company.created_at))
        .limit(10)
        .all()
    )

    return {
        "totals": {
            "companies": companies,
            "signals":   signals,
            "scored":    scored,
        },
        "by_industry": [
            {"industry": r[0] or "Unknown", "count": r[1]} for r in industries
        ],
        "by_signal_type": [
            {"signal_type": r[0], "count": r[1]} for r in sig_types
        ],
        "recent_companies": [
            {
                "id":       c.id,
                "name":     c.name,
                "industry": c.industry,
                "source":   c.source,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in recent
        ],
    }


# ── URL Import ────────────────────────────────────────────────────────────────

class UrlImportPayload(BaseModel):
    urls: List[str]
    label:       Optional[str] = None
    industry:    Optional[str] = None   # Logistics | Hospitality | Healthcare | Food Service
    signal_type: Optional[str] = None
    scrape_now:  bool = False


def _detect_scraper(url: str) -> str:
    u = url.lower()
    if any(x in u for x in ["indeed.com", "linkedin.com", "glassdoor", "ziprecruiter", "monster.com"]):
        return "job_board"
    if any(x in u for x in ["yellowpages", "tripadvisor", "booking.com", "expedia", "hotels.com"]):
        return "hotel_dir"
    if any(x in u for x in ["/rss", "/feed", "atom", "feedburner"]):
        return "rss_feed"
    if any(x in u for x in ["warehouse", "3pl", "logistics-dir", "distribution-dir"]):
        return "logistics_dir"
    return "rss_feed"


def _detect_industries(url: str, hint: Optional[str]) -> List[str]:
    if hint:
        return [hint]
    u = url.lower()
    found = []
    if any(x in u for x in ["hotel", "hospitality", "resort", "lodging", "airbnb"]):
        found.append("Hospitality")
    if any(x in u for x in ["warehouse", "logistics", "fulfillment", "distribution", "3pl", "supply"]):
        found.append("Logistics")
    if any(x in u for x in ["hospital", "health", "medical", "clinic", "pharmacy"]):
        found.append("Healthcare")
    if any(x in u for x in ["restaurant", "food", "kitchen", "qsr", "dining", "cafe"]):
        found.append("Food Service")
    return found or ["Logistics", "Hospitality", "Healthcare", "Food Service"]


@router.post("/import/urls")
def import_urls(payload: UrlImportPayload, background_tasks: BackgroundTasks):
    """
    Accept a list of URLs, auto-detect scraper + industry, and register
    them as active scrape targets. Set scrape_now=true to queue immediately.
    """
    from app.scrapers.scrape_targets import ALL_TARGETS, ScrapeTarget

    existing_urls = {t.url for t in ALL_TARGETS}
    added, skipped = [], []

    for raw in payload.urls:
        url = raw.strip()
        if not url or not url.startswith("http"):
            skipped.append({"url": url, "reason": "invalid URL"})
            continue
        if url in existing_urls:
            skipped.append({"url": url, "reason": "already registered"})
            continue

        scraper    = _detect_scraper(url)
        industries = _detect_industries(url, payload.industry)
        sig_types  = [payload.signal_type] if payload.signal_type else ["labor_pain", "expansion"]

        target = ScrapeTarget(
            url=url,
            label=payload.label or f"Imported: {url[:80]}",
            scraper=scraper,
            industries=industries,
            signal_types=sig_types,
            cadence="daily",
            active=True,
            notes="Manually imported via admin panel",
        )
        ALL_TARGETS.append(target)
        existing_urls.add(url)
        added.append({"url": url, "scraper": scraper, "industries": industries, "signal_types": sig_types})

    if payload.scrape_now and added:
        try:
            from worker.tasks import run_job_scraper_task, run_rss_scraper_task
            job_urls = [a["url"] for a in added if a["scraper"] == "job_board"]
            rss_urls = [a["url"] for a in added if a["scraper"] == "rss_feed"]
            if job_urls:
                background_tasks.add_task(run_job_scraper_task.delay, urls=job_urls)
            if rss_urls:
                background_tasks.add_task(run_rss_scraper_task.delay, urls=rss_urls)
        except Exception:
            pass  # Celery may not be running

    return {
        "added":           len(added),
        "skipped":         len(skipped),
        "targets":         added,
        "skipped_details": skipped,
    }


# ── Company Import ────────────────────────────────────────────────────────────

class CompanyRecord(BaseModel):
    name:           str
    website:        Optional[str] = None
    industry:       Optional[str] = None
    location_city:  Optional[str] = None
    location_state: Optional[str] = None
    source:         Optional[str] = "manual_import"


class CompanyImportPayload(BaseModel):
    companies: List[CompanyRecord]


@router.post("/import/companies")
def import_companies(payload: CompanyImportPayload, db: Session = Depends(get_db)):
    """Bulk-import company records. Skips junk names and duplicates."""
    from app.services.lead_filter import is_junk

    added, skipped = [], []

    for rec in payload.companies:
        junk, reason = is_junk(rec.name)
        if junk:
            skipped.append({"name": rec.name, "reason": reason})
            continue

        existing = db.query(Company).filter(Company.name == rec.name).first()
        if existing:
            skipped.append({"name": rec.name, "reason": "duplicate"})
            continue

        company = Company(
            name=rec.name,
            website=rec.website,
            industry=rec.industry or "Unknown",
            location_city=rec.location_city,
            location_state=rec.location_state,
            source=rec.source,
        )
        db.add(company)
        added.append(rec.name)

    db.commit()
    return {"added": len(added), "skipped": len(skipped), "names": added}


# ── Scrape Targets list ───────────────────────────────────────────────────────

@router.get("/scrape/targets")
def list_scrape_targets(
    scraper:  Optional[str] = None,
    industry: Optional[str] = None,
):
    """List all registered scrape targets."""
    from app.scrapers.scrape_targets import get_targets, summary

    targets = get_targets(scraper=scraper, industry=industry)
    return {
        "summary": summary(),
        "targets": [
            {
                "url":          t.url,
                "label":        t.label,
                "scraper":      t.scraper,
                "industries":   t.industries,
                "signal_types": t.signal_types,
                "cadence":      t.cadence,
                "active":       t.active,
                "notes":        t.notes,
            }
            for t in targets
        ],
    }


# ── Trigger Scrape ────────────────────────────────────────────────────────────

class TriggerScrapePayload(BaseModel):
    scraper:  str = "all"          # all | job_board | hotel_dir | rss_feed | news
    industry: Optional[str] = None
    urls:     Optional[List[str]] = None


@router.post("/scrape/trigger")
def trigger_scrape(payload: TriggerScrapePayload, background_tasks: BackgroundTasks):
    """Queue a scraper run. Returns immediately; work happens in background."""
    try:
        from worker.tasks import (
            run_all_scrapers_task,
            run_job_scraper_task,
            run_hotel_scraper_task,
            run_news_scraper_task,
            run_rss_scraper_task,
        )
        task_map = {
            "all":          run_all_scrapers_task,
            "job_board":    run_job_scraper_task,
            "hotel_dir":    run_hotel_scraper_task,
            "news":         run_news_scraper_task,
            "rss_feed":     run_rss_scraper_task,
        }
        fn = task_map.get(payload.scraper)
        if not fn:
            raise HTTPException(400, f"Unknown scraper '{payload.scraper}'. Options: {list(task_map)}")

        if payload.scraper == "all":
            background_tasks.add_task(fn.delay)
        elif payload.urls:
            background_tasks.add_task(fn.delay, urls=payload.urls)
        else:
            background_tasks.add_task(fn.delay, industry=payload.industry)

        return {"status": "queued", "scraper": payload.scraper, "industry": payload.industry}

    except ImportError:
        return {
            "status": "skipped",
            "reason": "Celery worker not running — start with: celery -A worker.celery_worker worker",
        }
