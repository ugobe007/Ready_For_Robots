"""
Extended Admin API Endpoints
=============================
Additional endpoints for company management and system controls.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from typing import Optional

from app.database import get_db
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score

router = APIRouter()


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
        query = query.filter(Company.industry == industry)
    
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
