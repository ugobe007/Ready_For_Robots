"""Jobs CRM recruiter extras: OEM specs, employer tokens, status emails.

Kept separate from keep/apply so the desk loop stays readable.
No invented employer emails. No Cal sales autonomy.
"""
from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
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
STATUS_INTERVIEW_CONFIRMED = "interview_confirmed"
STATUS_DECLINED = "declined"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"

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
    return {
        "employer_name": row.employer_name,
        "work_title": row.work_title,
        "workplace": row.workplace,
        "robot_name": row.robot_name,
        "selected_models": row.selected_models or [],
        "monthly_price": row.monthly_price,
        "status": row.status or STATUS_APPLIED,
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
        "can_accept": (row.status or STATUS_APPLIED)
        in {STATUS_APPLIED, STATUS_INTERVIEW_REQUESTED, STATUS_INTERVIEW_SCHEDULED},
        "can_interview": (row.status or STATUS_APPLIED)
        not in {STATUS_DECLINED, STATUS_SUCCESS, STATUS_FAILED},
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
        "interview_confirmed": "interview confirmed",
        "success": "marked success",
        "failed": "marked unsuccessful",
        "declined": "declined",
    }.get(event, event.replace("_", " "))
    subject = f"Application update: {application.work_title} at {application.employer_name} — {label}"
    when = (
        application.interview_at.strftime("%Y-%m-%d %H:%M UTC")
        if application.interview_at
        else None
    )
    lines = [
        f"This is a recruiter confirmation for your robot company account.",
        "",
        f"Job: {application.work_title}",
        f"Employer: {application.employer_name}",
        f"Robot: {application.robot_name}",
        f"Status: {label}",
    ]
    if when:
        lines.append(f"Interview time: {when}")
    if application.interview_mode == "connect_you":
        lines.append("The employer asked us to connect you. Reply to arrange the meeting.")
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
        row.interview_mode = "proposed_time"
        when_label = stamp.strftime("%Y-%m-%d %H:%M UTC")
        body = (
            f"{row.employer_name} proposed an interview for {row.work_title} "
            f"with {row.robot_name} at {when_label}."
        )
        event = STATUS_INTERVIEW_SCHEDULED
    else:
        row.status = STATUS_INTERVIEW_REQUESTED
        row.interview_mode = "connect_you"
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


def confirm_interview(db: Session, user: dict, application_id: str) -> dict[str, Any]:
    row = get_application(db, user, application_id)
    if not row.interview_at and row.interview_mode != "connect_you":
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
) -> None:
    if not row.employer_email or not row.oem_email:
        return
    verb = "confirmed" if confirmed else "proposed"
    subject = f"Interview {verb}: {row.work_title} at {row.employer_name}"
    lines = [
        f"Ready For Robots is connecting {row.employer_name} with the robot company for {row.work_title}.",
        "",
        f"Robot: {row.robot_name}",
    ]
    if when_label:
        lines.append(f"Time/date: {when_label}")
    else:
        lines.append("Time/date: we will confirm after both sides reply.")
    if row.interview_note:
        lines.append(f"Note: {row.interview_note}")
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
    payload["documents"] = [document_payload(doc) for doc in docs]
    return payload
