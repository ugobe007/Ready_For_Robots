"""
Social Posts API
================
GET  /api/social/daily-posts         — return (or generate) today's 5 posts
POST /api/social/daily-posts/refresh — force regenerate (X-Admin-Key required)
"""
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.social_posts_service import (
    generate_daily_posts,
    read_cached_posts,
    write_cached_posts,
)

router = APIRouter()

_CACHE_MAX_AGE_HOURS = 4.0


def _check_admin_key(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")) -> None:
    key = os.getenv("ADMIN_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="ADMIN_KEY not configured")
    if x_admin_key != key:
        raise HTTPException(status_code=401, detail="Invalid X-Admin-Key")


@router.get("/daily-posts")
def get_daily_posts(
    response: Response,
    refresh: bool = False,
    db: Session = Depends(get_db),
):
    """
    Returns today's 5 ready-to-post social media items.
    Each post includes `twitter` and `linkedin` text variants plus hashtags.
    Cached for 4 hours; pass ?refresh=true with X-Admin-Key to force regeneration.
    """
    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=600"

    if not refresh:
        cached = read_cached_posts(max_age_hours=_CACHE_MAX_AGE_HOURS)
        if cached:
            return cached

    data = generate_daily_posts(db)
    write_cached_posts(data)
    return data


@router.post("/daily-posts/refresh")
def refresh_daily_posts(
    db: Session = Depends(get_db),
    _: None = Depends(_check_admin_key),
):
    """Force-regenerate today's social posts. Requires X-Admin-Key header."""
    data = generate_daily_posts(db)
    write_cached_posts(data)
    return data
