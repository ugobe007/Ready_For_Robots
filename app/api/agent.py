"""
Agent API
=========
  GET  /api/agent/insights             — full ML analysis (sources, patterns, strategies)
  GET  /api/agent/strategy/{company_id} — approach strategy for a single company
  POST /api/agent/scrape/url           — quick-add a URL to scrape from dashboard
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.services.ml_agent import MLAgent, _build_strategy, insights_to_dict

router = APIRouter()


# ── Full insights ──────────────────────────────────────────────────────────────

@router.get("/insights")
def get_insights(db: Session = Depends(get_db)):
    """
    Run the ML agent over all collected data and return:
      - source_rankings: which scrape sources produce the best leads
      - signal_patterns: signal combinations that correlate with high scores
      - top_strategies:  tailored approach strategies for the best companies
      - recommended_targets: new URLs the agent recommends scraping
      - learning_notes: what the agent has learned from current data
      - coverage_gaps:  industries / signal types that are under-represented
    """
    insights = MLAgent.run(db)
    return insights_to_dict(insights)


# ── Per-company strategy ───────────────────────────────────────────────────────

@router.get("/strategy/{company_id}")
def get_strategy(company_id: int, db: Session = Depends(get_db)):
    """Generate a tailored approach strategy for a specific company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    score = company.scores
    if not score:
        raise HTTPException(status_code=422, detail="Company has no score data yet")

    sigs     = company.signals or []
    strategy = _build_strategy(company, score, sigs)

    return {
        "company_id":    strategy.company_id,
        "company_name":  strategy.company_name,
        "urgency":       strategy.urgency,
        "contact_role":  strategy.contact_role,
        "pitch_angle":   strategy.pitch_angle,
        "talking_points": strategy.talking_points,
        "best_channel":  strategy.best_channel,
        "timing_note":   strategy.timing_note,
        "confidence":    strategy.confidence,
    }


# ── Quick URL scrape ───────────────────────────────────────────────────────────

class QuickScrapePayload(BaseModel):
    urls: str                    # newline-separated URLs
    industry: Optional[str] = None
    scrape_now: bool = False


@router.post("/scrape/quick")
def quick_scrape(payload: QuickScrapePayload, db: Session = Depends(get_db)):
    """
    Fast path: paste URLs from the dashboard → add to scrape targets.
    Wraps the admin import/urls endpoint logic. Returns immediately.
    """
    from app.scrapers.scrape_targets import ALL_TARGETS, ScrapeTarget

    lines = [u.strip() for u in payload.urls.splitlines() if u.strip()]
    if not lines:
        raise HTTPException(status_code=422, detail="No valid URLs provided")

    added    = []
    skipped  = []
    existing = {t.url for t in ALL_TARGETS}

    for url in lines:
        if url in existing:
            skipped.append(url)
            continue
        ALL_TARGETS.append(ScrapeTarget(
            url=url,
            scraper_type=_detect_scraper(url),
            industry=payload.industry or _detect_industry(url),
            label=f"Quick import: {url[:60]}",
            notes="Added via dashboard quick-scrape",
        ))
        added.append(url)

    tasks_queued = 0
    if payload.scrape_now and added:
        try:
            from worker.tasks import run_scraper
            for url in added:
                run_scraper.delay("job_board", [url])
                tasks_queued += 1
        except Exception:
            pass  # Celery not available — silently skip

    return {
        "added":        len(added),
        "skipped":      len(skipped),
        "tasks_queued": tasks_queued,
        "urls":         added,
    }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _detect_scraper(url: str) -> str:
    url = url.lower()
    if any(k in url for k in ("simplyhired", "indeed", "ziprecruiter", "linkedin", "workday")):
        return "job_board"
    if any(k in url for k in ("hotel", "hospitality", "ahla", "tripadvisor")):
        return "hotel_dir"
    if any(k in url for k in ("logistics", "freight", "warehouse", "supply")):
        return "logistics_dir"
    return "news"


def _detect_industry(url: str) -> Optional[str]:
    url = url.lower()
    if any(k in url for k in ("hotel", "hospitality", "restaurant", "food", "dining")):
        return "Hospitality"
    if any(k in url for k in ("logistics", "freight", "warehouse", "supply", "shipping")):
        return "Logistics"
    if any(k in url for k in ("health", "hospital", "medical", "clinical")):
        return "Healthcare"
    if any(k in url for k in ("qsr", "fastfood", "foodservice")):
        return "Food Service"
    return None
