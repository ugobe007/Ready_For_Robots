"""Jobs CRM account storage: keep jobs, apply/outreach, employer threads."""
from __future__ import annotations

import json
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.jobs_crm import ApplicationMessage, JobApplication, JobsCrmActivity, KeptJob
from app.services.email_address import normalize_recipient_email
from app.services.plan_entitlements import (
    jobs_crm_monthly_cap,
    jobs_crm_ttl_days,
    jobs_crm_unlocked_limit,
    resolve_plan_tier,
)

SEND_NOT_SENT_NO_EMAIL = "not_sent_no_email"
SEND_STORED = "stored"
SEND_SENT = "sent"
SEND_FAILED = "failed"

THREAD_DRAFT = "draft"
THREAD_SENT = "sent"
THREAD_AWAITING = "awaiting_reply"
THREAD_REPLIED = "replied"

_NO_EMAIL_REASON = (
    "This Job Card has no employer contact email. We do not invent one. "
    "The application is stored on your account. Add a real employer email later, "
    "or paste a reply in the CRM inbox if they contact you another way."
)

_EMAIL_KEYS = (
    "employer_email",
    "contact_email",
    "company_email",
    "email",
)


def _uid(user: dict) -> UUID:
    return UUID(str(user["uid"]))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _has_monthly_price(value: str) -> bool:
    text = (value or "").strip()
    if not text:
        return False
    if re.fullmatch(r"(n/?a|none|tbd|unknown|-)", text, flags=re.I):
        return False
    return True


def employer_email_from_job(job: dict[str, Any] | None) -> Optional[str]:
    """Return a real contact email on the Job Card, or None. Never invent."""
    if not isinstance(job, dict):
        return None
    for key in _EMAIL_KEYS:
        raw = job.get(key)
        if isinstance(raw, str):
            hit = normalize_recipient_email(raw)
            if hit:
                return hit
    employer = job.get("employer")
    if isinstance(employer, dict):
        for key in _EMAIL_KEYS:
            raw = employer.get(key)
            if isinstance(raw, str):
                hit = normalize_recipient_email(raw)
                if hit:
                    return hit
    return None


def catalog_skus_for_oem(
    *,
    url: str | None = None,
    company_name: str | None = None,
) -> list[dict[str, str]]:
    """Named SKUs from the OEM listing / vendor_robots_oem_sku_seed. Never invent."""
    seen: set[str] = set()
    out: list[dict[str, str]] = []

    def _add(name: str, slug: str = "", source: str = "oem_listing") -> None:
        cleaned = re.sub(r"\s+", " ", (name or "").strip())
        key = re.sub(r"[^a-z0-9]", "", cleaned.lower())
        if len(key) < 2 or key in seen:
            return
        seen.add(key)
        out.append({"name": cleaned, "slug": slug, "source": source})

    if url:
        from app.services.jobs_oem_listing import listing_payload_for_url

        listing = listing_payload_for_url(url)
        for robot in listing.get("robots") or []:
            if isinstance(robot, dict):
                _add(str(robot.get("name") or ""), str(robot.get("slug") or ""), "oem_listing")

    if company_name:
        needle = re.sub(r"[^a-z0-9]", "", company_name.lower())
        if len(needle) >= 2:
            from app.services.vendor_robot_lookup import OEM_SKU_SEED_PATH

            try:
                data = json.loads(OEM_SKU_SEED_PATH.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {}
            for vendor in data.get("vendors") or []:
                vn = re.sub(r"[^a-z0-9]", "", str(vendor.get("vendor_name") or "").lower())
                if not vn or (needle not in vn and vn not in needle):
                    continue
                for robot in vendor.get("robots") or []:
                    if isinstance(robot, dict):
                        _add(
                            str(robot.get("name") or ""),
                            str(robot.get("model_slug") or ""),
                            "oem_sku_seed",
                        )
    return out


def jobs_crm_reply_address(reply_token: str) -> str:
    local = (
        (os.getenv("JOBS_CRM_REPLY_LOCAL_PART") or os.getenv("SCOUT_REPLY_LOCAL_PART") or "jobs")
        .strip()
        .split("@", 1)[0]
        or "jobs"
    )
    domain = (
        os.getenv("JOBS_CRM_REPLY_DOMAIN")
        or os.getenv("SCOUT_REPLY_DOMAIN")
        or os.getenv("RESEND_REPLY_TO")
        or ""
    ).strip()
    if "@" in domain:
        domain = domain.rsplit("@", 1)[1]
    if not domain:
        from_email = (os.getenv("RESEND_FROM_EMAIL") or "").strip()
        if "@" in from_email:
            domain = from_email.rsplit("@", 1)[1]
    if not domain:
        domain = "readyforrobots.com"
    return f"{local}+{reply_token}@{domain}"


def drop_expired_kept_jobs(db: Session, user_id: UUID, now: datetime | None = None) -> int:
    """Free TTL: un-acted jobs past expires_at leave the desk."""
    stamp = now or _now()
    rows = (
        db.query(KeptJob)
        .filter(
            KeptJob.user_id == user_id,
            KeptJob.acted_at.is_(None),
            KeptJob.expires_at.isnot(None),
            KeptJob.expires_at < stamp,
        )
        .all()
    )
    for row in rows:
        db.delete(row)
    return len(rows)


def _job_identity(job: dict[str, Any]) -> dict[str, Any]:
    job_key = str(job.get("job_key") or "").strip()
    employer = (
        str(job.get("company_name") or job.get("employer") or "").strip()
        if not isinstance(job.get("employer"), dict)
        else str((job.get("employer") or {}).get("name") or "").strip()
    )
    title = str(job.get("title") or job.get("work_title") or job.get("job_title") or "").strip()
    workplace = str(job.get("locality") or job.get("workplace") or "").strip() or None
    return {
        "job_key": job_key,
        "employer_name": employer or "Unnamed employer",
        "work_title": title or "Untitled work",
        "workplace": workplace,
        "source_ids": {
            "job_key": job_key,
            "path": job.get("path"),
            "source": job.get("source"),
            "industry": job.get("industry"),
        },
    }


def keep_jobs(
    db: Session,
    user: dict,
    jobs: list[dict[str, Any]],
    *,
    robot_name: str | None = None,
    robot_url: str | None = None,
    robot_submission_id: int | None = None,
) -> dict[str, Any]:
    """Upsert selected Job Cards onto the user. Enforces free batch / monthly / TTL."""
    uid = _uid(user)
    plan = resolve_plan_tier(user, db)
    batch_limit = jobs_crm_unlocked_limit(plan)
    monthly_cap = jobs_crm_monthly_cap(plan)
    ttl_days = jobs_crm_ttl_days(plan)
    now = _now()
    drop_expired_kept_jobs(db, uid, now)

    incoming: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in jobs or []:
        if not isinstance(raw, dict):
            continue
        ident = _job_identity(raw)
        key = ident["job_key"]
        if not key or key in seen:
            continue
        seen.add(key)
        incoming.append(raw)
        if batch_limit is not None and len(incoming) >= batch_limit:
            break

    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_count = (
        db.query(KeptJob)
        .filter(KeptJob.user_id == uid, KeptJob.created_at >= month_start)
        .count()
    )

    saved: list[KeptJob] = []
    created = 0
    skipped_monthly = 0
    for raw in incoming:
        ident = _job_identity(raw)
        email = employer_email_from_job(raw)
        existing = (
            db.query(KeptJob)
            .filter(KeptJob.user_id == uid, KeptJob.job_key == ident["job_key"])
            .first()
        )
        if existing:
            existing.employer_name = ident["employer_name"]
            existing.work_title = ident["work_title"]
            existing.workplace = ident["workplace"]
            existing.source_ids = ident["source_ids"]
            existing.job_payload = raw
            existing.robot_name = (robot_name or existing.robot_name or "").strip() or existing.robot_name
            existing.robot_url = (robot_url or existing.robot_url or "").strip() or existing.robot_url
            if robot_submission_id:
                existing.robot_submission_id = robot_submission_id
            if email:
                existing.employer_email = email
            existing.updated_at = now
            saved.append(existing)
            continue
        if monthly_cap is not None and monthly_count >= monthly_cap:
            skipped_monthly += 1
            continue
        row = KeptJob(
            user_id=uid,
            job_key=ident["job_key"],
            employer_name=ident["employer_name"],
            work_title=ident["work_title"],
            workplace=ident["workplace"],
            source_ids=ident["source_ids"],
            job_payload=raw,
            robot_name=(robot_name or "").strip() or None,
            robot_url=(robot_url or "").strip() or None,
            robot_submission_id=robot_submission_id,
            employer_email=email,
            expires_at=(now + timedelta(days=ttl_days)) if ttl_days else None,
        )
        db.add(row)
        monthly_count += 1
        created += 1
        saved.append(row)

    if saved:
        record_activity(
            db,
            user,
            kind="dump",
            label="Kept from FIND",
            job_key=saved[0].job_key if len(saved) == 1 else None,
            company=saved[0].employer_name if len(saved) == 1 else None,
        )
    db.commit()
    for row in saved:
        db.refresh(row)
    return {
        "saved_count": len(saved),
        "created_count": created,
        "skipped_monthly": skipped_monthly,
        "jobs": [kept_job_payload(row) for row in saved],
        "plan": plan,
        "batch_limit": batch_limit,
        "monthly_cap": monthly_cap,
    }


def list_kept_jobs(db: Session, user: dict) -> list[dict[str, Any]]:
    uid = _uid(user)
    plan = resolve_plan_tier(user, db)
    drop_expired_kept_jobs(db, uid)
    db.commit()
    rows = (
        db.query(KeptJob)
        .filter(KeptJob.user_id == uid)
        .order_by(KeptJob.created_at.desc())
        .all()
    )
    limit = jobs_crm_unlocked_limit(plan)
    if limit is not None:
        rows = rows[:limit]
    apps = {
        row.job_key: row
        for row in db.query(JobApplication)
        .filter(JobApplication.user_id == uid)
        .order_by(JobApplication.created_at.desc())
        .all()
    }
    out = []
    for row in rows:
        payload = kept_job_payload(row)
        app = apps.get(row.job_key)
        payload["application"] = application_payload(app, include_messages=False) if app else None
        out.append(payload)
    return out


def kept_job_payload(row: KeptJob) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "job_key": row.job_key,
        "employer_name": row.employer_name,
        "work_title": row.work_title,
        "workplace": row.workplace,
        "source_ids": row.source_ids or {},
        "job": row.job_payload or {},
        "robot_name": row.robot_name,
        "robot_url": row.robot_url,
        "robot_submission_id": row.robot_submission_id,
        "employer_email": row.employer_email,
        "acted_at": row.acted_at.isoformat() if row.acted_at else None,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def record_activity(
    db: Session,
    user: dict,
    *,
    kind: str,
    label: str,
    job_key: str | None = None,
    company: str | None = None,
) -> JobsCrmActivity:
    row = JobsCrmActivity(
        user_id=_uid(user),
        job_key=(job_key or "").strip() or None,
        kind=(kind or "dump").strip()[:32],
        label=(label or "").strip()[:240] or kind,
        company=(company or "").strip() or None,
    )
    db.add(row)
    return row


def list_activity(db: Session, user: dict, job_key: str | None = None) -> list[dict[str, Any]]:
    uid = _uid(user)
    q = db.query(JobsCrmActivity).filter(JobsCrmActivity.user_id == uid)
    if job_key:
        q = q.filter((JobsCrmActivity.job_key == job_key) | (JobsCrmActivity.job_key.is_(None)))
    rows = q.order_by(JobsCrmActivity.created_at.desc()).limit(40).all()
    return [
        {
            "id": str(row.id),
            "at": row.created_at.isoformat() if row.created_at else None,
            "kind": row.kind,
            "label": row.label,
            "jobKey": row.job_key,
            "company": row.company,
        }
        for row in rows
    ]


def _compose_offer_email(
    *,
    robot_name: str,
    models: list[str],
    poc: str,
    monthly_price: str,
    employer: str,
    work: str,
    workplace: str | None,
    accept_url: str | None = None,
    interview_url: str | None = None,
    document_lines: list[str] | None = None,
) -> tuple[str, str]:
    who = robot_name or "this robot"
    model_line = ", ".join(models) if models else "(no catalogued model selected)"
    place = f" at {workplace}" if workplace else ""
    subject = f"Applying {who} to {work} at {employer}"
    lines = [
        f"We are applying {who} to {work}{place}.",
        "",
        f"Model(s) we will use: {model_line}",
        f"PoC proof: {poc}",
        f"Proposed monthly price we would charge (our offer, not a site rate): {monthly_price}",
    ]
    if document_lines:
        lines.extend(["", *document_lines])
    if accept_url or interview_url:
        lines.extend(["", "Evaluate this application (no Ready For Robots account required):"])
        if accept_url:
            lines.append(f"Accept: {accept_url}")
        if interview_url:
            lines.append(f"Set up interview: {interview_url}")
    lines.extend(
        [
            "",
            "This is a proposed placement offer from the robot operator. "
            "Reply to this email to continue. We do not invent employer contacts or rental dollars.",
        ]
    )
    return subject, "\n".join(lines)


def apply_to_job(
    db: Session,
    user: dict,
    *,
    job_key: str,
    robot_name: str,
    selected_models: list[str],
    monthly_price: str,
    poc_evidence: str = "",
    poc_skipped: bool = False,
    job: dict[str, Any] | None = None,
    document_ids: list[str] | None = None,
    send: bool = True,
) -> dict[str, Any]:
    uid = _uid(user)
    price = (monthly_price or "").strip()
    models = [re.sub(r"\s+", " ", str(m).strip()) for m in (selected_models or []) if str(m).strip()]
    if not _has_monthly_price(price):
        raise ValueError("Enter the proposed monthly price you will charge. We do not invent it.")
    if not models:
        raise ValueError("Select at least one catalogued model you will use. We do not invent SKUs.")

    kept = (
        db.query(KeptJob)
        .filter(KeptJob.user_id == uid, KeptJob.job_key == job_key)
        .first()
    )
    payload = job if isinstance(job, dict) else (kept.job_payload if kept else {})
    ident = _job_identity(payload or {"job_key": job_key})
    if kept:
        ident["employer_name"] = kept.employer_name
        ident["work_title"] = kept.work_title
        ident["workplace"] = kept.workplace
    email = employer_email_from_job(payload) or (kept.employer_email if kept else None)
    robot = (robot_name or (kept.robot_name if kept else "") or "this robot").strip()
    poc_raw = (poc_evidence or "").strip()
    poc = poc_raw or (
        "skipped (employers prefer proof of concept)" if poc_skipped else "(not provided)"
    )
    snapshot = {
        "robot_name": robot,
        "selected_models": models,
        "poc_evidence": poc_raw,
        "poc_skipped": bool(poc_skipped),
        "monthly_price": price,
        "price_label": "proposed_offer",
        "job_key": ident["job_key"],
        "employer_name": ident["employer_name"],
        "work_title": ident["work_title"],
        "workplace": ident["workplace"],
        "employer_email": email,
    }
    reply_token = secrets.token_urlsafe(18)
    employer_token = secrets.token_urlsafe(18)
    reply_to = jobs_crm_reply_address(reply_token)
    from app.services.jobs_crm_recruiter import (
        attach_documents_to_application,
        document_lines_for_email,
        employer_decision_url,
        oem_email_for_user,
        notify_oem_status,
        resend_attachments_for,
        STATUS_APPLIED,
    )

    oem_email = oem_email_for_user(user, db)
    snapshot["document_ids"] = [str(x) for x in (document_ids or []) if str(x).strip()]
    snapshot["employer_token"] = employer_token
    decision = employer_decision_url(employer_token)
    application = JobApplication(
        user_id=uid,
        kept_job_id=kept.id if kept else None,
        job_key=ident["job_key"],
        employer_name=ident["employer_name"],
        work_title=ident["work_title"],
        workplace=ident["workplace"],
        robot_name=robot,
        selected_models=models,
        poc_evidence=poc_raw or None,
        poc_skipped="true" if poc_skipped else "false",
        monthly_price=price,
        offer_snapshot=snapshot,
        employer_email=email,
        send_status=SEND_STORED,
        reply_token=reply_token,
        reply_to=reply_to,
        thread_state=THREAD_DRAFT,
        employer_token=employer_token,
        status=STATUS_APPLIED,
        oem_email=oem_email,
    )
    db.add(application)
    db.flush()
    attached = attach_documents_to_application(db, user, application, document_ids)
    snapshot["documents"] = [
        {"id": str(doc.id), "filename": doc.original_name or doc.filename, "kind": doc.kind}
        for doc in attached
    ]
    application.offer_snapshot = snapshot
    subject, body = _compose_offer_email(
        robot_name=robot,
        models=models,
        poc=poc,
        monthly_price=price,
        employer=ident["employer_name"],
        work=ident["work_title"],
        workplace=ident["workplace"],
        accept_url=f"{decision}?action=accept",
        interview_url=f"{decision}?action=interview",
        document_lines=document_lines_for_email(employer_token, attached),
    )

    if kept:
        kept.acted_at = _now()
        kept.expires_at = None

    send_error = None
    if not email:
        application.send_status = SEND_NOT_SENT_NO_EMAIL
        application.send_error = _NO_EMAIL_REASON
        application.thread_state = THREAD_DRAFT
    elif send:
        try:
            from app.services.resend_email import ResendEmailError, send_email_via_resend

            result = send_email_via_resend(
                to_email=email,
                subject=subject,
                body_text=body,
                from_display_name="Ready For Robots Jobs",
                reply_to=reply_to,
                attachments=resend_attachments_for(attached) or None,
                idempotency_key=f"jobs-crm-apply/{application.id}",
            )
            application.send_status = SEND_SENT
            application.resend_id = result.get("resend_id")
            application.thread_state = THREAD_AWAITING
            db.add(
                ApplicationMessage(
                    application_id=application.id,
                    user_id=uid,
                    direction="outbound",
                    body=body,
                    subject=subject,
                    from_email=result.get("from_email") or os.getenv("RESEND_FROM_EMAIL"),
                    to_email=email,
                    provider_id=result.get("resend_id"),
                )
            )
        except Exception as exc:
            from app.services.resend_email import ResendEmailError

            send_error = str(exc)
            if not isinstance(exc, ResendEmailError):
                send_error = f"Outreach send failed: {exc}"
            application.send_status = SEND_FAILED
            application.send_error = send_error
            application.thread_state = THREAD_DRAFT
    else:
        application.send_status = SEND_STORED
        application.thread_state = THREAD_DRAFT

    record_activity(
        db,
        user,
        kind="apply",
        label="Applied",
        job_key=ident["job_key"],
        company=ident["employer_name"],
    )
    notify_oem_status(db, user, application, "applied")
    db.commit()
    db.refresh(application)
    return application_payload(application, include_messages=True)


def application_payload(row: JobApplication, *, include_messages: bool = False) -> dict[str, Any]:
    payload = {
        "id": str(row.id),
        "job_key": row.job_key,
        "employer_name": row.employer_name,
        "work_title": row.work_title,
        "workplace": row.workplace,
        "robot_name": row.robot_name,
        "selected_models": row.selected_models or [],
        "poc_evidence": row.poc_evidence,
        "poc_skipped": _truthy(row.poc_skipped),
        "monthly_price": row.monthly_price,
        "offer_snapshot": row.offer_snapshot or {},
        "employer_email": row.employer_email,
        "send_status": row.send_status,
        "send_error": row.send_error,
        "resend_id": row.resend_id,
        "reply_to": row.reply_to,
        "thread_state": row.thread_state,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "can_send": bool(row.employer_email),
        "no_email_reason": None if row.employer_email else _NO_EMAIL_REASON,
        "status": getattr(row, "status", None) or "applied",
        "interview_at": row.interview_at.isoformat() if getattr(row, "interview_at", None) else None,
        "interview_note": getattr(row, "interview_note", None),
        "interview_mode": getattr(row, "interview_mode", None),
        "oem_email": getattr(row, "oem_email", None),
        "employer_decision_url": None,
        "documents": (row.offer_snapshot or {}).get("documents") or [],
    }
    token = getattr(row, "employer_token", None)
    if token:
        from app.services.jobs_crm_recruiter import employer_decision_url

        payload["employer_decision_url"] = employer_decision_url(token)
    return payload


def get_application(db: Session, user: dict, application_id: str) -> JobApplication:
    row = (
        db.query(JobApplication)
        .filter(JobApplication.id == UUID(str(application_id)), JobApplication.user_id == _uid(user))
        .first()
    )
    if not row:
        raise KeyError("application_not_found")
    return row


def list_messages(db: Session, application_id: UUID) -> list[dict[str, Any]]:
    rows = (
        db.query(ApplicationMessage)
        .filter(ApplicationMessage.application_id == application_id)
        .order_by(ApplicationMessage.created_at.asc())
        .all()
    )
    return [
        {
            "id": str(row.id),
            "direction": row.direction,
            "body": row.body,
            "subject": row.subject,
            "from_email": row.from_email,
            "to_email": row.to_email,
            "provider_id": row.provider_id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


def application_with_thread(db: Session, user: dict, application_id: str) -> dict[str, Any]:
    row = get_application(db, user, application_id)
    payload = application_payload(row, include_messages=True)
    payload["messages"] = list_messages(db, row.id)
    from app.services.jobs_crm_recruiter import documents_for_application, document_payload

    payload["documents"] = [document_payload(doc) for doc in documents_for_application(db, row.id)]
    return payload


def reply_on_application(
    db: Session,
    user: dict,
    application_id: str,
    body: str,
) -> dict[str, Any]:
    row = get_application(db, user, application_id)
    text = (body or "").strip()
    if not text:
        raise ValueError("Reply body is required.")
    if not row.employer_email:
        raise ValueError(_NO_EMAIL_REASON)
    subject = f"Re: Applying {row.robot_name} to {row.work_title} at {row.employer_name}"
    from app.services.resend_email import ResendEmailError, send_email_via_resend

    try:
        result = send_email_via_resend(
            to_email=row.employer_email,
            subject=subject,
            body_text=text,
            from_display_name="Ready For Robots Jobs",
            reply_to=row.reply_to,
            idempotency_key=f"jobs-crm-reply/{row.id}/{secrets.token_urlsafe(8)}",
        )
    except ResendEmailError as exc:
        raise ValueError(str(exc)) from exc
    db.add(
        ApplicationMessage(
            application_id=row.id,
            user_id=_uid(user),
            direction="outbound",
            body=text,
            subject=subject,
            from_email=result.get("from_email") or os.getenv("RESEND_FROM_EMAIL"),
            to_email=row.employer_email,
            provider_id=result.get("resend_id"),
        )
    )
    if row.thread_state != THREAD_REPLIED:
        row.thread_state = THREAD_AWAITING
        row.send_status = SEND_SENT
    record_activity(
        db,
        user,
        kind="follow_up",
        label="Replied to employer",
        job_key=row.job_key,
        company=row.employer_name,
    )
    db.commit()
    return application_with_thread(db, user, application_id)


def paste_inbound_reply(
    db: Session,
    user: dict,
    application_id: str,
    *,
    body: str,
    from_email: str | None = None,
) -> dict[str, Any]:
    row = get_application(db, user, application_id)
    text = (body or "").strip()
    if not text:
        raise ValueError("Pasted reply body is required.")
    sender = normalize_recipient_email(from_email) or from_email or row.employer_email
    capture_inbound_message(
        db,
        row,
        body=text,
        from_email=sender,
        to_email=row.reply_to,
        subject=f"Re: Applying {row.robot_name} to {row.work_title}",
        provider_id=None,
    )
    record_activity(
        db,
        user,
        kind="follow_up",
        label="Employer reply stored",
        job_key=row.job_key,
        company=row.employer_name,
    )
    db.commit()
    return application_with_thread(db, user, application_id)


def capture_inbound_message(
    db: Session,
    application: JobApplication,
    *,
    body: str,
    from_email: str | None,
    to_email: str | None,
    subject: str | None,
    provider_id: str | None,
) -> ApplicationMessage:
    if provider_id:
        existing = (
            db.query(ApplicationMessage)
            .filter(ApplicationMessage.provider_id == provider_id)
            .first()
        )
        if existing:
            return existing
    msg = ApplicationMessage(
        application_id=application.id,
        user_id=application.user_id,
        direction="inbound",
        body=body or "",
        subject=subject,
        from_email=from_email,
        to_email=to_email,
        provider_id=provider_id,
    )
    db.add(msg)
    application.thread_state = THREAD_REPLIED
    return msg


def find_application_by_reply_token(db: Session, token: str) -> JobApplication | None:
    if not token:
        return None
    return db.query(JobApplication).filter(JobApplication.reply_token == token).first()
