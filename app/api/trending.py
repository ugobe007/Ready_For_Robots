"""
Trending API
============
GET /api/trending

Returns the top 25 highest-weighted signals across all companies.
Used by the frontend trending ticker to display live robot-automation needs.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.signal import Signal
from app.services.signal_ranker import compute_weighted_score, SIGNAL_TYPE_WEIGHTS

router = APIRouter()

# Human-readable labels for signal types
SIGNAL_LABELS: dict[str, str] = {
    "strategic_hire": "Strategic Hire",
    "capex":          "CapEx",
    "labor_shortage": "Labor Shortage",
    "expansion":      "Expansion",
    "funding_round":  "Funding",
    "ma_activity":    "M&A",
    "job_posting":    "Job Posting",
    "news":           "News",
}


@router.get("")
@router.get("/")
def get_trending(limit: int = 25, db: Session = Depends(get_db)):
    """
    Pull up to 500 signals (with their companies pre-loaded), rank them by
    compute_weighted_score, and return the top `limit` items.
    """
    signals = (
        db.query(Signal)
        .options(joinedload(Signal.company))
        .filter(Signal.signal_text.isnot(None))
        .limit(500)
        .all()
    )

    items = []
    for s in signals:
        if not s.company:
            continue
        ws = compute_weighted_score(s)
        items.append(
            {
                "company_name": s.company.name,
                "industry":     s.company.industry or "",
                "signal_type":  s.signal_type or "news",
                "signal_label": SIGNAL_LABELS.get(s.signal_type or "", s.signal_type or ""),
                "signal_text":  (s.signal_text or "")[:200],
                "strength":     round(float(s.signal_strength or 0), 2),
                "weighted_score": ws,
            }
        )

    items.sort(key=lambda x: x["weighted_score"], reverse=True)
    return {"items": items[:limit]}
