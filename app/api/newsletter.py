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

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth_deps import assert_newsletter_regen_allowed
from app.database import get_db
from app.models.newsletter_subscriber import NewsletterSubscriber
from app.services.resend_email import ResendEmailError, send_email_via_resend
from app.services.newsletter_service import generate_edition, read_cached_edition, write_cached_edition

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
                "Activate SCOUT here: https://readyforrobots.com/results?url=\n"
            ),
        )
        return {"sent": True, **result}
    except ResendEmailError as exc:
        return {"sent": False, "reason": str(exc)}

def _cache_max_age_hours() -> float:
    try:
        return float(os.getenv("NEWSLETTER_CACHE_MAX_AGE_HOURS", "1.5"))
    except ValueError:
        return 1.5


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
