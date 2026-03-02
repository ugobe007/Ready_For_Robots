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
    scraper:  str = "all"   # all | job_board | hotel_dir | rss_feed | news | serp | logistics | score_recalc
    industry: Optional[str] = None
    urls:     Optional[List[str]] = None


@router.post("/scrape/trigger")
def trigger_scrape(payload: TriggerScrapePayload, background_tasks: BackgroundTasks):
    """Queue a scraper run via APScheduler job functions. Returns immediately; work happens in background."""
    from app.scrapers.scheduled_jobs import (
        job_news, job_rss, job_jobs, job_hotel,
        job_serp, job_logistics, job_score_recalc, job_intelligence,
        job_refresh_cold_leads, job_publish_daily_top25,
        job_enrich_contacts, job_all,
    )

    task_map = {
        "all":                  job_all,
        "news":                 job_news,
        "rss_feed":             job_rss,
        "job_board":            job_jobs,
        "hotel_dir":            job_hotel,
        "serp":                 job_serp,
        "logistics":            job_logistics,
        "score_recalc":         job_score_recalc,
        "intelligence":         job_intelligence,
        "refresh_cold_leads":   job_refresh_cold_leads,
        "publish_daily_top25":  job_publish_daily_top25,
        "enrich_contacts":      job_enrich_contacts,
    }

    fn = task_map.get(payload.scraper)
    if not fn:
        raise HTTPException(400, f"Unknown scraper '{payload.scraper}'. Options: {list(task_map)}")

    background_tasks.add_task(fn)
    return {"status": "queued", "scraper": payload.scraper}


@router.post("/debug/score-sample")
def debug_score_sample(db: Session = Depends(get_db)):
    """Score the first 20 unscored companies inline and return errors.
    Used to diagnose why score_recalc might be failing."""
    from app.services.scoring_engine import compute_scores

    # Find companies without a score record
    scored_ids = {r[0] for r in db.query(Score.company_id).all()}
    unscored = (
        db.query(Company)
        .filter(Company.id.notin_(scored_ids))
        .limit(20)
        .all()
    )

    results = []
    for company in unscored:
        try:
            scores = compute_scores(company, company.signals or [])
            s = Score(company_id=company.id, **scores)
            db.add(s)
            db.commit()
            results.append({"id": company.id, "name": company.name, "status": "ok",
                            "overall": scores["overall_intent_score"]})
        except Exception as ex:
            db.rollback()
            results.append({"id": company.id, "name": company.name,
                            "status": "error", "error": str(ex)})

    return {
        "unscored_count": len(scored_ids),
        "total_companies": db.query(Company).count(),
        "sample_results": results,
    }


@router.post("/debug/score-all")
def debug_score_all(db: Session = Depends(get_db)):
    """Score ALL unscored companies synchronously. Returns totals.
    Safe to call multiple times — skips already-scored companies."""
    from app.services.scoring_engine import compute_scores

    scored_ids = {r[0] for r in db.query(Score.company_id).all()}
    unscored = (
        db.query(Company)
        .filter(Company.id.notin_(scored_ids))
        .all()
    )

    ok = 0
    errors = []
    for company in unscored:
        try:
            scores = compute_scores(company, company.signals or [])
            s = Score(company_id=company.id, **scores)
            db.add(s)
            db.commit()
            ok += 1
        except Exception as ex:
            db.rollback()
            errors.append({"id": company.id, "name": company.name, "error": str(ex)})

    total_scored = db.query(Score.company_id).distinct().count()
    return {
        "newly_scored": ok,
        "errors": errors[:20],  # cap to 20 for readability
        "total_distinct_scored": total_scored,
        "total_companies": db.query(Company).count(),
    }



# ── DB Maintenance ────────────────────────────────────────────────────────────

@router.post("/maintenance/dedup")
def dedup_companies(db: Session = Depends(get_db)):
    """
    Deduplicate the companies table (keep lowest id per name) and
    purge Unknown-industry / news_scraper companies (robot/AI vendors).
    Returns a summary of what was removed.
    """
    from sqlalchemy import text

    def _delete_company_children(ids: list):
        """Delete signals, scores, contacts for a list of company ids before deleting the company rows."""
        if not ids:
            return
        db.execute(text("DELETE FROM signals  WHERE company_id = ANY(:ids)"), {"ids": ids})
        db.execute(text("DELETE FROM scores   WHERE company_id = ANY(:ids)"), {"ids": ids})
        db.execute(text("DELETE FROM contacts WHERE company_id = ANY(:ids)"), {"ids": ids})

    # ── 1. Find duplicate company names ──────────────────────────────────────
    dup_rows = db.execute(text("""
        SELECT name, MIN(id) AS keep_id, array_agg(id ORDER BY id) AS all_ids
        FROM companies
        GROUP BY name
        HAVING COUNT(*) > 1
    """)).fetchall()

    signals_repointed = 0
    companies_deleted = 0

    for row in dup_rows:
        keep_id  = row.keep_id
        del_ids  = [i for i in row.all_ids if i != keep_id]

        # Re-point signals from duplicates to canonical id (before deleting)
        updated = db.execute(
            text("UPDATE signals SET company_id = :keep_id WHERE company_id = ANY(:del_ids)"),
            {"keep_id": keep_id, "del_ids": del_ids},
        ).rowcount
        signals_repointed += updated

        # Delete all child rows for the duplicate companies
        _delete_company_children(del_ids)

        deleted = db.execute(
            text("DELETE FROM companies WHERE id = ANY(:del_ids)"),
            {"del_ids": del_ids},
        ).rowcount
        companies_deleted += deleted

    # ── 2. Purge Unknown-industry vendor companies from news_scraper ─────────
    vendor_ids = [
        r.id for r in db.execute(text("""
            SELECT id FROM companies
            WHERE
              (industry = 'Unknown' AND source = 'news_scraper')
              OR (
                source = 'news_scraper'
                AND (
                  name ILIKE '%robotics%'
                  OR name ILIKE '%robot%'
                  OR name ILIKE '% ai %'
                  OR name ILIKE '% ai'
                  OR name ILIKE 'ai %'
                  OR name ILIKE '%autonomous%'
                  OR name ILIKE '%slated to%'
                  OR name ILIKE '%ice cream'
                  OR name LIKE 'Ice Cream'
                )
              )
        """)).fetchall()
    ]

    orphan_sigs = 0
    vendor_deleted = 0
    if vendor_ids:
        _delete_company_children(vendor_ids)
        orphan_sigs = db.execute(text("""
            SELECT COUNT(*) FROM signals
            WHERE company_id = ANY(:ids)
        """), {"ids": vendor_ids}).scalar() or 0   # already deleted above; count is 0
        vendor_deleted = db.execute(
            text("DELETE FROM companies WHERE id = ANY(:ids)"),
            {"ids": vendor_ids},
        ).rowcount

    # ── 3. Purge junk company names from all scraper sources ─────────────────
    from app.services.lead_filter import is_junk
    import re as _re

    _SENT_VERBS_MAINT = _re.compile(
        r'\b(face|faces|faced|fight|fights|fighting|is|are|was|were|has|have|had|'
        r'work|works|worked|say|says|said|warn|warns|ring|rings|lack|lacks|'
        r'struggle|struggles|suffer|suffers|report|reports|feel|feels|holds|hold|'
        r'plans|plan|aims|aim|tries|uses|use|improves|improve|slows|slow)\b$',
        _re.IGNORECASE,
    )

    # News-headline openers that are never company names
    _HEADLINE_START = _re.compile(
        r'^(how|why|when|where|what|who|the|a|an)\s', _re.IGNORECASE
    )
    # Looks like a standalone abbreviation (e.g. "U.S.", "U.K.", "AI")
    _ABBREV_ONLY = _re.compile(r'^([A-Z]\.)+[A-Z]?\.?$')

    all_companies = db.execute(text("SELECT id, name FROM companies")).fetchall()
    junk_ids = []
    for row in all_companies:
        name = row.name or ""
        words = name.split()
        junk, _ = is_junk(name)
        has_non_ascii = bool(_re.search(r'[^\x00-\x7F]', name))
        ends_with_prep = bool(_re.search(
            r'\b(over|amid|about|because|during|after|before|into|onto|with|'
            r'of|for|in|on|by|from|at|to)\b$', name, _re.IGNORECASE))
        is_headline = bool(_HEADLINE_START.match(name)) and len(words) > 2
        is_abbrev = bool(_ABBREV_ONLY.match(name))
        fragment = (
            len(words) > 6 or
            _SENT_VERBS_MAINT.search(name) or
            ends_with_prep or
            has_non_ascii or
            is_headline or
            is_abbrev or
            (len(words) >= 4 and not any(w[0].isupper() for w in words if w))
        )
        if junk or fragment:
            junk_ids.append(row.id)

    junk_deleted = 0
    if junk_ids:
        _delete_company_children(junk_ids)
        junk_deleted = db.execute(
            text("DELETE FROM companies WHERE id = ANY(:ids)"),
            {"ids": junk_ids},
        ).rowcount

    # ── 4. Ensure unique index exists ─────────────────────────────────────────
    try:
        db.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_companies_name ON companies (name)
        """))
    except Exception:
        pass  # non-fatal: may fail if duplicates remain

    db.commit()

    return {
        "status": "ok",
        "duplicate_companies_removed": companies_deleted,
        "signals_repointed":           signals_repointed,
        "vendor_companies_purged":     vendor_deleted,
        "junk_companies_purged":       junk_deleted,
        "orphan_signals_purged":       len(vendor_ids),
    }
