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
    "name": "Cal buyer cadence",
    "slug": "cal_buyer_v1",
    # Cal's voice: smooth, smart, lightly self-aware. Each touch adds a NEW idea
    # (not "just bumping this"), keeps it short/mobile-friendly, and makes the ask
    # a low-friction yes/no. Templates support {company_name} and {industry}.
    "steps": [
        {
            "step_number": 1,
            "delay_days": 0,
            "subject_template": "A robot that earns its spot — {company_name}",
            "body_template": (
                "Hi — I'm Cal with Ready For Robots.\n\n"
                "I help teams in {industry} find the spots where a robot actually pays for "
                "itself — and, just as usefully, the spots where it doesn't. No hype, no "
                "\"robots will change everything\" keynote.\n\n"
                "Worth a quick look at what's working for operators like {company_name}?\n\n"
                "— Cal\nReady For Robots"
            ),
            "action_label": "Intro",
        },
        {
            "step_number": 2,
            "delay_days": 3,
            "subject_template": "Following up (politely) — {company_name}",
            "body_template": (
                "Hi again — Cal here.\n\n"
                "I know \"just circling back\" is the junk food of your inbox, so I'll make this "
                "worth the click: the teams getting real ROI in {industry} aren't the ones buying "
                "the flashiest robot — they're the ones who pick one painful, repetitive task and "
                "let a robot own it end to end.\n\n"
                "I can send over the 2–3 tasks that tend to pay off first for a team like "
                "{company_name}. Want them?\n\n"
                "— Cal\nReady For Robots"
            ),
            "action_label": "Value follow-up",
        },
        {
            "step_number": 3,
            "delay_days": 6,
            "subject_template": "The part everyone gets wrong about robot pilots — {company_name}",
            "body_template": (
                "Hi — Cal again.\n\n"
                "Most robot pilots stall for the same unglamorous reason: nobody agreed up front on "
                "what \"it worked\" means. The operators who win pick one workflow, one number to "
                "move, and a 30-day window — then decide with data instead of vibes.\n\n"
                "I can map that out for {company_name} in about 20 minutes. A plain \"yes\" or "
                "\"not now\" is a perfectly good reply.\n\n"
                "— Cal\nReady For Robots"
            ),
            "action_label": "Proof / easy ask",
        },
        {
            "step_number": 4,
            "delay_days": 9,
            "subject_template": "I'll stop emailing (promise) — {company_name}",
            "body_template": (
                "Hi — Cal, one last time.\n\n"
                "I don't want to be the guy who keeps knocking after the lights are off, so I'll "
                "leave it here. If robots-that-earn-their-keep aren't on the {company_name} roadmap "
                "this quarter, no hard feelings.\n\n"
                "If timing changes — a new site, a labor crunch, a task nobody wants to staff — just "
                "reply \"Cal?\" and I'll pick up right where we left off.\n\n"
                "— Cal\nReady For Robots"
            ),
            "action_label": "Graceful breakup",
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


def sync_default_sequence_steps(db: Session) -> dict[str, int]:
    """Upsert DEFAULT_BUYER_SEQUENCE step copy onto the live sequence.

    ``ensure_default_sequence`` only seeds steps when the sequence is first
    created, so editing the templates in code does NOT reach the accounts already
    enrolled. Call this to push new subject/body/delay copy to the existing
    ``cal_buyer_v1`` steps (and add any new steps, e.g. a 4th touch) so in-flight
    follow-ups send the current voice.
    """
    seq = (
        db.query(OutreachSequence)
        .filter(OutreachSequence.slug == DEFAULT_BUYER_SEQUENCE["slug"])
        .first()
    )
    if not seq:
        return {"updated": 0, "added": 0, "sequence": 0}
    updated = added = 0
    for step in DEFAULT_BUYER_SEQUENCE["steps"]:
        row = (
            db.query(OutreachSequenceStep)
            .filter(
                OutreachSequenceStep.sequence_id == seq.id,
                OutreachSequenceStep.step_number == step["step_number"],
            )
            .first()
        )
        if row:
            row.subject_template = step["subject_template"]
            row.body_template = step["body_template"]
            row.delay_days = step["delay_days"]
            row.action_label = step["action_label"]
            updated += 1
        else:
            db.add(
                OutreachSequenceStep(
                    sequence_id=seq.id,
                    step_number=step["step_number"],
                    delay_days=step["delay_days"],
                    subject_template=step["subject_template"],
                    body_template=step["body_template"],
                    action_label=step["action_label"],
                )
            )
            added += 1
    db.commit()
    return {"updated": updated, "added": added, "sequence": 1}


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


def enroll_after_intro_send(
    db: Session,
    *,
    team_id,
    crm_account_id,
    sequence: OutreachSequence | None = None,
    variant_id: str | None = None,
) -> OutreachSequenceEnrollment:
    """Enroll after Cal's intro email — schedule step 2 follow-up.

    The intro's trust-first `variant_id` is stored on the enrollment so every
    follow-up in the cadence is attributed to the same angle in reporting.
    """
    sequence = sequence or ensure_default_sequence(db, team_id=team_id)
    now = datetime.now(timezone.utc)
    existing = (
        db.query(OutreachSequenceEnrollment)
        .filter(
            OutreachSequenceEnrollment.crm_account_id == crm_account_id,
            OutreachSequenceEnrollment.sequence_id == sequence.id,
        )
        .first()
    )
    step2 = (
        db.query(OutreachSequenceStep)
        .filter(
            OutreachSequenceStep.sequence_id == sequence.id,
            OutreachSequenceStep.step_number == 2,
        )
        .first()
    )
    delay_days = max(1, int(step2.delay_days if step2 else 3))
    if existing:
        if existing.status in ("paused", "completed", "blocked"):
            existing.status = "active"
            existing.paused_reason = None
        existing.current_step = 2
        existing.next_step_at = now + timedelta(days=delay_days)
        if variant_id:
            meta = dict(existing.payload or {})
            meta["variant_id"] = variant_id
            existing.payload = meta
        db.flush()
        return existing
    enrollment = OutreachSequenceEnrollment(
        team_id=team_id,
        sequence_id=sequence.id,
        crm_account_id=crm_account_id,
        current_step=2,
        status="active",
        enrolled_at=now,
        next_step_at=now + timedelta(days=delay_days),
        payload={"variant_id": variant_id} if variant_id else {},
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


def block_enrollment_for_reply(db: Session, *, crm_account_id, reason: str = "opt_out") -> int:
    """Hard-stop the cadence for opt-outs / not-a-fit.

    Completes any non-terminal enrollment so no further follow-up can fire. Unlike
    :func:`pause_enrollment_for_reply` (a soft pause that a re-enroll can reopen),
    this terminates the enrollment and records why.
    """
    rows = (
        db.query(OutreachSequenceEnrollment)
        .filter(
            OutreachSequenceEnrollment.crm_account_id == crm_account_id,
            OutreachSequenceEnrollment.status.in_(("active", "paused")),
        )
        .all()
    )
    for row in rows:
        row.status = "completed"
        row.paused_reason = f"opt_out:{reason}"
        row.next_step_at = None
    return len(rows)


_JUNK_INDUSTRIES = {"", "unknown", "other", "none", "n/a", "general robotics", "general"}


def _clean_industry(industry: str | None) -> str:
    """A phrase that reads naturally in 'teams in {industry}' — never a broken
    'your industry teams' or a meaningless 'Unknown'."""
    val = (industry or "").strip()
    if val.lower() in _JUNK_INDUSTRIES:
        return "your industry"
    return val


def _render_template(template: str, account: CrmAccount) -> str:
    return (
        template.replace("{company_name}", account.name or "your team")
        .replace("{industry}", _clean_industry(account.industry))
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
            payload={
                "sequence_enrollment_id": str(enrollment.id),
                "step": enrollment.current_step,
                **(
                    {"variant_id": (enrollment.payload or {}).get("variant_id")}
                    if (enrollment.payload or {}).get("variant_id")
                    else {}
                ),
            },
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
