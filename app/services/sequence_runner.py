"""Run outreach sequence enrollments — due follow-ups with pause-on-reply."""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.crm import CrmAccount
from app.models.outreach import OutreachMessage, OutreachReply
from app.models.sequences import OutreachSequence, OutreachSequenceEnrollment, OutreachSequenceStep
from app.services.resend_email import ResendEmailError, send_email_via_resend
from app.services.sales_learning_agent import record_sales_experience

logger = logging.getLogger(__name__)

DEFAULT_BUYER_SEQUENCE = {
    "name": "Buyer intro cadence",
    "slug": "buyer_intro_v1",
    "steps": [
        {
            "step_number": 1,
            "delay_days": 0,
            "subject_template": "Automation opportunity — {company_name}",
            "body_template": "Hi — Cal from Ready For Robots. We noticed automation intent at {company_name} and would love to share a relevant deployment pattern.",
            "action_label": "Intro",
        },
        {
            "step_number": 2,
            "delay_days": 3,
            "subject_template": "Following up — robotics fit for {company_name}",
            "body_template": "Quick follow-up on my note last week. Happy to share a short benchmark for peers in {industry}.",
            "action_label": "Value follow-up",
        },
        {
            "step_number": 3,
            "delay_days": 7,
            "subject_template": "Should I close the loop?",
            "body_template": "I do not want to crowd your inbox — should I close the loop, or is timing still off for {company_name}?",
            "action_label": "Breakup",
        },
    ],
}


def ensure_default_sequence(db: Session, *, team_id) -> OutreachSequence:
    row = (
        db.query(OutreachSequence)
        .filter(OutreachSequence.slug == DEFAULT_BUYER_SEQUENCE["slug"])
        .first()
    )
    if row:
        return row
    row = OutreachSequence(
        team_id=team_id,
        name=DEFAULT_BUYER_SEQUENCE["name"],
        slug=DEFAULT_BUYER_SEQUENCE["slug"],
        channel="email",
        is_default=True,
        status="active",
    )
    db.add(row)
    db.flush()
    for step in DEFAULT_BUYER_SEQUENCE["steps"]:
        db.add(
            OutreachSequenceStep(
                sequence_id=row.id,
                step_number=step["step_number"],
                delay_days=step["delay_days"],
                subject_template=step["subject_template"],
                body_template=step["body_template"],
                action_label=step["action_label"],
            )
        )
    db.flush()
    return row


def enroll_account(
    db: Session,
    *,
    team_id,
    crm_account_id,
    sequence: OutreachSequence | None = None,
) -> OutreachSequenceEnrollment:
    sequence = sequence or ensure_default_sequence(db, team_id=team_id)
    existing = (
        db.query(OutreachSequenceEnrollment)
        .filter(
            OutreachSequenceEnrollment.crm_account_id == crm_account_id,
            OutreachSequenceEnrollment.sequence_id == sequence.id,
        )
        .first()
    )
    if existing:
        return existing
    now = datetime.now(timezone.utc)
    enrollment = OutreachSequenceEnrollment(
        team_id=team_id,
        sequence_id=sequence.id,
        crm_account_id=crm_account_id,
        current_step=1,
        status="active",
        enrolled_at=now,
        next_step_at=now,
    )
    db.add(enrollment)
    db.flush()
    return enrollment


def pause_enrollment_for_reply(db: Session, *, crm_account_id) -> int:
    rows = (
        db.query(OutreachSequenceEnrollment)
        .filter(
            OutreachSequenceEnrollment.crm_account_id == crm_account_id,
            OutreachSequenceEnrollment.status == "active",
        )
        .all()
    )
    for row in rows:
        row.status = "paused"
        row.paused_reason = "reply_received"
    return len(rows)


def _render_template(template: str, account: CrmAccount) -> str:
    return (
        template.replace("{company_name}", account.name or "your team")
        .replace("{industry}", account.industry or "your industry")
    )


def _reply_address(token: str) -> str:
    import os

    domain = (os.getenv("RESEND_FROM_EMAIL") or "updates@readyforrobots.com").split("@")[-1]
    return f"scout+{token}@{domain}"


def process_due_enrollments(db: Session, *, limit: int = 50) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    due = (
        db.query(OutreachSequenceEnrollment)
        .filter(
            OutreachSequenceEnrollment.status == "active",
            OutreachSequenceEnrollment.next_step_at.isnot(None),
            OutreachSequenceEnrollment.next_step_at <= now,
        )
        .order_by(OutreachSequenceEnrollment.next_step_at.asc())
        .limit(limit)
        .all()
    )
    sent = 0
    skipped = 0
    failed = 0
    for enrollment in due:
        account = db.query(CrmAccount).filter(CrmAccount.id == enrollment.crm_account_id).first()
        if not account or not account.contact_email:
            enrollment.status = "blocked"
            enrollment.paused_reason = "missing_contact"
            skipped += 1
            continue
        replied = (
            db.query(OutreachReply.id)
            .filter(OutreachReply.crm_account_id == account.id)
            .limit(1)
            .first()
        )
        if replied:
            enrollment.status = "paused"
            enrollment.paused_reason = "reply_received"
            skipped += 1
            continue
        step = (
            db.query(OutreachSequenceStep)
            .filter(
                OutreachSequenceStep.sequence_id == enrollment.sequence_id,
                OutreachSequenceStep.step_number == enrollment.current_step,
            )
            .first()
        )
        if not step:
            enrollment.status = "completed"
            continue
        subject = _render_template(step.subject_template or f"Follow-up — {account.name}", account)
        body = _render_template(step.body_template or account.outreach_draft or "Following up from Ready For Robots.", account)
        reply_token = secrets.token_urlsafe(18)
        try:
            send_result = send_email_via_resend(
                to_email=account.contact_email,
                subject=subject,
                body_text=body,
                from_display_name="Cal",
                reply_to=_reply_address(reply_token),
                idempotency_key=f"sequence/{enrollment.id}/{enrollment.current_step}",
            )
        except ResendEmailError as exc:
            logger.warning("Sequence send failed enrollment=%s: %s", enrollment.id, exc)
            failed += 1
            continue
        msg = OutreachMessage(
            team_id=enrollment.team_id,
            crm_account_id=account.id,
            company_id=account.company_id,
            to_email=account.contact_email,
            from_email=send_result.get("from_email"),
            reply_to=_reply_address(reply_token),
            reply_token=reply_token,
            subject=subject,
            body_text=body,
            send_identity="scout",
            resend_id=send_result.get("resend_id"),
            status="sent",
            payload={"sequence_enrollment_id": str(enrollment.id), "step": enrollment.current_step},
            sent_at=now,
        )
        db.add(msg)
        account.outreach_sent_at = now
        account.outreach_stage = "sequence_step_sent"
        record_sales_experience(
            db,
            event_type="sequence_step_sent",
            outcome="sent",
            team_id=enrollment.team_id,
            crm_account_id=account.id,
            company_id=account.company_id,
            channel="email",
            payload={"step": enrollment.current_step, "sequence_id": str(enrollment.sequence_id)},
        )
        next_step = (
            db.query(OutreachSequenceStep)
            .filter(
                OutreachSequenceStep.sequence_id == enrollment.sequence_id,
                OutreachSequenceStep.step_number == enrollment.current_step + 1,
            )
            .first()
        )
        enrollment.last_step_at = now
        if next_step:
            enrollment.current_step += 1
            enrollment.next_step_at = now + timedelta(days=max(1, int(next_step.delay_days or 1)))
        else:
            enrollment.status = "completed"
            enrollment.next_step_at = None
        sent += 1
    db.commit()
    return {"processed": len(due), "sent": sent, "skipped": skipped, "failed": failed}
