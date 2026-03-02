"""
Intelligence Daily Summary Service
===================================
Generates a structured daily briefing from intelligence_items.
No LLM required — purely extractive (top items ranked by relevance_score).

Called automatically at the end of run_intelligence_scraper() and also
on-demand via GET /api/intelligence/daily-briefing.
"""

import json
import logging
from collections import Counter
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text

logger = logging.getLogger(__name__)

CATEGORY_ORDER = ["MA_WATCH", "HUMANOID", "COMPETITOR", "MARKET", "INDUSTRY", "PARTNER", "FOUNDATION"]

CATEGORY_LABELS = {
    "MA_WATCH":   "M&A Watch",
    "HUMANOID":   "Humanoid Market",
    "COMPETITOR": "Competitor Landscape",
    "MARKET":     "Market Signals",
    "INDUSTRY":   "Industry Trends",
    "PARTNER":    "Partner & Tech Ecosystem",
    "FOUNDATION": "VLA & Foundation Models",
}

_SUMMARIES_DDL = """
CREATE TABLE IF NOT EXISTS intelligence_summaries (
    id            SERIAL       PRIMARY KEY,
    summary_date  DATE         UNIQUE NOT NULL,
    summary_json  JSONB        NOT NULL,
    generated_at  TIMESTAMPTZ  DEFAULT now()
)
"""


def _ensure_summaries_table(db) -> None:
    """Idempotent table creation for intelligence_summaries."""
    try:
        db.execute(text(_SUMMARIES_DDL))
        db.commit()
    except Exception as exc:
        logger.warning("[summary] DDL skipped: %s", exc)
        try:
            db.rollback()
        except Exception:
            pass


def _row_to_item(r) -> dict:
    """Convert a SQLAlchemy row (tuple) to a plain dict."""
    def _iso(v):
        if v is None:
            return None
        return v.isoformat() if hasattr(v, "isoformat") else str(v)

    return {
        "id":              r[0],
        "title":           r[1],
        "summary":         r[2],
        "source_url":      r[3],
        "source_name":     r[4],
        "category":        r[5],
        "tag":             r[6],
        "relevance_score": int(r[7] or 0),
        "pub_date":        _iso(r[8]),
        "fetched_at":      _iso(r[9]),
    }


def generate_daily_summary(db, new_count: int = 0) -> dict:
    """
    Build a daily intelligence briefing from items fetched in the last 7 days.

    Args:
        db:        SQLAlchemy session (any Session or connection with .execute()).
        new_count: Number of new items inserted in this scrape run (passed in
                   from run_intelligence_scraper so it appears in the summary).

    Returns:
        The summary dict (also upserted into intelligence_summaries).
    """
    _ensure_summaries_table(db)

    # ── Fetch recent items (last 7 days, ordered by relevance then recency) ──
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    try:
        rows = db.execute(text("""
            SELECT id, title, summary, source_url, source_name,
                   category, tag, relevance_score, pub_date, fetched_at
            FROM   intelligence_items
            WHERE  fetched_at >= :cutoff
            ORDER  BY relevance_score DESC, fetched_at DESC
            LIMIT  500
        """), {"cutoff": cutoff}).fetchall()
    except Exception as exc:
        logger.error("[summary] query error: %s", exc)
        return {}

    if not rows:
        # Fallback: if nothing in the last 7 days, use all-time top items
        try:
            rows = db.execute(text("""
                SELECT id, title, summary, source_url, source_name,
                       category, tag, relevance_score, pub_date, fetched_at
                FROM   intelligence_items
                ORDER  BY relevance_score DESC, fetched_at DESC
                LIMIT  200
            """)).fetchall()
        except Exception as exc:
            logger.error("[summary] fallback query error: %s", exc)
            return {}

    items = [_row_to_item(r) for r in rows]

    # ── Spotlight: top 15 items across all categories ─────────────────────
    spotlight = [
        {
            "title":           it["title"],
            "category":        it["category"],
            "category_label":  CATEGORY_LABELS.get(it["category"], it["category"]),
            "tag":             it["tag"],
            "source_url":      it["source_url"],
            "source_name":     it["source_name"],
            "relevance_score": it["relevance_score"],
            "pub_date":        it["pub_date"],
        }
        for it in items[:15]
    ]

    # ── By category: count + top item per category ────────────────────────
    buckets: dict[str, list] = {cat: [] for cat in CATEGORY_ORDER}
    for it in items:
        cat = it["category"]
        if cat in buckets:
            buckets[cat].append(it)

    by_category: dict = {}
    for cat in CATEGORY_ORDER:
        cat_items = buckets[cat]
        top = None
        if cat_items:
            t = cat_items[0]
            top = {
                "title":           t["title"],
                "tag":             t["tag"],
                "source_url":      t["source_url"],
                "source_name":     t["source_name"],
                "relevance_score": t["relevance_score"],
                "pub_date":        t["pub_date"],
            }
        by_category[cat] = {
            "count": len(cat_items),
            "label": CATEGORY_LABELS.get(cat, cat),
            "top":   top,
        }

    # ── Trending tags: most frequent tags across the window ───────────────
    tag_counts = Counter(it["tag"] for it in items if it["tag"])
    trending_tags = [tag for tag, _ in tag_counts.most_common(10)]

    # ── Assemble final summary dict ───────────────────────────────────────
    today = date.today().isoformat()
    now   = datetime.now(timezone.utc).isoformat()
    summary = {
        "date":          today,
        "generated_at":  now,
        "total_items":   len(items),
        "new_today":     new_count,
        "spotlight":     spotlight,
        "by_category":   by_category,
        "trending_tags": trending_tags,
    }

    # ── Upsert into intelligence_summaries ────────────────────────────────
    try:
        db.execute(text("""
            INSERT INTO intelligence_summaries (summary_date, summary_json, generated_at)
            VALUES (:d, :j::jsonb, now())
            ON CONFLICT (summary_date) DO UPDATE
                SET summary_json = EXCLUDED.summary_json,
                    generated_at = EXCLUDED.generated_at
        """), {"d": today, "j": json.dumps(summary)})
        db.commit()
        logger.info(
            "[summary] generated for %s — %d items, %d spotlight, %d categories",
            today, len(items), len(spotlight), len([c for c in by_category if by_category[c]["count"] > 0])
        )
    except Exception as exc:
        logger.error("[summary] upsert error: %s", exc)
        try:
            db.rollback()
        except Exception:
            pass

    return summary
