"""Shared Cal buyer intro send — Resend + OutreachMessage reply token for webhook loop."""
from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.crm import CrmAccount
from app.models.company import Company
from app.models.outreach import OutreachMessage
from app.services.resend_email import ResendEmailError
from app.services.cal_email_send import send_cal_email_via_resend

logger = logging.getLogger(__name__)


def cal_reply_domain() -> str:
    raw = (
        os.getenv("SCOUT_REPLY_DOMAIN")
        or os.getenv("RESEND_REPLY_DOMAIN")
        or os.getenv("RESEND_FROM_EMAIL")
        or "readyforrobots.com"
    ).strip()
    if "<" in raw and ">" in raw:
        raw = raw.split("<", 1)[1].split(">", 1)[0]
    raw = raw.replace("mailto:", "").strip().strip("<>")
    if "://" in raw:
        raw = urlparse(raw).netloc or raw
    if "@" in raw:
        raw = raw.rsplit("@", 1)[1]
    raw = raw.strip().strip("/").lower()
    if not raw or " " in raw or "@" in raw:
        return "readyforrobots.com"
    return raw


def cal_reply_address(reply_token: str) -> str:
    local = (os.getenv("SCOUT_REPLY_LOCAL_PART") or "reply").strip().split("@", 1)[0] or "reply"
    return f"{local}+{reply_token}@{cal_reply_domain()}"


def parse_cal_draft(draft: str | None, fallback_name: str) -> tuple[str, str]:
    draft_lines = (draft or "").strip().splitlines()
    subject_line = next((line for line in draft_lines if line.strip()), None)
    if subject_line and subject_line.lower().startswith("subject:"):
        subject = subject_line[8:].strip()
        body_text = "\n".join(draft_lines[1:]).strip()
    else:
        subject = f"Robot automation partnership — {fallback_name}"
        body_text = draft or ""
    return subject, body_text


def send_cal_intro_email(
    db: Session,
    *,
    acct: CrmAccount,
    company: Company | None,
    team_id,
    to_email: str,
    subject: str,
    body_text: str,
    cc: list[str] | None = None,
    sender_user_id=None,
    idempotency_key: str,
    send_identity: str = "cal",
    include_demo: bool = True,
    variant_id: str | None = None,
    canary: bool = False,
) -> OutreachMessage:
    """Send intro email with reply routing and persist OutreachMessage for inbound webhook.

    `variant_id` records which trust-first angle produced this send so the weekly
    learning report can attribute replies back to a specific angle.
    """
    reply_token = secrets.token_urlsafe(18)
    reply_to = cal_reply_address(reply_token)
    inbound_missing = False

    try:
        send_result = send_cal_email_via_resend(
            to_email=to_email,
            subject=subject,
            body_text=body_text,
            from_display_name="Cal · Ready For Robots",
            reply_to=reply_to,
            cc=cc,
            idempotency_key=idempotency_key,
            include_demo=include_demo,
        )
    except ResendEmailError as exc:
        err_text = str(exc).lower()
        if any(kw in err_text for kw in ("notification service", "notification_service", "inbound", "not set", "not configured")):
            inbound_missing = True
            send_result = send_cal_email_via_resend(
                to_email=to_email,
                subject=subject,
                body_text=body_text,
                from_display_name="Cal · Ready For Robots",
                reply_to=None,
                cc=cc,
                idempotency_key=f"{idempotency_key}/no-inbound",
                include_demo=include_demo,
            )
        else:
            raise

    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "channel": "cal_buyer",
        "inbound_routing": not inbound_missing,
        "email_demo": include_demo,
    }
    if variant_id:
        payload["variant_id"] = variant_id
    if canary:
        # Tag deliverability-canary sends so the breaker can grade them in isolation.
        payload["canary"] = "true"
    msg = OutreachMessage(
        team_id=team_id,
        crm_account_id=acct.id,
        company_id=acct.company_id or (company.id if company else None),
        sender_user_id=sender_user_id,
        to_email=to_email,
        from_email=send_result.get("from_email"),
        reply_to=reply_to if not inbound_missing else None,
        reply_token=reply_token,
        subject=subject,
        body_text=body_text,
        send_identity=send_identity,
        resend_id=send_result.get("resend_id"),
        status="sent",
        sent_at=now,
        payload=payload,
    )
    db.add(msg)
    acct.outreach_sent_at = now
    acct.outreach_stage = "contacted"
    db.flush()
    return msg


def enroll_cal_followup(db: Session, *, team_id, crm_account_id, variant_id: str | None = None) -> None:
    try:
        from app.services.sequence_runner import enroll_after_intro_send

        enroll_after_intro_send(
            db, team_id=team_id, crm_account_id=crm_account_id, variant_id=variant_id
        )
    except Exception as exc:
        logger.warning("Cal follow-up enroll failed account=%s: %s", crm_account_id, exc)
