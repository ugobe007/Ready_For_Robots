"""Post-signup activation email — nudge first lead save on /pipeline."""
from __future__ import annotations

import logging
import os
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


def _site_url() -> str:
    return (os.getenv("PUBLIC_SITE_URL") or "https://readyforrobots.com").rstrip("/")


def welcome_email_body(*, display_name: Optional[str] = None) -> str:
    name = (display_name or "").strip()
    greeting = f"Hi {name}," if name else "Hi there,"
    pipeline = f"{_site_url()}/pipeline"
    return f"""{greeting}

Welcome to Ready For Robots — your workspace for live robot buyer signals, HOT/WARM timing, and outreach drafts.

Your best first step: open the pipeline and save one account that looks worth pursuing today.

{pipeline}

Pick a HOT or WARM lead, save it to your workspace, and Cal will keep the context ready for outreach.

— Cal
Ready For Robots
"""


def send_welcome_activation_email(*, to_email: str, display_name: Optional[str] = None, user_id: str) -> bool:
    from app.services.resend_email import ResendEmailError, send_email_via_resend

    email = (to_email or "").strip()
    if not email or "@" not in email:
        return False
    try:
        send_email_via_resend(
            to_email=email,
            subject="Save your first lead on Ready For Robots",
            body_text=welcome_email_body(display_name=display_name),
            from_display_name="Cal · Ready For Robots",
            idempotency_key=f"welcome-activation/{user_id}",
        )
        return True
    except ResendEmailError as exc:
        logger.warning("Welcome activation email failed for %s: %s", email, exc)
        return False


def maybe_send_welcome_email(db: Session, *, user_id: str, email: str, display_name: Optional[str] = None) -> bool:
    """Send once per user when welcome_email_sent_at is unset."""
    row = db.execute(
        text("SELECT welcome_email_sent_at FROM user_profiles WHERE id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if row is None:
        return False
    if getattr(row, "welcome_email_sent_at", None):
        return False

    sent = send_welcome_activation_email(to_email=email, display_name=display_name, user_id=user_id)
    if not sent:
        return False

    db.execute(
        text("UPDATE user_profiles SET welcome_email_sent_at = now() WHERE id = :uid"),
        {"uid": user_id},
    )
    db.commit()
    return True
