"""
Newsletter API
==============
GET /api/newsletter/edition

Returns the daily pre-built newsletter edition (hot leads + industry brief).
Content is generated once each morning by refresh_public_surface_caches_task (Celery)
and served read-only from durable cache — never regenerated on page load.

Force-regeneration (refresh=true, POST /generate): when NEWSLETTER_REGEN_SECRET is set in
the environment, callers must send X-Newsletter-Regen-Key or an admin Bearer JWT.
"""
import logging
import os
import time
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

_log = logging.getLogger(__name__)

from app.api.auth_deps import assert_newsletter_regen_allowed
from app.database import get_db
from app.models.newsletter_subscriber import NewsletterSubscriber
from app.services.resend_email import ResendEmailError, send_email_via_resend
from app.services.newsletter_service import (
    NEWSLETTER_PIPELINE_CACHE_KEY,
    fallback_edition,
    generate_edition,
    read_cached_edition_stale,
    write_cached_edition,
)
from app.services.public_surface_cache import read_public_cache, write_public_cache
from app.services.pipeline_cache_store import cache_read_safe

router = APIRouter()

_edition_mem_cache: dict = {}


class NewsletterSubscribeIn(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    name: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=240)
    robot_category: Optional[str] = Field(None, alias="robotCategory", max_length=160)
    source: Optional[str] = Field("newsletter", max_length=120)


def _valid_email(email: str) -> bool:
    return "@" in email and "." in email.rsplit("@", 1)[-1]


def _subscribe_row(db: Session, body: NewsletterSubscribeIn) -> NewsletterSubscriber:
    email = body.email.lower().strip()
    row = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.email == email).first()
    if row is None:
        row = NewsletterSubscriber(email=email)
        db.add(row)
    row.name = body.name or row.name or None
    row.company = body.company or row.company or None
    row.robot_category = body.robot_category or row.robot_category or None
    row.source = body.source or row.source or "newsletter"
    row.status = "active"
    row.consent_text = "Requested the ReadyForRobots Robot Intelligence Brief."
    row.subscriber_metadata = {
        **(row.subscriber_metadata or {}),
        "last_source": body.source or "newsletter",
    }
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        row = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.email == email).first()
        if row is None:
            raise
        row.name = body.name or row.name or None
        row.company = body.company or row.company or None
        row.robot_category = body.robot_category or row.robot_category or None
        row.source = body.source or row.source or "newsletter"
        row.status = "active"
        db.commit()
    db.refresh(row)
    return row


def _try_send_welcome(email: str) -> dict:
    try:
        result = send_email_via_resend(
            to_email=email,
            subject="Welcome to the Robot Intelligence Brief",
            from_display_name="ReadyForRobots",
            body_text=(
                "Thanks for subscribing to the Robot Intelligence Brief.\n\n"
                "You'll get robotics buying signals, deployment stories, vendor movement, "
                "and ROI benchmarks from ReadyForRobots.\n\n"
                "Start exploring live signals here: https://readyforrobots.com/signals\n"
                "Activate SCOUT here: https://readyforrobots.com/results?url=\n"
            ),
        )
        return {"sent": True, **result}
    except ResendEmailError as exc:
        return {"sent": False, "reason": str(exc)}


def _strategic_brief_days() -> int:
    try:
        return max(1, int(os.getenv("NEWSLETTER_STRATEGIC_BRIEF_DAYS", "7")))
    except ValueError:
        return 7


def _trim_edition(data: dict, limit: int) -> dict:
    stories = data.get("topStories") or []
    if len(stories) > limit:
        return {**data, "topStories": stories[:limit]}
    return data


def hydrate_newsletter_mem_cache(data: dict) -> None:
    _edition_mem_cache["v1"] = {"ts": time.monotonic(), "data": data}


def _get_mem_cache() -> Optional[dict]:
    entry = _edition_mem_cache.get("v1")
    if entry:
        return entry["data"]
    return None


def _load_durable_edition() -> Optional[dict]:
    mem = _get_mem_cache()
    if mem:
        return mem

    cached = read_public_cache(NEWSLETTER_PIPELINE_CACHE_KEY, stale_ok=True)
    if cached:
        hydrate_newsletter_mem_cache(cached)
        return cached

    shared = cache_read_safe(NEWSLETTER_PIPELINE_CACHE_KEY, stale_ok=True, timeout_sec=3.0)
    if shared:
        hydrate_newsletter_mem_cache(shared)
        return shared

    stale_file = read_cached_edition_stale()
    if stale_file:
        hydrate_newsletter_mem_cache(stale_file)
        return stale_file

    return None


@router.get("/edition")
def get_newsletter_edition(
    response: Response,
    limit: int = Query(15, description="Max top stories"),
    refresh: bool = Query(False, description="Force regeneration (bypass cache)"),
    authorization: Optional[str] = Header(None),
    x_newsletter_regen_key: Optional[str] = Header(None, alias="X-Newsletter-Regen-Key"),
    db: Session = Depends(get_db),
):
    """
    Daily newsletter edition — read-only from pre-built cache.
    """
    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=3600"

    if refresh:
        assert_newsletter_regen_allowed(authorization, x_newsletter_regen_key)
        from app.services.industry_brief_service import build_industry_brief_payload

        build_industry_brief_payload(
            db,
            days=_strategic_brief_days(),
            analytics=None,
            use_cache=True,
            force_refresh=True,
        )
        data = generate_edition(db, limit=limit, skip_openai_brief=False)
        write_cached_edition(data, db)
        write_public_cache(db, NEWSLETTER_PIPELINE_CACHE_KEY, data)
        hydrate_newsletter_mem_cache(data)
        return _trim_edition(data, limit)

    cached = _load_durable_edition()
    if cached:
        return _trim_edition(cached, limit)

    return _trim_edition(fallback_edition(limit=limit), limit)


def _warm_newsletter_cache_at_startup() -> None:
    """Hydrate newsletter L1 from durable cache — no on-request generation."""
    def _warm() -> None:
        try:
            from app.services.public_surface_cache import hydrate_public_surface_caches

            hydrate_public_surface_caches()
            edition = _get_mem_cache()
            if edition:
                _log.info(
                    "Newsletter L1 hydrated (%d stories)",
                    len(edition.get("topStories") or []),
                )
            else:
                _log.info("Newsletter cache empty — awaiting daily refresh task")
        except Exception as exc:
            _log.warning("Newsletter cache hydrate failed: %s", exc)

    import threading

    threading.Thread(target=_warm, daemon=True, name="newsletter-cache-hydrate").start()


@router.post("/subscribe")
def subscribe_newsletter(body: NewsletterSubscribeIn, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    if not _valid_email(email):
        raise HTTPException(status_code=400, detail="Valid email is required")
    row = _subscribe_row(db, body)
    send_result = _try_send_welcome(row.email)
    return {
        "ok": True,
        "subscriber": {
            "id": row.id,
            "email": row.email,
            "status": row.status,
            "source": row.source,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
        },
        "email": send_result,
    }


@router.post("/generate")
def trigger_newsletter_generate(
    background_tasks: BackgroundTasks,
    limit: int = Query(15, description="Max top stories"),
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
        from app.services.public_surface_cache import refresh_all_public_surface_caches

        db = SessionLocal()
        try:
            refresh_all_public_surface_caches(db)
        finally:
            db.close()

    background_tasks.add_task(_generate)
    return {
        "status": "generating",
        "message": "Public surfaces rebuilding in background. Check /api/newsletter/edition shortly.",
    }
