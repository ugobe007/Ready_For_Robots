"""
Social Posts API
================
GET  /api/social/daily-posts                 — return (or generate) today's 5 posts
POST /api/social/daily-posts/refresh         — generate a fresh batch skipping already-posted leads
POST /api/social/daily-posts/mark-posted     — record that a batch was posted (updates history)
"""
from datetime import datetime, timezone
from typing import List, Optional

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.social_posts_service import (
    generate_daily_posts,
    read_cached_posts,
    refresh_social_posts_cache,
    write_cached_posts,
    mark_companies_posted,
    get_recently_posted_ids,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _background_refresh_social_posts() -> None:
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        refresh_social_posts_cache(db)
    except Exception as exc:
        logger.warning("background social posts refresh failed: %s", exc)
    finally:
        db.close()

_CACHE_MAX_AGE_HOURS = 4.0


class RefreshPayload(BaseModel):
    exclude_ids: Optional[List[int]] = None    # company IDs to skip this batch
    trend_offset: int = 0                       # rotate which macro trend is used


class MarkPostedPayload(BaseModel):
    company_ids: List[int]
    post_types: Optional[List[str]] = None


@router.get("/daily-posts")
def get_daily_posts(
    response: Response,
    background_tasks: BackgroundTasks,
):
    """
    Returns today's 5 ready-to-post social media items (cached up to 4h).
    Each post includes `twitter` and `linkedin` text + `company_id` for tracking.
    Read-only — no DB session on the request path.
    """
    response.headers["Cache-Control"] = "public, max-age=120, stale-while-revalidate=300"

    cached = read_cached_posts(max_age_hours=_CACHE_MAX_AGE_HOURS)
    if cached and (cached.get("posts") or []):
        return cached

    stale = read_cached_posts(max_age_hours=None)
    if stale and (stale.get("posts") or []):
        response.headers["X-Social-Cache"] = "stale"
        background_tasks.add_task(_background_refresh_social_posts)
        return {**stale, "cache_status": "stale"}

    background_tasks.add_task(_background_refresh_social_posts)
    return {
        "date": datetime.now(timezone.utc).strftime("%B %d, %Y"),
        "posts": [],
        "cache_pending": True,
        "message": "Daily posts are being generated in the background. Retry in 1–2 minutes.",
    }


@router.post("/daily-posts/refresh")
def refresh_daily_posts(
    payload: RefreshPayload = RefreshPayload(),
    db: Session = Depends(get_db),
):
    """
    Generate a fresh batch of 5 posts.
    Automatically skips companies in the 7-day posted history.
    Pass exclude_ids to additionally skip specific company IDs (e.g. today's current batch).
    trend_offset rotates which macro trend is featured (0, 1, 2 …).
    No admin key required — it's just content generation.
    """
    data = generate_daily_posts(
        db,
        exclude_ids=payload.exclude_ids or [],
        trend_offset=payload.trend_offset,
    )
    write_cached_posts(data, db=db)
    return data


@router.post("/daily-posts/mark-posted")
def mark_posted(payload: MarkPostedPayload):
    """
    Record that these company IDs have been posted.
    Call this after sharing a batch so the next refresh skips them for 7 days.
    """
    if not payload.company_ids:
        return {"recorded": 0}
    mark_companies_posted(payload.company_ids, payload.post_types)
    return {
        "recorded": len(payload.company_ids),
        "recently_posted_count": len(get_recently_posted_ids(days=7)),
    }
