"""
Newsletter API
==============
GET /api/newsletter/edition

Serves the daily pre-built newsletter from durable cache + library archive.
The bundled seed library guarantees instant story content on cold deploy; the
morning agent (6:15 UTC) refreshes when lead/signal fingerprints change.
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
from app.services.newsletter_library import (
    build_daily_newsletter_edition,
    load_seed_edition,
    resolve_edition_for_serving,
)
from app.services.newsletter_service import (
    NEWSLETTER_PIPELINE_CACHE_KEY,
    write_cached_edition,
)
from app.services.public_surface_cache import read_public_cache, write_public_cache

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


_STORY_API_KEYS = frozenset({
    "category", "company", "headline", "snippet", "summary", "roi", "economics",
    "impact", "signalStrength", "company_id", "tier", "industry",
})


def _slim_story(story: dict) -> dict:
    """Drop heavy newsletter fields (fullText HTML, duplicate blobs) from API responses."""
    if not isinstance(story, dict):
        return story
    slim = {k: v for k, v in story.items() if k in _STORY_API_KEYS}
    for text_key in ("summary", "snippet", "headline"):
        val = slim.get(text_key)
        if isinstance(val, str) and len(val) > 1200:
            slim[text_key] = val[:1199].rstrip() + "…"
    full = story.get("fullText")
    if isinstance(full, str) and full.strip() and "summary" not in slim:
        slim["summary"] = full[:1200].rstrip() + ("…" if len(full) > 1200 else "")
    return slim


def _slim_edition_for_api(data: dict, *, limit: int) -> dict:
    trimmed = _trim_edition(data, limit)
    stories = [_slim_story(s) for s in (trimmed.get("topStories") or [])]
    out = {**trimmed, "topStories": stories}
    findings = trimmed.get("researchFindings") or []
    if isinstance(findings, list) and len(findings) > 8:
        out["researchFindings"] = findings[:8]
    brief = trimmed.get("industryBrief")
    if isinstance(brief, dict):
        out["industryBrief"] = {
            k: (v[:6] if isinstance(v, list) else v)
            for k, v in brief.items()
            if k in ("executive_take", "macro_trends", "strategic_implications", "risks_and_unknowns", "watch_next")
        }
    return out


def hydrate_newsletter_mem_cache(data: dict) -> None:
    if not (data.get("topStories") or []):
        return
    _edition_mem_cache["v1"] = {"ts": time.monotonic(), "data": data}


def _get_mem_cache() -> Optional[dict]:
    entry = _edition_mem_cache.get("v1")
    if entry:
        return entry["data"]
    return None


def _install_seed_if_empty() -> None:
    if _get_mem_cache():
        return
    seed = load_seed_edition()
    if seed:
        hydrate_newsletter_mem_cache(seed)
        _log.info("Newsletter seed library loaded into L1 (%d stories)", len(seed.get("topStories") or []))


_install_seed_if_empty()


@router.get("/edition")
def get_newsletter_edition(
    response: Response,
    limit: int = Query(15, description="Max top stories"),
    refresh: bool = Query(False, description="Force regeneration (bypass cache)"),
    authorization: Optional[str] = Header(None),
    x_newsletter_regen_key: Optional[str] = Header(None, alias="X-Newsletter-Regen-Key"),
):
    """Daily newsletter — instant from library; never empty when archive exists."""
    from app.services.public_surface_cache import maybe_schedule_public_cache_refresh

    response.headers["Cache-Control"] = "public, max-age=120, stale-while-revalidate=7200"
    maybe_schedule_public_cache_refresh()

    if refresh:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            assert_newsletter_regen_allowed(authorization, x_newsletter_regen_key)
            data = build_daily_newsletter_edition(db, limit=limit, force=True, skip_openai_brief=False)
            write_cached_edition(data, db)
            write_public_cache(db, NEWSLETTER_PIPELINE_CACHE_KEY, data)
            hydrate_newsletter_mem_cache(data)
            return _slim_edition_for_api(data, limit=limit)
        finally:
            db.close()

    mem = _get_mem_cache()
    if mem and len(mem.get("topStories") or []) >= 1:
        return _slim_edition_for_api(mem, limit=limit)

    edition = resolve_edition_for_serving(None, limit=limit)
    if len(edition.get("topStories") or []) >= 1:
        hydrate_newsletter_mem_cache(edition)
    return _slim_edition_for_api(edition, limit=limit)


def _warm_newsletter_cache_at_startup() -> None:
    """Hydrate newsletter L1 from library + durable cache."""
    def _warm() -> None:
        try:
            _install_seed_if_empty()
            from app.services.public_surface_cache import hydrate_public_surface_caches

            hydrate_public_surface_caches()
            edition = _get_mem_cache()
            if edition:
                _log.info(
                    "Newsletter L1 ready (%d stories, served_from=%s)",
                    len(edition.get("topStories") or []),
                    (edition.get("_meta") or {}).get("served_from", "mem"),
                )
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
    """Manually trigger full public-surface rebuild (admin)."""
    assert_newsletter_regen_allowed(authorization, x_newsletter_regen_key)

    def _generate():
        from app.database import SessionLocal
        from app.services.public_surface_cache import (
            hydrate_public_surface_caches,
            refresh_all_public_surface_caches,
        )

        db = SessionLocal()
        try:
            refresh_all_public_surface_caches(db)
            hydrate_public_surface_caches()
        finally:
            db.close()

    background_tasks.add_task(_generate)
    return {
        "status": "generating",
        "message": "Public surfaces rebuilding in background. Check /api/newsletter/edition shortly.",
    }
