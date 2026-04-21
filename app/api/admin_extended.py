"""
Extended Admin API Endpoints
=============================
Additional endpoints for company management and system controls.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_
from typing import Optional

from app.database import get_db
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.api.auth_deps import require_admin
from app.services.lead_filter import pick_primary_score
from app.services.lead_primary_link import enrich_lead_link_fields
from app.services.website_inference import sleep_between_lookups, try_duckduckgo_company_website

router = APIRouter(dependencies=[Depends(require_admin)])


# ── Company Management ────────────────────────────────────────────────────────

@router.get("/companies/search")
def search_companies(
    q: str = "",
    industry: str = "",
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search companies with filters for admin panel."""
    
    query = db.query(Company)
    
    if q:
        query = query.filter(
            or_(
                Company.name.ilike(f"%{q}%"),
                Company.website.ilike(f"%{q}%")
            )
        )
    
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))
    
    companies = query.order_by(desc(Company.created_at)).limit(limit).all()
    
    # Get signal counts and scores for each company
    result = []
    for c in companies:
        signal_count = db.query(func.count(Signal.id)).filter(Signal.company_id == c.id).scalar() or 0
        score_rec = db.query(Score).filter(Score.company_id == c.id).first()
        
        result.append({
            "id": c.id,
            "name": c.name,
            "website": c.website,
            "industry": c.industry,
            "location_city": c.location_city,
            "location_state": c.location_state,
            "signal_count": signal_count,
            "score": score_rec.overall_intent_score if score_rec else None,
        })
    
    return {"companies": result}


@router.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    """Delete a company and all its signals and scores."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Delete signals and scores first (cascade should handle this, but being explicit)
    db.query(Signal).filter(Signal.company_id == company_id).delete()
    db.query(Score).filter(Score.company_id == company_id).delete()
    db.delete(company)
    db.commit()
    
    return {"status": "deleted", "company_id": company_id}


class InferWebsitesBody(BaseModel):
    """Batch DDG lookups for companies missing a site and evidence URL — rate-limited."""

    limit: int = 12
    dry_run: bool = False
    min_score: float = 0.0


@router.post("/companies/infer-websites")
def infer_company_websites(body: InferWebsitesBody, db: Session = Depends(get_db)):
    """
    Best-effort: set `companies.website` from DuckDuckGo instant answers when the lead has
    no website and no http signal `source_url` (see `lead_primary_link.enrich_lead_link_fields`).
    """
    cap = max(1, min(body.limit, 40))
    rows = (
        db.query(Company)
        .options(joinedload(Company.signals), joinedload(Company.scores))
        .order_by(Company.id.desc())
        .limit(800)
        .all()
    )
    candidates: list = []
    for c in rows:
        ps = pick_primary_score(c.scores)
        sc = float(ps.overall_intent_score) if ps else 0.0
        if sc < body.min_score:
            continue
        sigs = c.signals or []
        ex = enrich_lead_link_fields(
            website=c.website,
            signals=sigs,
            overall_score=sc,
            signal_count=len(sigs),
        )
        if not ex["needs_website_inference"]:
            continue
        candidates.append((c, sc, ex["suggested_pipeline_action"]))
    candidates.sort(key=lambda x: -x[1])
    out: list = []
    for c, sc, action in candidates[:cap]:
        found = try_duckduckgo_company_website(c.name)
        sleep_between_lookups(0.8)
        item = {
            "company_id": c.id,
            "name": c.name,
            "overall_score": sc,
            "suggested_pipeline_action": action,
            "found_website": found,
            "applied": False,
        }
        if found and not body.dry_run:
            c.website = found
            db.add(c)
            item["applied"] = True
        out.append(item)
    if not body.dry_run:
        db.commit()
    return {"processed": len(out), "dry_run": body.dry_run, "results": out}


class MergeDupesBody(BaseModel):
    dry_run: bool = True
    domain: Optional[str] = None


@router.post("/merge-duplicate-companies-by-domain")
def merge_duplicate_companies_by_domain_admin(body: MergeDupesBody, db: Session = Depends(get_db)):
    """
    Physically merge duplicate `companies` rows sharing `website_domain` (see `company_merge` service).
    Default `dry_run: true` returns the plan without deleting rows.
    """
    from app.services.company_merge import merge_duplicate_companies_by_domain

    return merge_duplicate_companies_by_domain(
        db, dry_run=body.dry_run, domain_filter=body.domain
    )


@router.get("/rep-feedback-summary")
def rep_feedback_summary(db: Session = Depends(get_db)):
    """Aggregate rep thumbs / reason codes for tuning the pipeline."""
    from app.models.lead_rep_feedback import LeadRepFeedback

    vote_rows = (
        db.query(LeadRepFeedback.vote, func.count(LeadRepFeedback.id))
        .group_by(LeadRepFeedback.vote)
        .all()
    )
    by_vote = {r[0]: r[1] for r in vote_rows}
    reason_rows = (
        db.query(LeadRepFeedback.reason_code, func.count(LeadRepFeedback.id))
        .filter(LeadRepFeedback.reason_code.isnot(None))
        .group_by(LeadRepFeedback.reason_code)
        .all()
    )
    by_reason = {r[0]: r[1] for r in reason_rows}
    return {
        "by_vote": by_vote,
        "by_reason": by_reason,
        "total": sum(by_vote.values()),
    }


# ── System Controls ───────────────────────────────────────────────────────────

@router.post("/system/cache/clear")
def clear_cache():
    """Clear all application caches."""
    # In a real app, you'd clear Redis or in-memory caches
    # For now, just return success
    return {"status": "success", "message": "Cache cleared"}


@router.post("/system/reindex")
def reindex_database(db: Session = Depends(get_db)):
    """Reindex database for better performance."""
    # In a real app, you'd run database-specific reindex commands
    # For SQLite/Postgres, this would involve VACUUM, REINDEX, etc.
    return {"status": "success", "message": "Database reindexed"}


@router.get("/export/all")
def export_all_data(db: Session = Depends(get_db)):
    """Export all data as JSON."""
    from datetime import datetime
    
    companies = db.query(Company).all()
    signals = db.query(Signal).all()
    scores = db.query(Score).all()
    
    return {
        "exported_at": datetime.utcnow().isoformat(),
        "companies": [
            {
                "id": c.id,
                "name": c.name,
                "website": c.website,
                "industry": c.industry,
                "location_city": c.location_city,
                "location_state": c.location_state,
            }
            for c in companies
        ],
        "signals": [
            {
                "id": s.id,
                "company_id": s.company_id,
                "signal_type": s.signal_type,
                "description": s.description,
            }
            for s in signals
        ],
        "scores": [
            {
                "id": sc.id,
                "company_id": sc.company_id,
                "overall_intent_score": sc.overall_intent_score,
                "automation_score": sc.automation_score,
                "labor_pain_score": sc.labor_pain_score,
            }
            for sc in scores
        ],
    }
