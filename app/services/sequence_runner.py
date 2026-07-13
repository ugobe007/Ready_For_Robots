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
from app.services.lead_enrichment import address_previously_bounced, verify_email_deliverable
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
            # Teach — one deployment lesson. Live copy comes from the ladder
            # builders (per-industry); this static template is a fallback only.
            "step_number": 2,
            "delay_days": 6,
            "subject_template": "the workflow most teams automate last — {company_name}",
            "body_template": (
                "Hi,\n\n"
                "One pattern I see everywhere: the projects with the fastest payback rarely start "
                "with the most visible task. They start with the quiet process upstream that backs "
                "everything else up.\n\n"
                "Most teams automate the flashy part first, then wonder why the ROI never showed. If "
                "{company_name} ever maps this out, that's where I'd start.\n\n"
                "— Cal\nReady For Robots"
            ),
            "action_label": "Teach",
        },
        {
            # Trend — one market pattern / common mistake. Live copy = ladder.
            "step_number": 3,
            "delay_days": 14,
            "subject_template": "why \"evaluating five robots\" is usually the wrong question — {company_name}",
            "body_template": (
                "Hi,\n\n"
                "A team lines up five vendors, runs a bake-off, picks the fastest — and six months "
                "later it's parked. The robots that survive aren't the fastest; they're matched to "
                "one specific bottleneck, with integration and software actually resourced.\n\n"
                "If {company_name} is weighing vendors, I'm glad to share what separates the ones "
                "that last. No pitch.\n\n"
                "— Cal\nReady For Robots"
            ),
            "action_label": "Trend",
        },
        {
            # Question — one easy, genuine question. Live copy = ladder.
            "step_number": 4,
            "delay_days": 24,
            "subject_template": "one question about {company_name}",
            "body_template": (
                "Hi,\n\n"
                "No agenda here — one question tells me more than a whole discovery call.\n\n"
                "If you automated one workflow tomorrow, which would it be? Most teams name the "
                "busiest one. The one that actually pays back is usually the process quietly "
                "creating work everywhere else. Curious what you'd pick for {company_name}.\n\n"
                "— Cal\nReady For Robots"
            ),
            "action_label": "Question",
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
    delay_days = max(1, int(step2.delay_days if step2 else 6))
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


# Cal's buyer cadence follow-ups (steps 2/3/4) teach in the advisor voice rather
# than sending static "value / proof / breakup" copy. Map each step to a ladder
# touch by action_label first, then step number as a fallback.
_LADDER_STEP_TOUCH = {2: "teach", 3: "trend", 4: "question"}


def _step_touch(step: OutreachSequenceStep) -> str | None:
    label = (getattr(step, "action_label", "") or "").strip().lower()
    if label in ("teach", "trend", "question"):
        return label
    return _LADDER_STEP_TOUCH.get(getattr(step, "step_number", 0))


def _render_sequence_step(
    step: OutreachSequenceStep,
    account: CrmAccount,
    *,
    sequence_slug: str | None,
) -> tuple[str, str]:
    """Produce (subject, body) for a due follow-up.

    For Cal's buyer cadence (``cal_buyer_v1``), steps 2/3/4 are rendered by the
    ``agent_messaging`` ladder builders so each touch teaches one industry-specific
    thing in the advisor voice. Any other sequence — or a step without a ladder
    touch (e.g. the CRM manual step 1) — falls back to the static template.
    """
    if sequence_slug == DEFAULT_BUYER_SEQUENCE["slug"]:
        touch = _step_touch(step)
        if touch:
            from app.services.agent_messaging import (
                build_ladder_touch_body,
                ladder_touch_subject,
            )

            name = account.name or "your team"
            industry = account.industry or ""
            return (
                ladder_touch_subject(touch, name, industry),
                build_ladder_touch_body(touch, name, industry),
            )
    subject = _render_template(step.subject_template or f"Follow-up — {account.name}", account)
    body = _render_template(
        step.body_template or account.outreach_draft or "Following up from Ready For Robots.",
        account,
    )
    return subject, body


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
    slug_cache: dict[Any, str | None] = {}
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
        # Deliverability gate — mirror the intro send gate. Follow-ups keep running while
        # the circuit breaker has PAUSED intros, so an ungated follow-up loop was re-hitting
        # dead/guessed mailboxes and pinning the trailing bounce rate above threshold (the
        # breaker could never auto-recover). Never follow up to an address that already
        # bounced/complained, and re-verify it's still deliverable before sending.
        if address_previously_bounced(db, account.contact_email):
            enrollment.status = "blocked"
            enrollment.paused_reason = "suppressed_bounced"
            skipped += 1
            continue
        deliverable, deliver_reason = verify_email_deliverable(account.contact_email)
        if not deliverable:
            enrollment.status = "blocked"
            enrollment.paused_reason = f"undeliverable:{deliver_reason}"
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
        if enrollment.sequence_id not in slug_cache:
            seq_row = (
                db.query(OutreachSequence.slug)
                .filter(OutreachSequence.id == enrollment.sequence_id)
                .first()
            )
            slug_cache[enrollment.sequence_id] = seq_row[0] if seq_row else None
        subject, body = _render_sequence_step(
            step, account, sequence_slug=slug_cache[enrollment.sequence_id]
        )
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
