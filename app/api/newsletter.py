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
import logging
import os
import threading
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
    read_cached_edition,
    read_cached_edition_stale,
    read_edition_from_shared_cache,
    write_cached_edition,
)
from app.services.pipeline_cache_store import cache_read_safe

router = APIRouter()

_EDITION_MEM_TTL = 120.0  # seconds
_edition_mem_cache: dict = {}
_edition_refresh_lock = threading.Lock()
_edition_refresh_in_progress = False


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


def _cache_max_age_hours() -> float:
    try:
        return float(os.getenv("NEWSLETTER_CACHE_MAX_AGE_HOURS", "18"))
    except ValueError:
        return 18


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


def _set_mem_cache(data: dict) -> None:
    _edition_mem_cache["v1"] = {"ts": time.monotonic(), "data": data}


def _get_mem_cache() -> Optional[dict]:
    entry = _edition_mem_cache.get("v1")
    if not entry:
        return None
    if time.monotonic() - entry["ts"] > _EDITION_MEM_TTL:
        return None
    return entry["data"]


def _load_any_cached_edition(db: Session, max_age_hours: float) -> Optional[dict]:
    fresh = read_cached_edition(max_age_hours=max_age_hours)
    if fresh:
        return fresh
    shared = read_edition_from_shared_cache(db, stale_ok=True)
    if shared:
        return shared
    shared_safe = cache_read_safe(NEWSLETTER_PIPELINE_CACHE_KEY, stale_ok=True, timeout_sec=5.0)
    if shared_safe:
        return shared_safe
    return read_cached_edition_stale()


def _schedule_edition_refresh(limit: int, *, full: bool) -> None:
    global _edition_refresh_in_progress
    with _edition_refresh_lock:
        if _edition_refresh_in_progress:
            return
        _edition_refresh_in_progress = True

    def _run() -> None:
        global _edition_refresh_in_progress
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            data = generate_edition(db, limit=limit, skip_openai_brief=not full)
            write_cached_edition(data, db)
            _set_mem_cache(data)
            _log.info(
                "Newsletter edition refreshed in background (%s): %d stories",
                "full" if full else "fast",
                len(data.get("topStories") or []),
            )
        except Exception as exc:
            _log.warning("Newsletter background refresh failed: %s", exc)
        finally:
            db.close()
            with _edition_refresh_lock:
                _edition_refresh_in_progress = False

    threading.Thread(
        target=_run,
        daemon=True,
        name=f"newsletter-edition-refresh-{'full' if full else 'fast'}",
    ).start()


def _build_edition_sync(limit: int) -> dict:
    """Fast synchronous build — never blocks on OpenAI."""
    from app.database import SessionLocal
    from app.db_timeout import run_db

    def _fast_build() -> dict:
        db = SessionLocal()
        try:
            data = generate_edition(db, limit=limit, skip_openai_brief=True)
            write_cached_edition(data, db)
            _set_mem_cache(data)
            return data
        finally:
            db.close()

    try:
        return run_db(_fast_build, timeout_sec=25, label="newsletter/edition-fast")
    except TimeoutError:
        _log.error("newsletter fast build timed out")
        stale = cache_read_safe(NEWSLETTER_PIPELINE_CACHE_KEY, stale_ok=True, timeout_sec=5.0)
        if stale:
            return stale
        stale_file = read_cached_edition_stale()
        if stale_file:
            return stale_file
        return fallback_edition(limit=limit)


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
    Fresh newsletter edition: hot leads with actionable signals.
    Stale-while-revalidate: never block the page on a cold OpenAI brief rebuild.
    """
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    max_age = _cache_max_age_hours()

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
        _set_mem_cache(data)
        return _trim_edition(data, limit)

    mem = _get_mem_cache()
    if mem:
        return _trim_edition(mem, limit)

    cached = read_cached_edition(max_age_hours=max_age)
    if cached:
        _set_mem_cache(cached)
        return _trim_edition(cached, limit)

    stale = _load_any_cached_edition(db, max_age)
    if stale:
        _set_mem_cache(stale)
        _schedule_edition_refresh(limit, full=True)
        return _trim_edition(stale, limit)

    data = _build_edition_sync(limit)
    _schedule_edition_refresh(limit, full=True)
    return _trim_edition(data, limit)


def _warm_newsletter_cache_at_startup() -> None:
    """
    Pre-generate a fast newsletter edition at startup so the first user request
    does not hit a cold OpenAI brief rebuild (which can exceed proxy timeouts).
    """
    max_age = _cache_max_age_hours()

    def _warm() -> None:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            cached = read_cached_edition(max_age_hours=max_age) or read_cached_edition_stale()
            if cached and cached.get("topStories") and len(cached["topStories"]) >= 8:
                _set_mem_cache(cached)
                _log.info("Newsletter cache already warm (%d stories) — skipping startup regen.", len(cached["topStories"]))
                return
            _log.info("Newsletter cache cold — building fast edition at startup…")
            data = generate_edition(db, limit=15, skip_openai_brief=True)
            write_cached_edition(data, db)
            _set_mem_cache(data)
            _log.info("Newsletter fast cache warmed at startup: %d stories.", len(data.get("topStories") or []))
            _schedule_edition_refresh(15, full=True)
        except Exception as exc:
            _log.warning("Newsletter startup warm-up failed (non-fatal): %s", exc)
        finally:
            db.close()

    threading.Thread(target=_warm, daemon=True, name="newsletter-cache-warmer").start()


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
            build_industry_brief_payload(
                db,
                days=_strategic_brief_days(),
                analytics=None,
                use_cache=True,
                force_refresh=True,
            )
            data = generate_edition(db, limit=limit, skip_openai_brief=False)
            write_cached_edition(data, db)
            _set_mem_cache(data)
        finally:
            db.close()

    background_tasks.add_task(_generate)
    return {
        "status": "generating",
        "message": "Newsletter edition generating in background. Check /api/newsletter/edition in a few seconds.",
    }
