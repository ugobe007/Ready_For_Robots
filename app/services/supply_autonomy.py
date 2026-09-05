"""Supply-side Cal autonomy — vendor outreach with signup CTA, scheduled sends, format review."""
from __future__ import annotations

import hashlib
import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import quote

from sqlalchemy.orm import Session

from app.models.robot_company import RobotCompany
from app.models.supply_outreach import SupplyOutreachMessage
from app.services.cal_autonomy import get_cal_review_email, resolve_cal_admin_context

logger = logging.getLogger(__name__)

_REDIS_FP_KEY = "supply:outreach:template_fingerprint"


def supply_autonomy_enabled() -> bool:
    if os.getenv("SUPPLY_AUTONOMY_ENABLED", "").strip().lower() in ("0", "false", "no"):
        return False
    if os.getenv("SUPPLY_AUTONOMY_ENABLED", "").strip().lower() in ("1", "true", "yes"):
        return True
    return os.getenv("ENABLE_SCHEDULED_SUPPLY_AUTONOMY", "").strip().lower() in ("1", "true", "yes")


def _redis_client():
    url = (os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL") or "").strip()
    if not url:
        return None
    try:
        import redis

        return redis.from_url(url, decode_responses=True)
    except Exception:
        return None


def _stored_template_fingerprint() -> Optional[str]:
    client = _redis_client()
    if not client:
        return None
    try:
        return client.get(_REDIS_FP_KEY)
    except Exception:
        return None


def _persist_template_fingerprint(fp: str) -> None:
    client = _redis_client()
    if not client:
        return
    try:
        client.set(_REDIS_FP_KEY, fp, ex=60 * 60 * 24 * 120)
    except Exception:
        pass


def _site_url() -> str:
    return (os.getenv("PUBLIC_SITE_URL") or "https://readyforrobots.com").rstrip("/")


def build_supply_tracking(
    rc: RobotCompany,
    *,
    message_token: str | None = None,
) -> dict[str, str]:
    tracking = {
        "utm_source": "cal_supply",
        "utm_medium": "email",
        "utm_campaign": "vendor_signup",
        "rc": str(getattr(rc, "id", "") or ""),
    }
    if message_token:
        tracking["msg"] = message_token
    return {k: v for k, v in tracking.items() if v}


def build_supply_cta_url(rc: RobotCompany, *, tracking: dict[str, str] | None = None) -> str:
    site = _site_url()
    website = (getattr(rc, "website", None) or "").strip()
    query = "&".join(f"{key}={quote(value, safe='')}" for key, value in (tracking or {}).items())
    if website:
        base = f"{site}/results?url={quote(website, safe='')}"
        return f"{base}&{query}" if query else base
    return f"{site}/signup?{query}" if query else f"{site}/signup"


def append_signup_cta(
    body: str,
    rc: RobotCompany,
    *,
    tracking: dict[str, str] | None = None,
) -> str:
    """Ensure vendor outreach includes a signup / results scan link."""
    text = (body or "").rstrip()
    lower = text.lower()
    if "readyforrobots.com/signup" in lower or "/results?url=" in lower:
        return text
    link = build_supply_cta_url(rc, tracking=tracking)
    website = (getattr(rc, "website", None) or "").strip()
    if website:
        line = f"Start free — scan your market and get matched buyer signals: {link}"
    else:
        line = f"Create a free workspace to receive matched buyer signals: {link}"
    return f"{text}\n\n{line}"


def outreach_template_fingerprint() -> str:
    from types import SimpleNamespace

    from app.api.robot_companies import _vendor_signup_email

    version = (os.getenv("SUPPLY_TEMPLATE_VERSION") or "1").strip()
    sample = SimpleNamespace(
        company_name="Sample Robotics Inc",
        robot_type="AMR",
        target_market="logistics",
        website="https://example.com",
        data_source=None,
        market_intelligence={},
        next_trade_show=None,
        trade_shows=None,
    )
    matches = [
        {
            "company_name": "Acme Warehouse",
            "industry": "Logistics",
            "why_match": "Active automation signal.",
            "signal": "CapEx expansion noted.",
        }
    ]
    draft = _vendor_signup_email(sample, matches)
    body = append_signup_cta(draft["body"], sample)
    payload = f"{version}|{draft['subject']}|{body[:900]}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def notify_admin_of_format_change(
    *,
    sample_company: str,
    sample_subject: str,
    sample_body: str,
    previous_fingerprint: Optional[str],
    new_fingerprint: str,
) -> bool:
    to_email = get_cal_review_email()
    if not to_email:
        logger.warning("Supply format changed but ADMIN_EMAIL / ADMIN_EMAILS is not configured")
        return False

    from app.services.resend_email import ResendEmailError, send_email_via_resend

    subject = "Cal updated supply outreach format — review sample"
    body = f"""Cal refreshed the vendor supply outreach template used for robot company signups.

Previous fingerprint: {previous_fingerprint or "(none)"}
New fingerprint: {new_fingerprint}
Template version: {os.getenv("SUPPLY_TEMPLATE_VERSION") or "1"}

Sample company: {sample_company}
Sample subject: {sample_subject}

--- Sample draft Cal will send (autonomous sends continue) ---

{sample_body}

---
Review in supply pipeline: /supply-pipeline
Reply to this email if you want supply autonomy paused or the tone adjusted.
"""
    try:
        send_email_via_resend(
            to_email=to_email,
            subject=subject,
            body_text=body,
            from_display_name="Ready For Robots · Cal ops",
            idempotency_key=f"supply-format-review-{new_fingerprint}",
        )
        return True
    except ResendEmailError as exc:
        logger.warning("Supply format review email failed: %s", exc)
        return False


def _allow_inferred_inboxes() -> bool:
    return os.getenv("SUPPLY_AUTONOMY_ALLOW_INFERRED", "").strip().lower() in ("1", "true", "yes")


def _pick_recipient(contact_strategy: dict[str, Any]) -> Optional[str]:
    from app.services.lead_enrichment import verify_email_deliverable

    allow_inferred = _allow_inferred_inboxes()
    for target in contact_strategy.get("targets") or []:
        email = (target.get("contact") or "").strip()
        if not email:
            continue
        if target.get("needs_verification") and not allow_inferred:
            continue
        ok, _reason = verify_email_deliverable(email)
        if ok:
            return email
    for email in contact_strategy.get("recommended_to") or []:
        email = (email or "").strip()
        if not email:
            continue
        ok, _reason = verify_email_deliverable(email)
        if ok:
            return email
    return None


def _sent_robot_company_ids(db: Session) -> set[int]:
    rows = (
        db.query(SupplyOutreachMessage.robot_company_id)
        .filter(SupplyOutreachMessage.status.in_(("sent", "test_sent")))
        .distinct()
        .all()
    )
    return {int(row[0]) for row in rows if row[0] is not None}


def _send_supply_email(
    db: Session,
    *,
    company: RobotCompany,
    user: dict[str, Any],
    to_emails: list[str],
    subject: str,
    body: str,
    dry_run: bool,
    tracking: dict[str, str] | None = None,
    match_lead_ids: list[int] | None = None,
) -> dict[str, Any]:
    from app.api.robot_companies import (
        _create_crm_supply_tracking_copy,
        _prepare_supply_pipeline_copy,
        _supply_reply_address,
        _uuid_for_session,
    )
    from app.services.cal_email_send import send_cal_email_via_resend
    from app.services.resend_email import ResendEmailError

    subject, body = _prepare_supply_pipeline_copy(company, subject, body)
    if dry_run:
        return {"dry_run": True, "subject": subject, "to_emails": to_emails}

    reply_token = secrets.token_urlsafe(18)
    reply_to = _supply_reply_address(reply_token)
    inbound_missing = False
    try:
        send_result = send_cal_email_via_resend(
            to_email=to_emails,
            subject=subject,
            body_text=body,
            from_display_name="Cal",
            reply_to=reply_to,
            idempotency_key=f"supply-auto/{company.id}/{'-'.join(to_emails)[:120]}",
            include_demo=True,
        )
    except ResendEmailError as exc:
        err_text = str(exc).lower()
        if any(
            kw in err_text
            for kw in (
                "notification service",
                "notification_service",
                "notification url",
                "notification_url",
                "inbound",
                "not set",
                "not configured",
            )
        ):
            inbound_missing = True
            send_result = send_cal_email_via_resend(
                to_email=to_emails,
                subject=subject,
                body_text=body,
                from_display_name="Cal",
                reply_to=None,
                idempotency_key=f"supply-auto/{company.id}/{'-'.join(to_emails)[:120]}/no-inbound",
                include_demo=True,
            )
        else:
            raise

    now = datetime.now(timezone.utc)
    effective_reply_to = None if inbound_missing else reply_to
    msg = SupplyOutreachMessage(
        id=_uuid_for_session(db),
        robot_company_id=company.id,
        to_emails=to_emails,
        from_email=send_result.get("from_email"),
        reply_to=effective_reply_to,
        reply_token=reply_token,
        subject=subject,
        body_text=body,
        template_type="supply_pipeline",
        resend_id=send_result.get("resend_id"),
        status="sent",
        is_test=False,
        payload={
            "source": "supply_autonomy",
            "conversion_tracking": tracking or {},
            "match_lead_ids": match_lead_ids or [],
            **({"inbound_not_configured": True} if inbound_missing else {}),
        },
        approved_at=now,
        sent_at=now,
    )
    db.add(msg)
    _create_crm_supply_tracking_copy(
        db,
        company,
        user=user,
        to_emails=to_emails,
        subject=subject,
        body=body,
        reply_to=effective_reply_to or "",
        send_result=send_result,
        supply_message=msg,
    )
    company.last_contact_date = now
    timestamp = now.strftime("%Y-%m-%d %H:%M")
    existing = company.workflow_notes or ""
    company.workflow_notes = (
        f"{existing}\n[{timestamp}] Supply autonomy sent to {to_emails}: {subject}"
    ).strip()
    if company.outreach_status == "not_contacted":
        company.outreach_status = "contacted"
    return {"sent": True, "supply_outreach_message_id": str(msg.id), "to_emails": to_emails}


def run_supply_autonomy_cycle(db: Session, *, dry_run: bool = False) -> dict[str, Any]:
    """Send vendor signup outreach to unscored robot companies with verified contacts."""
    if not supply_autonomy_enabled():
        return {"status": "disabled", "reason": "SUPPLY_AUTONOMY_ENABLED / ENABLE_SCHEDULED_SUPPLY_AUTONOMY off"}

    ctx = resolve_cal_admin_context(db)
    if not ctx:
        return {
            "status": "skipped",
            "reason": "No admin-cal-outreach team — sign in to /admin once or set CAL_ADMIN_USER_ID",
        }

    uid, _team = ctx
    admin_email = get_cal_review_email() or "admin@readyforrobots.com"
    user = {"uid": str(uid), "email": admin_email}

    from app.api.robot_companies import (
        _contact_strategy,
        _match_buyer_leads,
        _research_robot_company_contacts,
        _select_supply_batch_matches,
        _vendor_signup_email,
    )

    min_score = int(os.getenv("SUPPLY_AUTONOMY_MIN_SCORE", "60") or "60")
    send_limit = int(os.getenv("SUPPLY_AUTONOMY_SEND_LIMIT", "6") or "6")
    batch_limit = int(os.getenv("SUPPLY_AUTONOMY_BATCH", "40") or "40")
    sent_ids = _sent_robot_company_ids(db)

    candidates = (
        db.query(RobotCompany)
        .filter(
            RobotCompany.lead_score >= min_score,
            RobotCompany.outreach_status == "not_contacted",
        )
        .order_by(RobotCompany.lead_score.desc())
        .limit(max(batch_limit, send_limit * 4))
        .all()
    )

    sent = 0
    skipped_already_sent = 0
    skipped_no_contact = 0
    skipped_unverified = 0
    skipped_insufficient_matches = 0
    skipped_assembly_rejected = 0
    errors: list[dict[str, Any]] = []
    format_sample: Optional[tuple[str, str, str]] = None
    used_lead_ids: set[int] = set()

    for company in candidates:
        if company.id in sent_ids:
            skipped_already_sent += 1
            continue
        if sent >= send_limit:
            break

        matches = _match_buyer_leads(db, company, limit=12)
        matches = _select_supply_batch_matches(matches, used_lead_ids, limit=3)
        from app.services.cal_pipeline_enrichment import ensure_supply_matches_enriched

        matches, _enriched_count = ensure_supply_matches_enriched(db, matches)
        min_matches = int(os.getenv("SUPPLY_AUTONOMY_MIN_MATCHES", "2") or "2")
        tracking_token = secrets.token_urlsafe(10)
        tracking = build_supply_tracking(company, message_token=tracking_token)

        research = _research_robot_company_contacts(company, enabled=True, max_pages=1, timeout=1.2)
        contact = _contact_strategy(company, research)
        to_email = _pick_recipient(contact)
        if not to_email:
            skipped_no_contact += 1
            continue

        draft = _vendor_signup_email(company, matches, force_rfr=True)
        body = append_signup_cta(draft["body"], company, tracking=tracking)
        subject = draft["subject"]

        from app.services.cal_assembly_agent import assemble_supply_outreach, cal_assembly_required

        if cal_assembly_required():
            assembly = assemble_supply_outreach(
                db,
                company,
                matches,
                subject=subject,
                body=body,
                min_matches=min_matches,
            )
            if not assembly.approved:
                skipped_assembly_rejected += 1
                from app.services.cal_ops_monitor import record_cal_assembly_rejection

                record_cal_assembly_rejection(
                    db,
                    channel="supply",
                    robot_company_id=company.id,
                    vendor_name=company.company_name or "",
                    subject=subject,
                    issues=assembly.issues,
                )
                logger.info(
                    "Cal assembly rejected supply send to %s: %s",
                    company.company_name,
                    "; ".join(assembly.issues[:5]),
                )
                continue
            if assembly.matches and assembly.matches != matches:
                draft = _vendor_signup_email(company, assembly.matches, force_rfr=True)
                body = append_signup_cta(draft["body"], company, tracking=tracking)
                subject = draft["subject"]
                matches = assembly.matches
        elif len(matches) < max(1, min_matches):
            skipped_insufficient_matches += 1
            continue

        for match in matches:
            match_id = int(match.get("id") or 0)
            if match_id:
                used_lead_ids.add(match_id)

        if format_sample is None:
            format_sample = (company.company_name or "Sample", subject, body)

        try:
            _send_supply_email(
                db,
                company=company,
                user=user,
                to_emails=[to_email],
                subject=subject,
                body=body,
                dry_run=dry_run,
                tracking=tracking,
                match_lead_ids=[int(m.get("id") or 0) for m in matches if m.get("id")],
            )
            sent += 1
            sent_ids.add(company.id)
        except Exception as exc:
            err_text = str(exc).lower()
            if "verify" in err_text or "deliverable" in err_text:
                skipped_unverified += 1
            else:
                errors.append({"company_id": company.id, "name": company.company_name, "error": str(exc)})

    new_fp = outreach_template_fingerprint()
    old_fp = _stored_template_fingerprint()
    format_notified = False
    if format_sample and (old_fp is None or old_fp != new_fp) and not dry_run:
        format_notified = notify_admin_of_format_change(
            sample_company=format_sample[0],
            sample_subject=format_sample[1],
            sample_body=format_sample[2],
            previous_fingerprint=old_fp,
            new_fingerprint=new_fp,
        )
    if not dry_run and (old_fp != new_fp or old_fp is None):
        _persist_template_fingerprint(new_fp)

    if not dry_run and (sent or skipped_assembly_rejected):
        db.commit()

    return {
        "status": "ok",
        "dry_run": dry_run,
        "sent": sent,
        "skipped_already_sent": skipped_already_sent,
        "skipped_no_contact": skipped_no_contact,
        "skipped_unverified": skipped_unverified,
        "skipped_insufficient_matches": skipped_insufficient_matches,
        "skipped_assembly_rejected": skipped_assembly_rejected,
        "errors": errors[:20],
        "template_fingerprint": new_fp,
        "format_review_notified": format_notified,
        "review_email": get_cal_review_email(),
        "admin_user_id": str(uid),
        "min_score": min_score,
        "send_limit": send_limit,
    }


def get_supply_autonomy_status() -> dict[str, Any]:
    from app.services.cal_assembly_agent import get_cal_assembly_status

    return {
        "enabled": supply_autonomy_enabled(),
        "review_email": get_cal_review_email(),
        "template_fingerprint": outreach_template_fingerprint(),
        "stored_fingerprint": _stored_template_fingerprint(),
        "template_version": os.getenv("SUPPLY_TEMPLATE_VERSION") or "1",
        "send_limit": int(os.getenv("SUPPLY_AUTONOMY_SEND_LIMIT", "6") or "6"),
        "min_score": int(os.getenv("SUPPLY_AUTONOMY_MIN_SCORE", "60") or "60"),
        "every_hours": float(os.getenv("SUPPLY_AUTONOMY_EVERY_HOURS", "6") or "6"),
        "allow_inferred_inboxes": _allow_inferred_inboxes(),
        "assembly": get_cal_assembly_status(),
    }
