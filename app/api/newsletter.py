"""
Newsletter API
==============
GET /api/newsletter/edition

Returns fresh newsletter content for the daily brief:
- Top hot leads with actionable signals
- Formatted for social sharing

Content is generated daily by generate_newsletter_edition_task (Celery).
Cached edition is served when fresh (<25h); otherwise generated on-the-fly.

Force-regeneration (refresh=true, POST /generate): when NEWSLETTER_REGEN_SECRET is set in
the environment, callers must send X-Newsletter-Regen-Key or an admin Bearer JWT.
"""
import os
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Query, Response
from sqlalchemy.orm import Session

from app.api.auth_deps import assert_newsletter_regen_allowed
from app.database import get_db
from app.services.newsletter_service import generate_edition, read_cached_edition, write_cached_edition

router = APIRouter()

def _cache_max_age_hours() -> float:
    try:
        return float(os.getenv("NEWSLETTER_CACHE_MAX_AGE_HOURS", "24.0"))
    except ValueError:
        return 24.0


@router.get("/edition")
def get_newsletter_edition(
    response: Response,
    limit: int = Query(8, description="Max top stories"),
    refresh: bool = Query(False, description="Force regeneration (bypass cache)"),
    authorization: Optional[str] = Header(None),
    x_newsletter_regen_key: Optional[str] = Header(None, alias="X-Newsletter-Regen-Key"),
    db: Session = Depends(get_db),
):
    """
    Fresh newsletter edition: hot leads with actionable signals.
    Cache TTL defaults to 1.5h (NEWSLETTER_CACHE_MAX_AGE_HOURS) so content
    does not stay frozen for a day when Celery is off. Stale cache → regenerate.
    """
    response.headers["Cache-Control"] = "public, max-age=120, stale-while-revalidate=300"
    max_age = _cache_max_age_hours()

    if refresh:
        assert_newsletter_regen_allowed(authorization, x_newsletter_regen_key)
        from app.services.industry_brief_service import build_industry_brief_payload

        build_industry_brief_payload(db, days=1, analytics=None, use_cache=True, force_refresh=True)
        data = generate_edition(db, limit=limit)
        write_cached_edition(data)
        return data

    cached = read_cached_edition(max_age_hours=max_age)
    if cached:
        if cached.get("topStories") and len(cached["topStories"]) > limit:
            cached = {**cached, "topStories": cached["topStories"][:limit]}
        return cached

    data = generate_edition(db, limit=limit)
    try:
        write_cached_edition(data)
    except OSError:
        pass
    return data


@router.post("/generate")
def trigger_newsletter_generate(
    background_tasks: BackgroundTasks,
    limit: int = Query(8, description="Max top stories"),
    authorization: Optional[str] = Header(None),
    x_newsletter_regen_key: Optional[str] = Header(None, alias="X-Newsletter-Regen-Key"),
):
    """
    Manually trigger newsletter generation and caching.
    Runs in background. Use before posting to refresh the edition.
    """
    assert_newsletter_regen_allowed(authorization, x_newsletter_regen_key)

    def _generate():
        from app.database import SessionLocal
        from app.services.industry_brief_service import build_industry_brief_payload

        db = SessionLocal()
        try:
            build_industry_brief_payload(db, days=1, analytics=None, use_cache=True, force_refresh=True)
            data = generate_edition(db, limit=limit)
            write_cached_edition(data)
        finally:
            db.close()

    background_tasks.add_task(_generate)
    return {
        "status": "generating",
        "message": "Newsletter edition generating in background. Check /api/newsletter/edition in a few seconds.",
    }
