"""Daily Cal activity digest — plain-text operator email (no admin UI required)."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_REDIS_DIGEST_KEY = "cal:daily_digest:last_sent_date"
_SITE = (os.getenv("PUBLIC_SITE_URL") or "https://readyforrobots.com").rstrip("/")


def get_cal_digest_recipients() -> list[str]:
    """Inbox(es) for the daily Cal digest."""
    explicit = (os.getenv("CAL_DAILY_DIGEST_EMAIL") or "").strip()
    if explicit:
        return _split_emails(explicit)
    from app.services.cal_autonomy import get_cal_review_email

    primary = get_cal_review_email()
    if primary:
        return [primary]
    admins = (os.getenv("ADMIN_EMAILS") or "").strip()
    return _split_emails(admins)


def _split_emails(raw: str) -> list[str]:
    emails: list[str] = []
    seen: set[str] = set()
    for part in raw.replace(";", ",").split(","):
        email = part.strip()
        if "@" not in email:
            continue
        key = email.lower()
        if key in seen:
            continue
        seen.add(key)
        emails.append(email)
    return emails


def _redis_client():
    from app.services.cal_autonomy import _redis_client as client_fn

    return client_fn()


def _digest_already_sent(day: str) -> bool:
    client = _redis_client()
    if not client:
        return False
    try:
        return str(client.get(_REDIS_DIGEST_KEY) or "") == day
    except Exception:
        return False


def _mark_digest_sent(day: str) -> None:
    client = _redis_client()
    if not client:
        return
    try:
        client.set(_REDIS_DIGEST_KEY, day, ex=60 * 60 * 48)
    except Exception:
        pass


def build_cal_daily_digest(db: Session, *, period_hours: int = 24) -> dict[str, Any]:
    """Collect Cal queue stats + recent activity for the operator digest."""
    from app.models.calendar import CalendarEvent
    from app.models.crm import CrmAccount
    from app.models.outreach import OutreachMessage, OutreachReply
    from app.models.sales_agent import SalesAgentAction, SalesOpportunity
    from app.models.sequences import OutreachSequenceEnrollment
    from app.services.cal_autonomy import get_cal_autonomy_status, resolve_cal_admin_context

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=max(1, period_hours))
    day_label = now.date().isoformat()

    autopilot = get_cal_autonomy_status()
    ctx = resolve_cal_admin_context(db)
    queue_summary: dict[str, Any] = {}
    if ctx:
        from app.api.admin_extended import _build_cal_draft_status_payload

        admin_uid, _team = ctx
        payload = _build_cal_draft_status_payload(
            db,
            admin_uid=admin_uid,
            include_draft_bodies=False,
            include_prospects=False,
            prospect_limit=0,
        )
        queue_summary = payload.get("summary") or {}

    sent_statuses = ["sent", "delivered", "opened", "clicked", "replied"]
    intro_sent = (
        db.query(func.count(OutreachMessage.id))
        .filter(
            OutreachMessage.sent_at.isnot(None),
            OutreachMessage.sent_at >= since,
            OutreachMessage.sent_at <= now,
            or_(
                OutreachMessage.send_identity.is_(None),
                OutreachMessage.send_identity.in_(("cal", "admin", "crm")),
            ),
        )
        .scalar()
        or 0
    )
    # Follow-ups are recorded by the sequence runner with a
    # ``payload.sequence_enrollment_id`` marker (send_identity defaults to
    # "scout"). The old filter counted send_identity == "sequence" — a value no
    # sender ever writes — so follow-ups always reported 0 even when they sent.
    followup_marker = OutreachMessage.payload.op("->>")("sequence_enrollment_id").isnot(None)
    followup_sent = (
        db.query(func.count(OutreachMessage.id))
        .filter(
            OutreachMessage.sent_at.isnot(None),
            OutreachMessage.sent_at >= since,
            OutreachMessage.sent_at <= now,
            followup_marker,
        )
        .scalar()
        or 0
    )
    replies = (
        db.query(func.count(OutreachReply.id))
        .filter(OutreachReply.received_at >= since, OutreachReply.received_at <= now)
        .scalar()
        or 0
    )
    drafts_touched = (
        db.query(func.count(CrmAccount.id))
        .filter(
            CrmAccount.outreach_draft.isnot(None),
            CrmAccount.updated_at >= since,
        )
        .scalar()
        or 0
    )
    enroll_due = (
        db.query(func.count(OutreachSequenceEnrollment.id))
        .filter(
            OutreachSequenceEnrollment.status == "active",
            OutreachSequenceEnrollment.next_step_at.isnot(None),
            OutreachSequenceEnrollment.next_step_at <= now,
        )
        .scalar()
        or 0
    )
    enroll_active = (
        db.query(func.count(OutreachSequenceEnrollment.id))
        .filter(OutreachSequenceEnrollment.status == "active")
        .scalar()
        or 0
    )

    recent_intros = (
        db.query(OutreachMessage)
        .filter(
            OutreachMessage.sent_at.isnot(None),
            OutreachMessage.sent_at >= since,
            or_(
                OutreachMessage.send_identity.is_(None),
                OutreachMessage.send_identity.in_(("cal", "admin", "crm")),
            ),
        )
        .order_by(desc(OutreachMessage.sent_at))
        .limit(8)
        .all()
    )
    crm_names = {
        str(row.id): row.name
        for row in db.query(CrmAccount.id, CrmAccount.name).limit(2000).all()
    }
    intro_lines = []
    for msg in recent_intros:
        who = crm_names.get(str(msg.crm_account_id)) or msg.to_email or "prospect"
        when = msg.sent_at.strftime("%H:%M UTC") if msg.sent_at else "?"
        intro_lines.append(f"  • {when} — {who} — {msg.subject or '(no subject)'}")

    recent_replies = (
        db.query(OutreachReply)
        .filter(OutreachReply.received_at >= since)
        .order_by(desc(OutreachReply.received_at))
        .limit(6)
        .all()
    )
    reply_lines = []
    for reply in recent_replies:
        who = crm_names.get(str(reply.crm_account_id)) or reply.from_email or "sender"
        when = reply.received_at.strftime("%H:%M UTC") if reply.received_at else "?"
        reply_lines.append(f"  • {when} — {who} — {reply.subject or 'Inbound reply'}")

    needs_you: list[str] = []

    # Positive-intent replies are the whole point of the loop — put them at the top
    # of "Needs you" so a warm "yes / let's talk / what's it cost" never gets buried.
    _POSITIVE_INTENTS = ("interested", "meeting", "pricing", "referral")
    hot_replies = (
        db.query(OutreachReply)
        .filter(
            OutreachReply.received_at >= since,
            OutreachReply.detected_intent.in_(_POSITIVE_INTENTS),
        )
        .order_by(desc(OutreachReply.received_at))
        .limit(8)
        .all()
    )
    _intent_label = {
        "interested": "Interested reply",
        "meeting": "Wants a call",
        "pricing": "Asked about pricing",
        "referral": "Referred you on",
    }
    for reply in hot_replies:
        who = crm_names.get(str(reply.crm_account_id)) or reply.from_email or "prospect"
        label = _intent_label.get(reply.detected_intent or "", "Reply")
        needs_you.append(f"  • {label} — reply to {who}")

    pending_approval = (
        db.query(SalesAgentAction)
        .filter(
            SalesAgentAction.requires_approval.is_(True),
            SalesAgentAction.status.in_(["planned", "draft", "pending", "review", "drafted"]),
        )
        .order_by(desc(SalesAgentAction.updated_at))
        .limit(5)
        .all()
    )
    for action in pending_approval:
        needs_you.append(f"  • Approve Cal action: {action.recommendation or action.action_type}")

    scheduled_opp_ids = {
        str(row.sales_opportunity_id)
        for row in db.query(CalendarEvent.sales_opportunity_id)
        .filter(CalendarEvent.sales_opportunity_id.isnot(None))
        .all()
        if row.sales_opportunity_id
    }
    meeting_opps = (
        db.query(SalesOpportunity)
        .filter(SalesOpportunity.current_stage == "meeting_requested")
        .order_by(desc(SalesOpportunity.updated_at))
        .limit(5)
        .all()
    )
    for opp in meeting_opps:
        if str(opp.id) in scheduled_opp_ids:
            continue
        needs_you.append(f"  • Book meeting: {opp.title or 'Opportunity'}")

    from app.services.cal_ops_monitor import get_cal_ops_monitor

    # Assembly rejections are Cal's buyer/eligibility guard working as intended —
    # it auto-skips OEMs/vendors (e.g. Zebra) that are not real buyers. No send
    # happened and no operator action is required, so these are FYI, not "Needs
    # you" alarms. Surfacing them as tasks made the digest read as broken.
    auto_filtered: list[str] = []
    ops = get_cal_ops_monitor(db, limit=5)
    for row in ops.get("assembly_rejections") or []:
        name = row.get("vendor_name") or "prospect"
        issue = "; ".join((row.get("issues") or [])[:1]) or "not a buyer opportunity"
        auto_filtered.append(f"  • {name}: {issue}")

    autopilot_on = bool(autopilot.get("enabled"))
    sendable = int(queue_summary.get("sendable") or 0)
    unsent = int(queue_summary.get("unsent_drafted") or 0)
    replied_total = int(queue_summary.get("replied") or 0)

    # Deliverability (trailing 7d) — makes the bounce trend visible and signals when
    # the circuit breaker is likely to pause new intros.
    from app.services.lead_enrichment import recent_bounce_rate

    deliverability = recent_bounce_rate(db, hours=168)
    pause_threshold = float(os.getenv("CAL_BOUNCE_PAUSE_THRESHOLD", "0.10") or "0.10")
    deliverability["pause_threshold"] = pause_threshold
    deliverability["paused"] = (
        deliverability["sent"] >= int(os.getenv("CAL_BOUNCE_PAUSE_MIN_SAMPLE", "20") or "20")
        and deliverability["rate"] > pause_threshold
    )

    body = render_cal_daily_digest_text(
        day_label=day_label,
        period_hours=period_hours,
        autopilot_on=autopilot_on,
        queue_summary=queue_summary,
        activity={
            "intro_sent": intro_sent,
            "followup_sent": followup_sent,
            "replies": replies,
            "drafts_touched": drafts_touched,
            "enroll_active": enroll_active,
            "enroll_due": enroll_due,
            "replied_total": replied_total,
            "sendable": sendable,
            "unsent_drafted": unsent,
            "deliverability": deliverability,
        },
        intro_lines=intro_lines,
        reply_lines=reply_lines,
        needs_you=needs_you,
        auto_filtered=auto_filtered,
    )

    return {
        "date": day_label,
        "subject": f"Cal daily update — {day_label}",
        "body_text": body,
        "recipients": get_cal_digest_recipients(),
        "autopilot": autopilot,
        "queue_summary": queue_summary,
        "activity": {
            "intro_sent": intro_sent,
            "followup_sent": followup_sent,
            "replies": replies,
            "drafts_touched": drafts_touched,
        },
    }


def render_cal_daily_digest_text(
    *,
    day_label: str,
    period_hours: int,
    autopilot_on: bool,
    queue_summary: dict[str, Any],
    activity: dict[str, Any],
    intro_lines: list[str],
    reply_lines: list[str],
    needs_you: list[str],
    auto_filtered: list[str] | None = None,
) -> str:
    autopilot_line = "ON — Cal runs draft/send/follow-up cycles on the worker." if autopilot_on else (
        "OFF — scheduled cycles paused (manual Run cycle still works in admin)."
    )
    hot = int(queue_summary.get("hot") or 0)
    warm = int(queue_summary.get("warm") or 0)
    sendable = int(activity.get("sendable") or 0)
    unsent = int(activity.get("unsent_drafted") or 0)
    replied_total = int(activity.get("replied_total") or 0)

    lines = [
        f"Cal daily update — {day_label}",
        "",
        "What Cal did (last {0}h)".format(period_hours),
        f"  • Buyer intro emails sent: {activity.get('intro_sent', 0)}",
        f"  • Follow-up emails sent: {activity.get('followup_sent', 0)}",
        f"  • Inbound replies received: {activity.get('replies', 0)}",
        f"  • Drafts created or refreshed: {activity.get('drafts_touched', 0)}",
        "",
        "Queue right now",
        f"  • HOT / WARM prospects in Cal queue: {hot} / {warm}",
        f"  • Drafts ready to send: {sendable}",
        f"  • Drafts waiting (unsent): {unsent}",
        f"  • Active follow-up sequences: {activity.get('enroll_active', 0)} "
        f"({activity.get('enroll_due', 0)} due now)",
        f"  • Total replied (all time in queue): {replied_total}",
        "",
        f"Autopilot: {autopilot_line}",
        "",
    ]

    deliverability = activity.get("deliverability") or {}
    if int(deliverability.get("sent") or 0) > 0:
        rate_pct = float(deliverability.get("rate") or 0.0) * 100
        thr_pct = float(deliverability.get("pause_threshold") or 0.10) * 100
        status = (
            "⚠️ PAUSING new intros" if deliverability.get("paused")
            else "OK" if rate_pct <= thr_pct
            else "elevated"
        )
        lines.extend([
            "Deliverability (last 7d)",
            f"  • Sends: {deliverability.get('sent', 0)}  •  Delivered: {deliverability.get('delivered', 0)}"
            f"  •  Bounced/complaints: {deliverability.get('bounced', 0)}",
            f"  • Bounce rate: {rate_pct:.1f}%  (circuit breaker at {thr_pct:.0f}%) — {status}",
            "",
        ])

    # When nothing new went out but the queue still shows prospects, say why —
    # otherwise "sent: 0" alongside "ready: N" reads as a broken pipeline when
    # it is actually the verified-contact gate plus an already-contacted pool.
    if int(activity.get("intro_sent") or 0) == 0 and (sendable > 0 or hot > 0):
        lines.extend([
            "Why 0 new intros",
            "  • Cal only emails verified contacts. Ready drafts without a verified "
            "email wait for enrichment; the rest of the HOT/WARM pool is already "
            "contacted and is now in follow-up. New intros resume as fresh, verified "
            "buyers land in the queue.",
            "",
        ])

    if intro_lines:
        lines.extend(["Recent intro sends", *intro_lines, ""])
    else:
        lines.extend(["Recent intro sends", "  • (none in this period)", ""])

    if reply_lines:
        lines.extend(["Recent replies", *reply_lines, ""])
    elif int(activity.get("replies") or 0) == 0:
        lines.extend(["Recent replies", "  • (none in this period)", ""])

    if needs_you:
        lines.extend(["Needs you", *needs_you[:8], ""])
    else:
        lines.extend(["Needs you", "  • Nothing urgent — Cal is running.", ""])

    if auto_filtered:
        lines.extend([
            "Auto-filtered by Cal (FYI — no action needed)",
            "  These were skipped as OEMs/vendors, not buyers. Cal did not email them.",
            *auto_filtered[:6],
            "",
        ])

    lines.extend([
        "Links",
        f"  • Admin (Cal control): {_SITE}/admin",
        f"  • Replies inbox: {_SITE}/inbox",
        f"  • Calendar (book meetings): {_SITE}/calendar",
        "",
        "You receive this once per day while Cal daily digest is enabled.",
        "Reply to this email if you want Cal paused or the tone adjusted.",
    ])
    return "\n".join(lines)


def send_cal_daily_digest(
    db: Session,
    *,
    period_hours: int = 24,
    force: bool = False,
) -> dict[str, Any]:
    """Email the daily Cal digest. Skips if already sent today unless force=True."""
    recipients = get_cal_digest_recipients()
    if not recipients:
        return {"sent": False, "reason": "No CAL_DAILY_DIGEST_EMAIL / ADMIN_EMAIL configured"}

    today = datetime.now(timezone.utc).date().isoformat()
    if not force and _digest_already_sent(today):
        return {"sent": False, "reason": "Already sent today", "date": today, "recipients": recipients}

    digest = build_cal_daily_digest(db, period_hours=period_hours)
    from app.services.resend_email import ResendEmailError, send_email_via_resend

    try:
        result = send_email_via_resend(
            to_email=recipients,
            subject=digest["subject"],
            body_text=digest["body_text"],
            from_display_name="Ready For Robots · Cal",
            idempotency_key=f"cal-daily-digest-{today}",
        )
    except ResendEmailError as exc:
        logger.warning("Cal daily digest email failed: %s", exc)
        return {"sent": False, "reason": str(exc), "recipients": recipients}

    _mark_digest_sent(today)
    return {
        "sent": True,
        "date": today,
        "recipients": recipients,
        "resend_id": result.get("resend_id"),
        "activity": digest.get("activity"),
        "queue_summary": digest.get("queue_summary"),
    }


def cal_daily_digest_enabled() -> bool:
    if os.getenv("CAL_DAILY_DIGEST_ENABLED", "").strip().lower() in ("0", "false", "no"):
        return False
    return os.getenv("ENABLE_SCHEDULED_CAL_DAILY_DIGEST", "1").strip().lower() in ("1", "true", "yes")


def next_digest_run_utc(*, hour: int = 15, minute: int = 0) -> datetime:
    """Next scheduled send at hour:minute UTC."""
    now = datetime.now(timezone.utc)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target
