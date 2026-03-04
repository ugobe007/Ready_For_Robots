"""
Agent API
=========
  GET  /api/agent/insights              — full ML analysis (sources, patterns, strategies)
  GET  /api/agent/strategy/{company_id} — approach strategy for a single company
  GET  /api/agent/profile/{company_id}  — full AI analysis: strategy + robot match + DMs + intel links
  POST /api/agent/scrape/url            — quick-add a URL to scrape from dashboard
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import urllib.parse

from app.database import get_db
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.models.robot import Robot
from app.services.ml_agent import MLAgent, _build_strategy, insights_to_dict

router = APIRouter()


# Helper function to get robots from database
def _get_robots_for_industry(industry: str, db: Session, limit: int = 5):
    """Get robots from database that match the given industry."""
    robots = db.query(Robot).filter(Robot.is_active == True).all()
    
    # Filter by industry in Python for SQLite compatibility
    filtered = [r for r in robots if r.industries and industry in r.industries][:limit]
    
    return [{
        "name": r.name,
        "vendor": r.vendor,
        "tagline": r.tagline,
        "url": r.product_url,
        "use_cases": r.use_cases or [],
        "industries": r.industries or [],
        "roi_stat": r.roi_stat,
        "robot_type": r.robot_type,
    } for r in filtered]


def _get_all_active_robots(db: Session):
    """Get all active robots from database."""
    robots = db.query(Robot).filter(Robot.is_active == True).all()
    
    result = {}
    for r in robots:
        key = r.name.upper().replace(" ", "_").replace("-", "_")
        result[key] = {
            "name": r.name,
            "vendor": r.vendor,
            "tagline": r.tagline,
            "url": r.product_url,
            "use_cases": r.use_cases or [],
            "industries": r.industries or [],
            "roi_stat": r.roi_stat,
        }
    return result


# Decision-maker roles per industry with LinkedIn search query
_DM_ROLES = {
    "Hospitality": [
        {"title": "VP of Operations",           "dept": "Operations"},
        {"title": "General Manager",             "dept": "Executive"},
        {"title": "Director of Food & Beverage", "dept": "F&B"},
        {"title": "Director of Rooms",           "dept": "Rooms"},
        {"title": "VP of Facilities",            "dept": "Facilities"},
        {"title": "Chief Operating Officer",     "dept": "Executive"},
    ],
    "Logistics": [
        {"title": "VP of Supply Chain",                "dept": "Supply Chain"},
        {"title": "Director of Warehouse Operations",  "dept": "Operations"},
        {"title": "COO",                               "dept": "Executive"},
        {"title": "VP of Operations",                  "dept": "Operations"},
        {"title": "Director of Distribution",          "dept": "Distribution"},
        {"title": "VP of Fulfillment",                 "dept": "Fulfillment"},
    ],
    "Healthcare": [
        {"title": "COO",                                 "dept": "Executive"},
        {"title": "Director of Support Services",        "dept": "EVS/Support"},
        {"title": "VP of Facilities Management",         "dept": "Facilities"},
        {"title": "Director of Clinical Operations",     "dept": "Clinical"},
        {"title": "VP of Patient Experience",            "dept": "Patient Exp"},
        {"title": "Director of Environmental Services",  "dept": "EVS"},
    ],
    "Food Service": [
        {"title": "Director of Operations",   "dept": "Operations"},
        {"title": "VP of Culinary",           "dept": "Culinary"},
        {"title": "COO",                      "dept": "Executive"},
        {"title": "VP of Restaurant Operations", "dept": "Operations"},
        {"title": "Director of Technology",   "dept": "Technology"},
    ],
}
_DEFAULT_ROLES = [
    {"title": "COO",              "dept": "Executive"},
    {"title": "VP of Operations", "dept": "Operations"},
    {"title": "CTO",              "dept": "Technology"},
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _linkedin_people_url(company_name: str, title: str) -> str:
    q = urllib.parse.quote(f"{title} {company_name}")
    return f"https://www.linkedin.com/search/results/people/?keywords={q}"

def _linkedin_company_url(company_name: str) -> str:
    q = urllib.parse.quote(company_name)
    return f"https://www.linkedin.com/search/results/companies/?keywords={q}"

def _intelligence_links(company_name: str, website: str = None) -> list:
    name_enc = urllib.parse.quote(company_name)
    links = [
        {"label": "LinkedIn Company",  "url": _linkedin_company_url(company_name), "icon": "li"},
        {"label": "Crunchbase",        "url": f"https://www.crunchbase.com/search/organizations/field/organizations/facet_ids/company?q={name_enc}", "icon": "cb"},
        {"label": "D&B Hoovers",       "url": f"https://www.dnb.com/business-directory/company-search.html#q={name_enc}", "icon": "db"},
        {"label": "Google News",       "url": f"https://news.google.com/search?q={name_enc}+automation+robotics", "icon": "gn"},
        {"label": "Google News (HR)",  "url": f"https://news.google.com/search?q={name_enc}+labor+shortage+staffing+hiring", "icon": "gn"},
        {"label": "ZoomInfo",          "url": f"https://www.zoominfo.com/s/#!search/company/{name_enc}", "icon": "zi"},
    ]
    if website:
        links.insert(0, {"label": "Company Website", "url": website, "icon": "web"})
    return links

def _robot_positioning(company: Company, score: Score, sigs: list, db: Session) -> list:
    """Get robot recommendations from database based on company industry and signals."""
    industry = company.industry or "Unknown"
    
    # Get robots from database for this industry
    all_robots = db.query(Robot).filter(Robot.is_active == True).all()
    
    # Filter by industry in Python for SQLite compatibility
    robots_query = [r for r in all_robots if r.industries and industry in r.industries]
    
    # Sort by preference: preferred robots first
    robots_query.sort(key=lambda r: (not r.is_preferred, r.vendor, r.name))
    
    # Fallback to any active robots if no industry match
    if not robots_query:
        robots_query = all_robots[:5]
        robots_query.sort(key=lambda r: (not r.is_preferred, r.vendor, r.name))

    sig_types = {s.signal_type for s in sigs}

    recommendations = []
    for robot in robots_query[:3]:  # Top 3 recommendations
        # Build why-now rationale
        why = []
        if "labor_shortage" in sig_types or "labor_pain" in sig_types:
            why.append("Acute labor shortage makes this a replace-or-augment priority")
        if "expansion" in sig_types:
            why.append("New locations are the ideal deployment window — spec robots into build-out")
        if "capex" in sig_types or "funding_round" in sig_types:
            why.append("Capital is allocated — this is the window to close")
        if "automation_intent" in sig_types or "strategic_hire" in sig_types:
            why.append("Active evaluation underway — get in before a competitor does")
        if not why:
            why.append(f"Strong {industry} market fit — ROI achievable in 12–18 months")

        recommendations.append({
            "name": robot.name,
            "vendor": robot.vendor,
            "tagline": robot.tagline,
            "url": robot.product_url,
            "use_cases": robot.use_cases or [],
            "industries": robot.industries or [],
            "roi_stat": robot.roi_stat,
            "why_now": why[:2],
            "priority": "PRIMARY" if len(recommendations) == 0 else "SECONDARY",
        })

    return recommendations

def _decision_makers(company: Company) -> list:
    industry = company.industry or "Unknown"
    roles = _DM_ROLES.get(industry, _DEFAULT_ROLES)
    company_name = company.name or ""
    return [
        {
            **role,
            "linkedin_search": _linkedin_people_url(company_name, role["title"]),
            "linkedin_company": _linkedin_company_url(company_name),
        }
        for role in roles
    ]


# ── Insights ──────────────────────────────────────────────────────────────────

@router.get("/insights")
def get_insights(db: Session = Depends(get_db)):
    insights = MLAgent.run(db)
    return insights_to_dict(insights)


# ── Per-company strategy (legacy, kept for compatibility) ──────────────────────

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


# ── Full AI profile (strategy + robot match + DMs + intel links) ──────────────

@router.get("/profile/{company_id}")
def get_profile(company_id: int, db: Session = Depends(get_db)):
    """
    Full AI analysis for a company — powers the AI Analysis modal.
    Returns strategy + robot product recommendations + decision maker targeting
    + intelligence/research links.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    score = company.scores
    sigs  = company.signals or []

    # Strategy (falls back gracefully if no score)
    if score:
        strategy = _build_strategy(company, score, sigs)
        strategy_dict = {
            "urgency":       strategy.urgency,
            "contact_role":  strategy.contact_role,
            "pitch_angle":   strategy.pitch_angle,
            "talking_points": strategy.talking_points,
            "best_channel":  strategy.best_channel,
            "timing_note":   strategy.timing_note,
            "confidence":    strategy.confidence,
        }
    else:
        strategy_dict = None

    # Scores
    score_dict = {
        "overall_score":    round(score.overall_intent_score, 1)  if score else 0,
        "automation_score": round(score.automation_score, 1)      if score else 0,
        "labor_pain_score": round(score.labor_pain_score, 1)      if score else 0,
        "expansion_score":  round(score.expansion_score, 1)       if score else 0,
        "market_fit_score": round(score.robotics_fit_score, 1)    if score else 0,
    } if score else {}

    # Signals summary
    sig_summary = [
        {
            "signal_type": s.signal_type,
            "strength": round(float(s.signal_strength or 0), 2),
            "text": (s.signal_text or "")[:300],
            "source_url": s.source_url,
        }
        for s in sorted(sigs, key=lambda x: float(x.signal_strength or 0), reverse=True)[:10]
    ]

    return {
        "company": {
            "id":               company.id,
            "name":             company.name,
            "industry":         company.industry,
            "website":          company.website,
            "location_city":    company.location_city,
            "location_state":   company.location_state,
            "employee_estimate":company.employee_estimate,
            "source":           company.source,
        },
        "scores":          score_dict,
        "strategy":        strategy_dict,
        "robot_match":     _robot_positioning(company, score, sigs, db),
        "decision_makers": _decision_makers(company),
        "intel_links":     _intelligence_links(company.name, company.website),
        "signals":         sig_summary,
        "signal_count":    len(sigs),
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
