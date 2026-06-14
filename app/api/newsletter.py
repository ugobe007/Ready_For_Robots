"""
Newsletter API
==============
GET /api/newsletter/edition

Serves a pre-built daily snapshot from durable cache + in-process L1.
The morning publish job (6:00 America/Los_Angeles) rebuilds the edition once;
GET never runs DB generation or OpenAI on the request path.
"""
import logging
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
)
from app.services.newsletter_service import write_cached_edition
from app.services.newsletter_snapshot import (
    hydrate_newsletter_mem_cache,
    get_newsletter_mem_cache,
    publish_api_snapshot,
    serve_api_snapshot,
    slim_edition_for_api,
)

router = APIRouter()


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
                "Activate SIGNAL here: https://readyforrobots.com/results?url=\n"
            ),
        )
        return {"sent": True, **result}
    except ResendEmailError as exc:
        return {"sent": False, "reason": str(exc)}


def _install_seed_if_empty() -> None:
    if get_newsletter_mem_cache():
        return
    seed = load_seed_edition()
    if seed:
        hydrate_newsletter_mem_cache(slim_edition_for_api(seed, limit=15))
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
    """Daily newsletter — instant from pre-built snapshot; never rebuilds on page load."""
    response.headers["Cache-Control"] = "public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800"

    if refresh:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            assert_newsletter_regen_allowed(authorization, x_newsletter_regen_key)
            data = build_daily_newsletter_edition(db, limit=limit, force=True, skip_openai_brief=False)
            write_cached_edition(data, db)
            return publish_api_snapshot(db, data, limit=limit)
        finally:
            db.close()

    return serve_api_snapshot(limit=limit)


def _warm_newsletter_cache_at_startup() -> None:
    """Hydrate newsletter L1 from API snapshot + durable cache."""
    def _warm() -> None:
        try:
            _install_seed_if_empty()
            from app.services.public_surface_cache import hydrate_public_surface_caches

            hydrate_public_surface_caches()
            edition = get_newsletter_mem_cache()
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
