"""
Social Posts API
================
GET  /api/social/daily-posts                 — return (or generate) today's 5 posts
POST /api/social/daily-posts/refresh         — generate a fresh batch skipping already-posted leads
POST /api/social/daily-posts/mark-posted     — record that a batch was posted (updates history)
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.social_posts_service import (
    generate_daily_posts,
    read_cached_posts,
    write_cached_posts,
    mark_companies_posted,
    get_recently_posted_ids,
)

router = APIRouter()

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
    db: Session = Depends(get_db),
):
    """
    Returns today's 5 ready-to-post social media items (cached up to 4h).
    Each post includes `twitter` and `linkedin` text + `company_id` for tracking.
    """
    response.headers["Cache-Control"] = "public, max-age=120, stale-while-revalidate=300"

    cached = read_cached_posts(max_age_hours=_CACHE_MAX_AGE_HOURS)
    if cached:
        return cached

    data = generate_daily_posts(db)
    write_cached_posts(data)
    return data


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
    write_cached_posts(data)
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
