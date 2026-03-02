"""
Intelligence API
================
GET /api/intelligence          — paginated feed, filterable by category / tag
GET /api/intelligence/summary  — counts + last_fetched per category
POST /api/intelligence/refresh — trigger a fresh scrape (admin)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

CATEGORY_LABELS = {
    "MA_WATCH":   "M&A Watch",
    "HUMANOID":   "Humanoid Market",
    "COMPETITOR": "Competitor Landscape",
    "MARKET":     "Market Signals",
    "INDUSTRY":   "Industry Trends",
    "PARTNER":    "Partner & Tech Ecosystem",
    "FOUNDATION": "VLA & Foundation Models",
}

CATEGORY_ORDER = ["MA_WATCH", "HUMANOID", "COMPETITOR", "MARKET", "INDUSTRY", "PARTNER", "FOUNDATION"]


# ── helpers ─────────────────────────────────────────────────────────────────

def _table_exists(db: Session) -> bool:
    row = db.execute(text("""
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'intelligence_items'
    """)).fetchone()
    return row is not None


def _row_to_dict(row) -> dict:
    return {
        "id":              row.id,
        "title":           row.title,
        "summary":         row.summary or "",
        "source_url":      row.source_url or "",
        "source_name":     row.source_name or "",
        "category":        row.category,
        "category_label":  CATEGORY_LABELS.get(row.category, row.category),
        "tag":             row.tag or "",
        "relevance_score": getattr(row, "relevance_score", 0) or 0,
        "pub_date":        row.pub_date.isoformat() if row.pub_date else None,
        "fetched_at":      row.fetched_at.isoformat() if row.fetched_at else None,
    }


# ── endpoints ────────────────────────────────────────────────────────────────

@router.get("/intelligence")
def get_intelligence(
    category: Optional[str] = Query(None, description="Filter by category key e.g. MA_WATCH"),
    tag:      Optional[str] = Query(None, description="Filter by tag"),
    days:     int           = Query(7,    description="Look-back window in days", ge=1, le=90),
    limit:    int           = Query(100,  description="Max items to return",       ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return a categorised intelligence feed."""
    if not _table_exists(db):
        # Table not yet created — return empty scaffold so the UI can still render
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total":        0,
            "days":         days,
            "by_category":  {k: [] for k in CATEGORY_ORDER},
            "items":        [],
        }

    params: dict = {"days": days, "limit": limit}
    where_clauses = ["fetched_at >= now() - (interval '1 day' * :days)"]

    if category:
        where_clauses.append("category = :category")
        params["category"] = category.upper()

    if tag:
        where_clauses.append("tag ILIKE :tag")
        params["tag"] = f"%{tag}%"

    where_sql = " AND ".join(where_clauses)

    rows = db.execute(text(f"""
        SELECT id, title, summary, source_url, source_name,
               category, tag,
               COALESCE(relevance_score, 0) AS relevance_score,
               pub_date, fetched_at
        FROM   intelligence_items
        WHERE  {where_sql}
        ORDER  BY COALESCE(relevance_score, 0) DESC, COALESCE(pub_date, fetched_at) DESC
        LIMIT  :limit
    """), params).fetchall()

    items = [_row_to_dict(r) for r in rows]

    # Group by category in specified order
    by_category: dict[str, list] = {k: [] for k in CATEGORY_ORDER}
    for item in items:
        cat = item["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total":        len(items),
        "days":         days,
        "by_category":  by_category,
        "items":        items,
    }


@router.get("/intelligence/summary")
def get_intelligence_summary(db: Session = Depends(get_db)):
    """Return per-category counts and the most recent fetch timestamp."""
    if not _table_exists(db):
        return {
            "categories": [
                {"key": k, "label": CATEGORY_LABELS[k], "count": 0, "last_fetched": None}
                for k in CATEGORY_ORDER
            ],
            "total": 0,
            "last_fetched": None,
        }

    rows = db.execute(text("""
        SELECT category,
               COUNT(*)                          AS cnt,
               MAX(fetched_at)                   AS last_fetched,
               MAX(COALESCE(pub_date, fetched_at)) AS newest_item
        FROM   intelligence_items
        WHERE  fetched_at >= now() - interval '30 days'
        GROUP  BY category
    """)).fetchall()

    counts = {r.category: {"count": r.cnt, "last_fetched": r.last_fetched, "newest_item": r.newest_item}
              for r in rows}

    categories = []
    for key in CATEGORY_ORDER:
        info = counts.get(key, {})
        categories.append({
            "key":          key,
            "label":        CATEGORY_LABELS[key],
            "count":        int(info.get("count", 0)),
            "last_fetched": info["last_fetched"].isoformat() if info.get("last_fetched") else None,
            "newest_item":  info["newest_item"].isoformat()  if info.get("newest_item")  else None,
        })

    global_last = db.execute(text("SELECT MAX(fetched_at) FROM intelligence_items")).scalar()

    return {
        "categories":   categories,
        "total":        sum(c["count"] for c in categories),
        "last_fetched": global_last.isoformat() if global_last else None,
    }


@router.get("/intelligence/daily-briefing")
def get_daily_briefing(db: Session = Depends(get_db)):
    """
    Return the latest pre-generated daily intelligence briefing.
    If none exists yet, generates one on-demand from current DB contents.
    """
    import json as _json

    # Try to read the most recent stored briefing
    try:
        row = db.execute(text("""
            SELECT summary_json, generated_at
            FROM   intelligence_summaries
            ORDER  BY summary_date DESC
            LIMIT  1
        """)).fetchone()
    except Exception:
        row = None

    if row:
        briefing = row[0] if isinstance(row[0], dict) else _json.loads(row[0])
        return briefing

    # No stored briefing — generate on-demand from whatever is in the DB
    if not _table_exists(db):
        raise HTTPException(503, "Intelligence not yet initialised. Run /refresh first.")

    total = db.execute(text("SELECT COUNT(*) FROM intelligence_items")).scalar() or 0
    if total == 0:
        raise HTTPException(404, "No intelligence items found. Run /refresh to populate.")

    try:
        from app.services.intelligence_summary import generate_daily_summary
        briefing = generate_daily_summary(db, new_count=0)
        return briefing
    except Exception as exc:
        logger.error("[intelligence] on-demand briefing error: %s", exc)
        raise HTTPException(500, str(exc))


@router.post("/intelligence/refresh")
def refresh_intelligence():
    """Trigger a fresh intelligence scrape synchronously. Returns summary of new items."""
    try:
        from app.scrapers.intelligence_scraper import run_intelligence_scraper
        result = run_intelligence_scraper()
        return {"status": "ok", **result}
    except Exception as exc:
        logger.error("[intelligence] refresh error: %s", exc)
        raise HTTPException(500, str(exc))
