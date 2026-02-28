"""
Intelligence Search API
=======================
GET /api/search           — keyword + category full-text search across signals & companies
GET /api/search/categories — list available preset categories

Query params:
  q         str    free-text query (matched against signal text & company name)
  category  str    preset category key (see CATEGORY_KEYWORDS below)
  limit     int    default 30  (max 100)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional, List

from app.database import get_db
from app.models.company import Company
from app.models.signal import Signal

router = APIRouter()

# ---------------------------------------------------------------------------
# Category → keyword seeds  (case-insensitive ILIKE on signal_text)
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS: dict = {
    "automation_investment": [
        "invest", "fund", "raise", "capital", "round", "grant", "pilot",
        "robotic", "automat", "startup", "university", "government",
        "DoD", "NSF", "SBIR", "Series A", "Series B", "strategic partner",
        "joint venture", "venture", "seed round",
    ],
    "acquisitions": [
        "acqui", "merger", "buyout", "M&A", "acquired", "takes over",
        "strategic purchase", "divestiture", "fold into", "absorb",
        "carve-out", "spin-off",
    ],
    "labor_downsizing": [
        "layoff", "lay-off", "downsize", "reduction in force", "RIF",
        "furlough", "job cut", "workforce reduction", "headcount reduction",
        "restructur", "labor shortage", "can't find workers", "labor cost",
        "overtime", "turnover", "absenteeism", "attrition", "staffing crisis",
    ],
    "intra_logistics": [
        "intralogistic", "intra-logistic", "warehouse automation",
        "distribution center", "AGV", "AMR", "autonomous mobile robot",
        "conveyor", "sortation", "goods-to-person", "pick-to-light",
        "fulfillment center", "cross-dock", "pallet", "depalletiz",
        "robot arm", "collaborative robot", "cobot",
    ],
    "pack_work": [
        "pack out", "pack-out", "packing", "packout", "co-pack",
        "pick and pack", "pick & pack", "pack station", "end-of-line",
        "case packing", "secondary packaging", "tray packing",
    ],
    "kitting": [
        "kitting", "kit assembly", "kit fulfillment", "kit build",
        "sub-assembly", "subassembly", "light assembly", "value-added",
        "postponement", "build to order", "BOM", "bill of materials",
    ],
    "restocking": [
        "restock", "re-stock", "replenish", "shelf repl", "auto-replen",
        "cycle count", "inventory refresh", "auto-fill", "kanban",
        "continuous replenishment", "VMI", "vendor managed inventory",
    ],
    "inventory_management": [
        "inventory", "WMS", "warehouse management system", "stock count",
        "SKU", "asset tracking", "RFID", "real-time tracking", "ERP",
        "supply chain visibility", "serialization", "lot tracking",
        "inventory visibility", "perpetual inventory",
    ],
    "healthcare_automation": [
        "health system", "healthcare", "hospital ", "hospitals ",
        "pharmacy", "medical center", "EVS", "environmental services",
        "clinical", "patient transport", "surgical", "ICU",
        "sterile processing", "CSSD", "medication", "specimen",
        "nursing shortage", "linen", "care facility",
        "delivery bot", "health care",
    ],
    "retail_automation": [
        "retail", "grocery", "supermarket", "convenience store",
        "store fulfillment", "last mile", "click and collect",
        "micro-fulfillment", "dark store", "front-of-store",
        "back-of-store", "planogram", "scan-and-go",
        "autonomous checkout", "inventory drone",
    ],
}

CATEGORY_LABELS: dict = {
    "automation_investment": "Automation Investments",
    "acquisitions":          "Acquisitions & M&A",
    "labor_downsizing":      "Labor Downsizing",
    "intra_logistics":       "Intra-Logistics",
    "pack_work":             "Pack In / Pack Out",
    "kitting":               "Kitting & Assembly",
    "restocking":            "Restocking",
    "inventory_management":  "Inventory Management",
    "healthcare_automation": "Healthcare Automation",
    "retail_automation":     "Retail Automation",
}


def _run_keyword_search(
    db: Session,
    keywords: List[str],
    free_text: Optional[str],
    limit: int,
) -> list:
    """ILIKE match signals (and optionally company names) for given keywords."""

    conditions = [Signal.signal_text.ilike(f"%{kw}%") for kw in keywords]
    if free_text and free_text.strip():
        conditions.append(Signal.signal_text.ilike(f"%{free_text.strip()}%"))

    if not conditions:
        return []

    rows = (
        db.query(
            Signal.company_id,
            Signal.signal_text,
            Signal.signal_type,
            Signal.signal_strength,
        )
        .filter(or_(*conditions))
        .all()
    )

    # group matched signals by company_id
    company_signals: dict = {}
    for row in rows:
        company_signals.setdefault(row.company_id, []).append(
            {
                "signal_type": row.signal_type,
                "signal_text": row.signal_text,
                "strength": round(float(row.signal_strength), 3),
            }
        )

    # also match company names if free_text provided
    if free_text and free_text.strip():
        name_rows = (
            db.query(Company.id)
            .filter(Company.name.ilike(f"%{free_text.strip()}%"))
            .all()
        )
        for (cid,) in name_rows:
            company_signals.setdefault(cid, [])

    if not company_signals:
        return []

    companies = (
        db.query(Company)
        .options(joinedload(Company.scores))
        .filter(Company.id.in_(list(company_signals.keys())))
        .all()
    )

    results = []
    for c in companies:
        score = round(float(c.scores.overall_intent_score), 1) if c.scores else 0.0
        matched = sorted(
            company_signals.get(c.id, []),
            key=lambda x: x["strength"],
            reverse=True,
        )
        results.append(
            {
                "id": c.id,
                "company_name": c.name,
                "industry": c.industry,
                "location_city": c.location_city,
                "location_state": c.location_state,
                "website": c.website,
                "employee_estimate": c.employee_estimate,
                "overall_score": score,
                "matched_signals": matched[:4],
            }
        )

    results.sort(key=lambda x: x["overall_score"], reverse=True)
    return results[:limit]


@router.get("")
@router.get("/")
def search(
    q: Optional[str] = Query(None, description="Free-text query"),
    category: Optional[str] = Query(None, description="Preset category key"),
    limit: int = Query(30, le=100, description="Max results (hard cap 100)"),
    db: Session = Depends(get_db),
):
    """
    Full-text search across signal texts.
    Combine a preset category (keyword seed list) with optional free-text.
    """
    keywords: List[str] = []
    if category and category in CATEGORY_KEYWORDS:
        keywords = CATEGORY_KEYWORDS[category]

    results = _run_keyword_search(db, keywords, q, limit)

    return {
        "results": results,
        "total": len(results),
        "query": q,
        "category": category,
        "category_label": CATEGORY_LABELS.get(category) if category else None,
    }


@router.get("/categories")
def list_categories():
    """Return all available preset search categories."""
    return [{"key": k, "label": v} for k, v in CATEGORY_LABELS.items()]
