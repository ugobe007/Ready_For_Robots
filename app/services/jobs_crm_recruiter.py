"""Jobs CRM recruiter extras: OEM specs, employer tokens, status emails.

Kept separate from keep/apply so the desk loop stays readable.
No invented employer emails. No Cal sales autonomy.
"""
from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.jobs_crm import (
    ApplicationDocument,
    ApplicationMessage,
    JobApplication,
    UserRobotDocument,
)
from app.models.user_profile import UserProfile
from app.services.email_address import normalize_recipient_email
from app.services.jobs_crm import (
    THREAD_REPLIED,
    application_with_thread,
    get_application,
    record_activity,
)

STATUS_APPLIED = "applied"
STATUS_ACCEPTED = "accepted"
STATUS_INTERVIEW_REQUESTED = "interview_requested"
STATUS_INTERVIEW_SCHEDULED = "interview_scheduled"
STATUS_INTERVIEW_HELD = "interview_held"
STATUS_INTERVIEW_CONFIRMED = "interview_confirmed"
STATUS_HOLD_RELEASED = "hold_released"
STATUS_DECLINED = "declined"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"

INTERVIEW_MODE_PROPOSED = "proposed_time"
INTERVIEW_MODE_CONNECT = "connect_you"
INTERVIEW_MODE_HOLD = "hold_slot"
HOLD_TTL_HOURS = 48
DEFAULT_SLOT_MINUTES = 60

# Task-model loop: why policy/job fit failed. Short list, not a novel.
DECLINE_REASON_WORK_MISMATCH = "work_mismatch"
DECLINE_REASON_MODEL_UNPROVEN = "model_unproven"
DECLINE_REASON_SITE_CONSTRAINTS = "site_constraints"
DECLINE_REASON_TIMING_BUDGET = "timing_budget"
DECLINE_REASON_OTHER = "other"
DECLINE_REASON_CODES = frozenset(
    {
        DECLINE_REASON_WORK_MISMATCH,
        DECLINE_REASON_MODEL_UNPROVEN,
        DECLINE_REASON_SITE_CONSTRAINTS,
        DECLINE_REASON_TIMING_BUDGET,
        DECLINE_REASON_OTHER,
    }
)
DECLINE_REASON_LABELS = {
    DECLINE_REASON_WORK_MISMATCH: "this robot cannot do this physical work",
    DECLINE_REASON_MODEL_UNPROVEN: "hardware maybe, task model / demo not convincing",
    DECLINE_REASON_SITE_CONSTRAINTS: "aisle, payload, SOP, safety, environment",
    DECLINE_REASON_TIMING_BUDGET: "not now / budget / contract",
    DECLINE_REASON_OTHER: "other",
}

_OPEN_FOR_ACCEPT = {
    STATUS_APPLIED,
    STATUS_INTERVIEW_REQUESTED,
    STATUS_INTERVIEW_SCHEDULED,
    STATUS_INTERVIEW_HELD,
}
_CLOSED_FOR_INTERVIEW = {STATUS_DECLINED, STATUS_SUCCESS, STATUS_FAILED}
_CLOSED_FOR_DECLINE = {STATUS_DECLINED, STATUS_SUCCESS, STATUS_FAILED}

ALLOWED_DOC_MIME = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)
ALLOWED_DOC_EXT = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}
MAX_DOC_BYTES = 8 * 1024 * 1024
MAX_DOCS_PER_USER = 20
RESEND_ATTACH_BUDGET = 3 * 1024 * 1024


def public_site_base() -> str:
    return (
        os.getenv("PUBLIC_SITE_URL")
        or os.getenv("JOBS_PUBLIC_SITE_URL")
        or "https://readyforrobots.com"
    ).rstrip("/")


def public_api_base() -> str:
    return (
        os.getenv("PUBLIC_API_URL")
        or os.getenv("JOBS_PUBLIC_API_URL")
        or "https://ready-2-robot.fly.dev"
    ).rstrip("/")


def upload_root() -> Path:
    return Path(os.getenv("JOBS_CRM_UPLOAD_DIR") or "uploads/jobs_crm").resolve()


def _uid(user: dict) -> UUID:
    return UUID(str(user["uid"]))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def oem_email_for_user(user: dict, db: Session | None = None) -> Optional[str]:
    hit = normalize_recipient_email(str(user.get("email") or ""))
    if hit:
        return hit
    if db is None:
        return None
    try:
        profile = db.query(UserProfile).filter(UserProfile.id == _uid(user)).first()
    except Exception:
        return None
    if not profile:
        return None
    return normalize_recipient_email(str(profile.email or ""))


def employer_decision_url(token: str) -> str:
    return f"{public_site_base()}/employer/{token}"


def oem_hold_url(token: str) -> str:
    return f"{public_site_base()}/oem-hold/{token}"


def _iso(stamp: datetime | None) -> str | None:
    return stamp.isoformat() if stamp else None


def decline_reason_label(code: str | None) -> str:
    cleaned = (code or "").strip().lower()
    if not cleaned:
        return ""
    return DECLINE_REASON_LABELS.get(cleaned, cleaned.replace("_", " "))


def decline_fields_for_payload(row: JobApplication) -> dict[str, Any]:
    status = row.status or STATUS_APPLIED
    code = getattr(row, "decline_reason_code", None)
    return {
        "decline_reason_code": code,
        "decline_reason_label": decline_reason_label(code) if code else None,
        "decline_note": getattr(row, "decline_note", None),
        "can_decline": status not in _CLOSED_FOR_DECLINE,
    }


def slot_window_label(application: JobApplication) -> str | None:
    start = getattr(application, "slot_start", None) or getattr(application, "interview_at", None)
    end = getattr(application, "slot_end", None)
    if start and end:
        return (
            f"{start.strftime('%Y-%m-%d %H:%M UTC')} – {end.strftime('%Y-%m-%d %H:%M UTC')}"
        )
    if start:
        return start.strftime("%Y-%m-%d %H:%M UTC")
    return None


def hold_fields_for_payload(
    row: JobApplication,
    *,
    include_hold_url: bool = True,
) -> dict[str, Any]:
    status = row.status or STATUS_APPLIED
    held = status == STATUS_INTERVIEW_HELD
    token = getattr(row, "oem_hold_token", None)
    fields: dict[str, Any] = {
        "held_at": _iso(getattr(row, "held_at", None)),
        "hold_expires_at": _iso(getattr(row, "hold_expires_at", None)),
        "slot_start": _iso(getattr(row, "slot_start", None)),
        "slot_end": _iso(getattr(row, "slot_end", None)),
        "slot_label": slot_window_label(row),
        "can_confirm_hold": held,
        "can_release_hold": held,
    }
    if include_hold_url:
        fields["hold_url"] = oem_hold_url(token) if token else None
    return fields


def employer_doc_url(token: str, document_id: str) -> str:
    return f"{public_api_base()}/api/jobs-crm/employer/{token}/documents/{document_id}/file"


def _safe_filename(name: str) -> str:
    base = Path(name or "upload.bin").name
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in base)[:160]
    return cleaned or "upload.bin"


def infer_doc_mime(filename: str, declared: str | None) -> Optional[str]:
    declared_clean = (declared or "").split(";", 1)[0].strip().lower()
    if declared_clean in ALLOWED_DOC_MIME:
        return declared_clean
    ext = Path(filename or "").suffix.lower()
    return ALLOWED_DOC_EXT.get(ext)


def document_payload(row: UserRobotDocument) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "filename": row.original_name or row.filename,
        "mime_type": row.mime_type,
        "size_bytes": int(row.size_bytes or 0),
        "kind": row.kind,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def list_user_documents(db: Session, user: dict) -> list[dict[str, Any]]:
    rows = (
        db.query(UserRobotDocument)
        .filter(UserRobotDocument.user_id == _uid(user))
        .order_by(UserRobotDocument.created_at.desc())
        .all()
    )
    return [document_payload(row) for row in rows]


def store_user_document(
    db: Session,
    user: dict,
    *,
    filename: str,
    content: bytes,
    mime_type: str | None,
    kind: str = "spec",
) -> dict[str, Any]:
    if not content:
        raise ValueError("Upload a brochure or product spec file.")
    if len(content) > MAX_DOC_BYTES:
        raise ValueError("File is too large. Cap is 8 MB per brochure or spec.")
    mime = infer_doc_mime(filename, mime_type)
    if not mime:
        raise ValueError("Upload a PDF or image spec (PDF, JPEG, PNG, WebP, GIF).")
    uid = _uid(user)
    existing = (
        db.query(UserRobotDocument).filter(UserRobotDocument.user_id == uid).count()
    )
    if existing >= MAX_DOCS_PER_USER:
        raise ValueError(f"Account document cap is {MAX_DOCS_PER_USER}. Remove one to upload another.")
    kind_clean = (kind or "spec").strip().lower()
    if kind_clean not in {"brochure", "spec", "other"}:
        kind_clean = "spec"
    doc_id = secrets.token_hex(8)
    safe = _safe_filename(filename)
    folder = upload_root() / str(uid)
    folder.mkdir(parents=True, exist_ok=True)
    stored_name = f"{doc_id}_{safe}"
    path = folder / stored_name
    path.write_bytes(content)
    row = UserRobotDocument(
        user_id=uid,
        filename=stored_name,
        original_name=safe,
        mime_type=mime,
        size_bytes=len(content),
        storage_path=str(path),
        kind=kind_clean,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return document_payload(row)


def get_user_document(db: Session, user: dict, document_id: str) -> UserRobotDocument:
    row = (
        db.query(UserRobotDocument)
        .filter(UserRobotDocument.id == UUID(str(document_id)), UserRobotDocument.user_id == _uid(user))
        .first()
    )
    if not row:
        raise KeyError("document_not_found")
    return row


def attach_documents_to_application(
    db: Session,
    user: dict,
    application: JobApplication,
    document_ids: list[str] | None,
) -> list[UserRobotDocument]:
    attached: list[UserRobotDocument] = []
    seen: set[str] = set()
    for raw in document_ids or []:
        key = str(raw or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        try:
            doc = get_user_document(db, user, key)
        except (KeyError, ValueError):
            continue
        db.add(ApplicationDocument(application_id=application.id, document_id=doc.id))
        attached.append(doc)
    return attached


def documents_for_application(db: Session, application_id: UUID) -> list[UserRobotDocument]:
    return (
        db.query(UserRobotDocument)
        .join(ApplicationDocument, ApplicationDocument.document_id == UserRobotDocument.id)
        .filter(ApplicationDocument.application_id == application_id)
        .order_by(UserRobotDocument.created_at.asc())
        .all()
    )


def resend_attachments_for(docs: list[UserRobotDocument]) -> list[dict[str, Any]]:
    """Small files can ride along; larger ones stay as hosted token URLs."""
    out: list[dict[str, Any]] = []
    budget = 0
    for doc in docs:
        path = Path(doc.storage_path)
        if not path.is_file():
            continue
        size = int(doc.size_bytes or path.stat().st_size)
        if budget + size > RESEND_ATTACH_BUDGET:
            continue
        try:
            import base64

            payload = base64.b64encode(path.read_bytes()).decode("ascii")
        except OSError:
            continue
        out.append({"filename": doc.original_name or doc.filename, "content": payload})
        budget += size
    return out


def document_lines_for_email(token: str, docs: list[UserRobotDocument]) -> list[str]:
    if not docs:
        return []
    lines = ["Specs / brochures attached to this application:"]
    for doc in docs:
        lines.append(f"- {doc.original_name or doc.filename}: {employer_doc_url(token, str(doc.id))}")
    return lines


def find_application_by_employer_token(db: Session, token: str) -> JobApplication | None:
    cleaned = (token or "").strip()
    if not cleaned:
        return None
    return db.query(JobApplication).filter(JobApplication.employer_token == cleaned).first()


def employer_public_payload(db: Session, row: JobApplication) -> dict[str, Any]:
    docs = documents_for_application(db, row.id)
    status = row.status or STATUS_APPLIED
    payload = {
        "employer_name": row.employer_name,
        "work_title": row.work_title,
        "workplace": row.workplace,
        "robot_name": row.robot_name,
        "selected_models": row.selected_models or [],
        "monthly_price": row.monthly_price,
        "poc_evidence": row.poc_evidence,
        "poc_video_url": getattr(row, "poc_video_url", None),
        "status": status,
        "interview_at": row.interview_at.isoformat() if row.interview_at else None,
        "interview_mode": row.interview_mode,
        "documents": [
            {
                "id": str(doc.id),
                "filename": doc.original_name or doc.filename,
                "kind": doc.kind,
            }
            for doc in docs
        ],
        "can_accept": status in _OPEN_FOR_ACCEPT,
        "can_interview": status not in _CLOSED_FOR_INTERVIEW,
        "can_hold": status not in _CLOSED_FOR_INTERVIEW,
    }
    payload.update(hold_fields_for_payload(row, include_hold_url=False))
    payload.update(decline_fields_for_payload(row))
    return payload


def find_application_by_oem_hold_token(db: Session, token: str) -> JobApplication | None:
    cleaned = (token or "").strip()
    if not cleaned:
        return None
    return db.query(JobApplication).filter(JobApplication.oem_hold_token == cleaned).first()


def oem_hold_public_payload(db: Session, row: JobApplication) -> dict[str, Any]:
    del db
    status = row.status or STATUS_APPLIED
    return {
        "employer_name": row.employer_name,
        "work_title": row.work_title,
        "workplace": row.workplace,
        "robot_name": row.robot_name,
        "status": status,
        "interview_note": row.interview_note,
        **hold_fields_for_payload(row, include_hold_url=False),
    }


def _add_system_message(
    db: Session,
    application: JobApplication,
    *,
    body: str,
    direction: str = "inbound",
    from_email: str | None = None,
    to_email: str | None = None,
    subject: str | None = None,
) -> ApplicationMessage:
    msg = ApplicationMessage(
        application_id=application.id,
        user_id=application.user_id,
        direction=direction,
        body=body,
        subject=subject,
        from_email=from_email,
        to_email=to_email,
    )
    db.add(msg)
    return msg


def notify_oem_status(
    db: Session,
    user: dict | None,
    application: JobApplication,
    event: str,
    *,
    extra_lines: list[str] | None = None,
) -> dict[str, Any]:
    """Recruiter posture: confirm each application status to the OEM account email."""
    email = application.oem_email
    if not email and user:
        email = oem_email_for_user(user, db)
    if not email:
        return {"sent": False, "reason": "no_oem_email"}
    subject, body = compose_oem_status_email(application, event, extra_lines=extra_lines)
    try:
        from app.services.resend_email import ResendEmailError, send_email_via_resend

        result = send_email_via_resend(
            to_email=email,
            subject=subject,
            body_text=body,
            from_display_name="Ready For Robots Jobs",
            idempotency_key=f"jobs-crm-oem/{application.id}/{event}/{secrets.token_urlsafe(6)}",
        )
    except Exception as exc:
        from app.services.resend_email import ResendEmailError

        reason = str(exc)
        if not isinstance(exc, ResendEmailError):
            reason = f"OEM status email failed: {exc}"
        return {"sent": False, "reason": reason}
    _add_system_message(
        db,
        application,
        body=body,
        direction="outbound",
        from_email=result.get("from_email") or os.getenv("RESEND_FROM_EMAIL"),
        to_email=email,
        subject=subject,
    )
    return {"sent": True, "resend_id": result.get("resend_id"), "to": email}


def compose_oem_status_email(
    application: JobApplication,
    event: str,
    *,
    extra_lines: list[str] | None = None,
) -> tuple[str, str]:
    label = {
        "applied": "applied",
        "accepted": "accepted by the employer",
        "interview_requested": "interview requested",
        "interview_scheduled": "interview time proposed",
        "interview_held": "slot held",
        "interview_confirmed": "interview confirmed",
        "hold_released": "held slot released",
        "success": "marked success",
        "failed": "marked unsuccessful",
        "declined": "declined",
    }.get(event, event.replace("_", " "))
    subject = f"Application update: {application.work_title} at {application.employer_name} — {label}"
    when = slot_window_label(application)
    lines = [
        f"This is a recruiter confirmation for your robot company account.",
        "",
        f"Job: {application.work_title}",
        f"Employer: {application.employer_name}",
        f"Robot: {application.robot_name}",
        f"Status: {label}",
    ]
    if event == STATUS_INTERVIEW_HELD and when:
        lines.append(f"Slot held for {application.employer_name} {application.work_title} {when}")
    elif when:
        lines.append(f"Interview time: {when}")
    if application.interview_mode == INTERVIEW_MODE_CONNECT:
        lines.append("The employer asked us to connect you. Reply to arrange the meeting.")
    if application.interview_mode == INTERVIEW_MODE_HOLD and event == STATUS_INTERVIEW_HELD:
        lines.append("This is a held meeting window on the application — not Cal sales autonomy.")
    if event == STATUS_DECLINED:
        code = getattr(application, "decline_reason_code", None)
        if code:
            lines.append(f"Decline reason: {decline_reason_label(code)} ({code})")
        note = getattr(application, "decline_note", None)
        if note:
            lines.append(f"Decline note: {note}")
    if application.interview_note:
        lines.append(f"Note: {application.interview_note}")
    if extra_lines:
        lines.extend(["", *extra_lines])
    lines.extend(
        [
            "",
            "Open CRM to see the thread and next action.",
            f"{public_site_base()}/pipeline?src=jobs_activate",
        ]
    )
    return subject, "\n".join(lines)


def accept_application(db: Session, token: str) -> dict[str, Any]:
    row = find_application_by_employer_token(db, token)
    if not row:
        raise KeyError("application_not_found")
    if row.status in {STATUS_DECLINED, STATUS_FAILED}:
        raise ValueError("This application is no longer open.")
    row.status = STATUS_ACCEPTED
    row.thread_state = THREAD_REPLIED
    body = (
        f"{row.employer_name} accepted the application for {row.robot_name} "
        f"on {row.work_title}."
    )
    _add_system_message(
        db,
        row,
        body=body,
        from_email=row.employer_email,
        subject="Application accepted",
    )
    record_activity(
        db,
        {"uid": str(row.user_id)},
        kind="follow_up",
        label="Employer accepted",
        job_key=row.job_key,
        company=row.employer_name,
    )
    notify_oem_status(db, None, row, STATUS_ACCEPTED)
    db.commit()
    return employer_public_payload(db, row)


def decline_application(
    db: Session,
    token: str,
    *,
    reason_code: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    row = find_application_by_employer_token(db, token)
    if not row:
        raise KeyError("application_not_found")
    if row.status in _CLOSED_FOR_DECLINE:
        raise ValueError("This application is no longer open.")
    code = (reason_code or "").strip().lower()
    if code not in DECLINE_REASON_CODES:
        raise ValueError("Pick a decline reason.")
    note_clean = (note or "").strip()[:2000] or None
    if code == DECLINE_REASON_OTHER and not note_clean:
        raise ValueError("Add a short note when the reason is other.")
    row.status = STATUS_DECLINED
    row.decline_reason_code = code
    row.decline_note = note_clean
    row.thread_state = THREAD_REPLIED
    label = decline_reason_label(code)
    body = (
        f"{row.employer_name} declined the application for {row.robot_name} "
        f"on {row.work_title}. Reason: {label} ({code})."
    )
    if note_clean:
        body = f"{body}\n\nNote: {note_clean}"
    _add_system_message(
        db,
        row,
        body=body,
        from_email=row.employer_email,
        subject="Application declined",
    )
    record_activity(
        db,
        {"uid": str(row.user_id)},
        kind="follow_up",
        label=f"Employer declined ({code})",
        job_key=row.job_key,
        company=row.employer_name,
    )
    notify_oem_status(db, None, row, STATUS_DECLINED)
    db.commit()
    return employer_public_payload(db, row)


def request_interview(
    db: Session,
    token: str,
    *,
    proposed_at: str | None = None,
    note: str | None = None,
    connect_you: bool = False,
) -> dict[str, Any]:
    row = find_application_by_employer_token(db, token)
    if not row:
        raise KeyError("application_not_found")
    if row.status in {STATUS_DECLINED, STATUS_SUCCESS, STATUS_FAILED}:
        raise ValueError("This application is no longer open for interview.")
    stamp = _parse_proposed_at(proposed_at)
    note_clean = (note or "").strip()[:2000] or None
    if stamp:
        row.status = STATUS_INTERVIEW_SCHEDULED
        row.interview_at = stamp
        row.interview_mode = INTERVIEW_MODE_PROPOSED
        row.slot_start = None
        row.slot_end = None
        row.held_at = None
        row.hold_expires_at = None
        when_label = stamp.strftime("%Y-%m-%d %H:%M UTC")
        body = (
            f"{row.employer_name} proposed an interview for {row.work_title} "
            f"with {row.robot_name} at {when_label}."
        )
        event = STATUS_INTERVIEW_SCHEDULED
    else:
        row.status = STATUS_INTERVIEW_REQUESTED
        row.interview_mode = INTERVIEW_MODE_CONNECT
        row.slot_start = None
        row.slot_end = None
        row.held_at = None
        row.hold_expires_at = None
        body = (
            f"{row.employer_name} asked Ready For Robots to connect them with "
            f"the robot company for {row.work_title}."
        )
        event = STATUS_INTERVIEW_REQUESTED
        when_label = None
    row.interview_note = note_clean
    row.thread_state = THREAD_REPLIED
    if note_clean:
        body = f"{body}\n\nNote: {note_clean}"
    _add_system_message(
        db,
        row,
        body=body,
        from_email=row.employer_email,
        subject="Interview requested",
    )
    extra = []
    if when_label:
        extra.append(f"Please confirm this time with the employer, or reply to rearrange.")
        extra.append(f"Proposed: {when_label}")
    else:
        extra.append("The employer did not pick a time. Arrange the 1-to-1 and confirm back.")
    notify_oem_status(db, None, row, event, extra_lines=extra)
    if row.employer_email and row.oem_email:
        _email_interview_both_sides(row, when_label)
    record_activity(
        db,
        {"uid": str(row.user_id)},
        kind="follow_up",
        label="Interview requested" if event == STATUS_INTERVIEW_REQUESTED else "Interview scheduled",
        job_key=row.job_key,
        company=row.employer_name,
    )
    db.commit()
    return employer_public_payload(db, row)


def hold_slot(
    db: Session,
    token: str,
    *,
    slot_start: str | None,
    slot_end: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    row = find_application_by_employer_token(db, token)
    if not row:
        raise KeyError("application_not_found")
    if row.status in _CLOSED_FOR_INTERVIEW:
        raise ValueError("This application is no longer open for interview.")
    start = _parse_proposed_at(slot_start)
    if not start:
        raise ValueError("Pick a start time to hold this slot.")
    end = _parse_proposed_at(slot_end)
    if end is None:
        end = start + timedelta(minutes=DEFAULT_SLOT_MINUTES)
    if end <= start:
        raise ValueError("The slot must end after it starts.")
    now = _now()
    note_clean = (note or "").strip()[:2000] or None
    row.status = STATUS_INTERVIEW_HELD
    row.interview_mode = INTERVIEW_MODE_HOLD
    row.interview_at = start
    row.slot_start = start
    row.slot_end = end
    row.held_at = now
    row.hold_expires_at = now + timedelta(hours=HOLD_TTL_HOURS)
    row.interview_note = note_clean
    row.thread_state = THREAD_REPLIED
    if not row.oem_hold_token:
        row.oem_hold_token = secrets.token_urlsafe(18)
    when_label = slot_window_label(row) or start.strftime("%Y-%m-%d %H:%M UTC")
    body = (
        f"{row.employer_name} held an interview slot for {row.work_title} "
        f"with {row.robot_name}: {when_label}."
    )
    if note_clean:
        body = f"{body}\n\nNote: {note_clean}"
    _add_system_message(
        db,
        row,
        body=body,
        from_email=row.employer_email,
        subject="Interview slot held",
    )
    hold_link = oem_hold_url(row.oem_hold_token)
    extra = [
        f"Slot held for {row.employer_name} {row.work_title} {when_label}.",
        "Confirm or release this hold. We treat the hold as the booked meeting until you release it.",
        f"Confirm or release: {hold_link}",
    ]
    notify_oem_status(db, None, row, STATUS_INTERVIEW_HELD, extra_lines=extra)
    if row.employer_email and row.oem_email:
        _email_interview_both_sides(row, when_label, kind="held", hold_url=hold_link)
    record_activity(
        db,
        {"uid": str(row.user_id)},
        kind="follow_up",
        label="Interview slot held",
        job_key=row.job_key,
        company=row.employer_name,
    )
    db.commit()
    return employer_public_payload(db, row)


def confirm_hold(db: Session, user: dict, application_id: str) -> dict[str, Any]:
    row = get_application(db, user, application_id)
    _confirm_hold_row(db, row, user=user)
    db.commit()
    return application_with_thread(db, user, application_id)


def release_hold(db: Session, user: dict, application_id: str) -> dict[str, Any]:
    row = get_application(db, user, application_id)
    _release_hold_row(db, row, user=user)
    db.commit()
    return application_with_thread(db, user, application_id)


def confirm_hold_by_token(db: Session, token: str) -> dict[str, Any]:
    row = find_application_by_oem_hold_token(db, token)
    if not row:
        raise KeyError("application_not_found")
    _confirm_hold_row(db, row, user={"uid": str(row.user_id), "email": row.oem_email})
    db.commit()
    return oem_hold_public_payload(db, row)


def release_hold_by_token(db: Session, token: str) -> dict[str, Any]:
    row = find_application_by_oem_hold_token(db, token)
    if not row:
        raise KeyError("application_not_found")
    _release_hold_row(db, row, user={"uid": str(row.user_id), "email": row.oem_email})
    db.commit()
    return oem_hold_public_payload(db, row)


def _require_held_slot(row: JobApplication) -> None:
    held = (row.status or "") == STATUS_INTERVIEW_HELD or row.interview_mode == INTERVIEW_MODE_HOLD
    if not held or not (row.slot_start or row.interview_at):
        raise ValueError("No held slot on this application.")


def _confirm_hold_row(db: Session, row: JobApplication, *, user: dict | None) -> None:
    _require_held_slot(row)
    row.status = STATUS_INTERVIEW_CONFIRMED
    if row.slot_start:
        row.interview_at = row.slot_start
    when = slot_window_label(row) or "to be arranged"
    _add_system_message(
        db,
        row,
        body=f"Robot company confirmed the held slot ({when}).",
        direction="outbound",
        to_email=row.employer_email,
        subject="Interview hold confirmed",
    )
    notify_oem_status(
        db,
        user,
        row,
        STATUS_INTERVIEW_CONFIRMED,
        extra_lines=[f"Confirmed held window: {when}"],
    )
    if row.employer_email and row.oem_email:
        _email_interview_both_sides(row, when if (row.slot_start or row.interview_at) else None, kind="confirmed")
    record_activity(
        db,
        user or {"uid": str(row.user_id)},
        kind="follow_up",
        label="Interview hold confirmed",
        job_key=row.job_key,
        company=row.employer_name,
    )


def _release_hold_row(db: Session, row: JobApplication, *, user: dict | None) -> None:
    _require_held_slot(row)
    when = slot_window_label(row)
    row.status = STATUS_APPLIED
    row.interview_mode = None
    row.interview_at = None
    row.slot_start = None
    row.slot_end = None
    row.held_at = None
    row.hold_expires_at = None
    body = "Robot company released the held interview slot."
    if when:
        body = f"{body} Previous window: {when}."
    _add_system_message(
        db,
        row,
        body=body,
        direction="outbound",
        to_email=row.employer_email,
        subject="Interview hold released",
    )
    extra = ["The held window is released. The employer can propose or hold a new time."]
    if when:
        extra.append(f"Released window: {when}")
    notify_oem_status(db, user, row, STATUS_HOLD_RELEASED, extra_lines=extra)
    if row.employer_email and row.oem_email:
        _email_interview_both_sides(row, when, kind="released")
    record_activity(
        db,
        user or {"uid": str(row.user_id)},
        kind="follow_up",
        label="Interview hold released",
        job_key=row.job_key,
        company=row.employer_name,
    )


def confirm_interview(db: Session, user: dict, application_id: str) -> dict[str, Any]:
    row = get_application(db, user, application_id)
    if (
        not row.interview_at
        and row.interview_mode not in {INTERVIEW_MODE_CONNECT, INTERVIEW_MODE_HOLD}
        and not getattr(row, "slot_start", None)
    ):
        raise ValueError("No interview time is on this application yet.")
    row.status = STATUS_INTERVIEW_CONFIRMED
    when = (
        row.interview_at.strftime("%Y-%m-%d %H:%M UTC")
        if row.interview_at
        else "to be arranged"
    )
    _add_system_message(
        db,
        row,
        body=f"Robot company confirmed the interview ({when}).",
        direction="outbound",
        to_email=row.employer_email,
        subject="Interview confirmed",
    )
    notify_oem_status(
        db,
        user,
        row,
        STATUS_INTERVIEW_CONFIRMED,
        extra_lines=[f"Confirmed time/date: {when}"],
    )
    if row.employer_email:
        _email_interview_both_sides(row, when if row.interview_at else None, confirmed=True)
    record_activity(
        db,
        user,
        kind="follow_up",
        label="Interview confirmed",
        job_key=row.job_key,
        company=row.employer_name,
    )
    db.commit()
    return application_with_thread(db, user, application_id)


def mark_application_outcome(
    db: Session,
    user: dict,
    application_id: str,
    outcome: str,
) -> dict[str, Any]:
    row = get_application(db, user, application_id)
    cleaned = (outcome or "").strip().lower()
    if cleaned not in {STATUS_SUCCESS, STATUS_FAILED}:
        raise ValueError("Outcome must be success or failed. Do not invent a placement.")
    row.status = cleaned
    label = "Interview / placement succeeded" if cleaned == STATUS_SUCCESS else "Interview / placement unsuccessful"
    _add_system_message(
        db,
        row,
        body=label,
        direction="outbound",
        subject=label,
    )
    notify_oem_status(db, user, row, cleaned)
    record_activity(
        db,
        user,
        kind="follow_up",
        label=label,
        job_key=row.job_key,
        company=row.employer_name,
    )
    db.commit()
    return application_with_thread(db, user, application_id)


def _parse_proposed_at(raw: str | None) -> datetime | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        stamp = datetime.fromisoformat(text)
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)


def _email_interview_both_sides(
    row: JobApplication,
    when_label: str | None,
    *,
    confirmed: bool = False,
    kind: str | None = None,
    hold_url: str | None = None,
) -> None:
    if not row.employer_email or not row.oem_email:
        return
    verb = kind or ("confirmed" if confirmed else "proposed")
    subject = f"Interview {verb}: {row.work_title} at {row.employer_name}"
    if verb == "held":
        subject = f"Interview slot held: {row.work_title} at {row.employer_name}"
    elif verb == "released":
        subject = f"Interview hold released: {row.work_title} at {row.employer_name}"
    lines = [
        f"Ready For Robots is connecting {row.employer_name} with the robot company for {row.work_title}.",
        "",
        f"Robot: {row.robot_name}",
    ]
    if verb == "held" and when_label:
        lines.append(f"Slot held for {row.employer_name} {row.work_title} {when_label}")
    elif when_label:
        lines.append(f"Time/date: {when_label}")
    else:
        lines.append("Time/date: we will confirm after both sides reply.")
    if row.interview_note:
        lines.append(f"Note: {row.interview_note}")
    if verb == "held" and hold_url:
        lines.append(f"Robot company: confirm or release this hold at {hold_url}")
    lines.extend(
        [
            "",
            "This is a 1-to-1 between the robot company and the employer.",
            "Reply-all (or reply to us) to lock the meeting. We do not run Cal sales autonomy here.",
        ]
    )
    try:
        from app.services.resend_email import send_email_via_resend

        send_email_via_resend(
            to_email=[row.oem_email, row.employer_email],
            subject=subject,
            body_text="\n".join(lines),
            from_display_name="Ready For Robots Jobs",
            idempotency_key=f"jobs-crm-interview/{row.id}/{verb}/{secrets.token_urlsafe(4)}",
        )
    except Exception:
        return


def enrich_application_payload(
    db: Session,
    row: JobApplication,
    payload: dict[str, Any],
) -> dict[str, Any]:
    docs = documents_for_application(db, row.id)
    payload["status"] = row.status or STATUS_APPLIED
    payload["interview_at"] = row.interview_at.isoformat() if row.interview_at else None
    payload["interview_note"] = row.interview_note
    payload["interview_mode"] = row.interview_mode
    payload["oem_email"] = row.oem_email
    payload["employer_decision_url"] = (
        employer_decision_url(row.employer_token) if row.employer_token else None
    )
    payload.update(hold_fields_for_payload(row))
    payload.update(decline_fields_for_payload(row))
    payload["documents"] = [document_payload(doc) for doc in docs]
    return payload
