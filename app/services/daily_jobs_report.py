"""Daily top-25 Robot Jobs report — operator email + admin list.

Named employers and real work only. Not SIGNAL buyers. No paid LLM.
"""
from __future__ import annotations

import html
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import case, desc
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

TOP_N = 25
POOL = 200
DEFAULT_RECIPIENT = "ugobe07@gmail.com"
_SITE = (os.getenv("PUBLIC_SITE_URL") or "https://readyforrobots.com").rstrip("/")
_REDIS_SENT_KEY = "jobs:daily_report:last_sent_date"
_REDIS_PAYLOAD_KEY = "jobs:daily_report:latest"


def get_daily_jobs_report_recipients() -> list[str]:
    extra = _split_emails(os.getenv("DAILY_JOBS_REPORT_EMAIL") or "")
    emails: list[str] = []
    seen: set[str] = set()
    for email in [DEFAULT_RECIPIENT, *extra]:
        key = email.lower()
        if key in seen:
            continue
        seen.add(key)
        emails.append(email)
    return emails


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


def _claim_report_day(day: str) -> bool:
    client = _redis_client()
    if not client:
        return True
    try:
        # Try to claim with NX first (key doesn't exist)
        if client.set(_REDIS_SENT_KEY, day, nx=True, ex=60 * 60 * 48):
            return True
        # Key exists; check if it's a stale day
        current = str(client.get(_REDIS_SENT_KEY) or "")
        if current != day:
            # Stale day; claim the new day
            client.set(_REDIS_SENT_KEY, day, ex=60 * 60 * 48)
            return True
        # Already sent for this day
        return False
    except Exception:
        return True


def _release_report_day(day: str) -> None:
    client = _redis_client()
    if not client:
        return
    try:
        current = str(client.get(_REDIS_SENT_KEY) or "")
        if current == day:
            client.delete(_REDIS_SENT_KEY)
    except Exception:
        pass


def _mark_report_sent(day: str, payload: dict[str, Any]) -> None:
    client = _redis_client()
    if not client:
        return
    try:
        client.set(_REDIS_SENT_KEY, day, ex=60 * 60 * 48)
        client.set(_REDIS_PAYLOAD_KEY, json.dumps(payload), ex=60 * 60 * 48)
    except Exception:
        pass


def last_sent_day() -> Optional[str]:
    client = _redis_client()
    if not client:
        return None
    try:
        raw = client.get(_REDIS_SENT_KEY)
        return str(raw) if raw else None
    except Exception:
        return None


def _serialize_job(row: Any, rank: int) -> dict[str, Any]:
    title = str(getattr(row, "robot_compatible_task", "") or "").strip()
    action = str(getattr(row, "action", "") or "").strip()
    if not title:
        title = action.replace("_", " ") or "Operational work"
    created = getattr(row, "created_at", None)
    return {
        "rank": rank,
        "job_key": str(getattr(row, "job_key", "") or ""),
        "employer": str(getattr(row, "company_name", "") or "").strip(),
        "title": title,
        "locality": str(getattr(row, "locality", "") or "").strip(),
        "action": action,
        "investigate_status": str(getattr(row, "investigate_status", "") or ""),
        "created_at": created.isoformat() if created else None,
        "apply_url": str(getattr(row, "apply_url", "") or "").strip() or None,
    }


def compose_daily_jobs_report(db: Session, *, limit: int = TOP_N) -> dict[str, Any]:
    """Rank named-employer Robot Jobs the same way FIND accepts them."""
    from app.models.robot_directed_discovery import RobotJob
    from app.services.robot_job_extract import is_job_employer_name
    from app.services.robot_requirement_match import is_named_robot_job

    cap = max(1, min(int(limit), 50))
    day_label = datetime.now(timezone.utc).date().isoformat()
    status_rank = case(
        (RobotJob.investigate_status == "yes", 2),
        (RobotJob.investigate_status == "weak", 1),
        else_=0,
    )
    jobs: list[dict[str, Any]] = []
    try:
        rows = (
            db.query(RobotJob)
            .order_by(
                desc(status_rank),
                desc(RobotJob.existence_confidence),
                desc(RobotJob.definition_completeness),
                desc(RobotJob.created_at),
            )
            .limit(POOL)
            .all()
        )
    except Exception:
        logger.debug("daily jobs report query skipped", exc_info=True)
        rows = []
    seen: set[str] = set()
    for row in rows:
        employer = str(getattr(row, "company_name", "") or "").strip()
        locality = str(getattr(row, "locality", "") or "").strip()
        title = str(getattr(row, "robot_compatible_task", "") or "").strip()
        if not is_named_robot_job(employer, locality):
            continue
        if not is_job_employer_name(employer, title=title):
            continue
        key = str(getattr(row, "job_key", "") or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        jobs.append(_serialize_job(row, len(jobs) + 1))
        if len(jobs) >= cap:
            break
    return {
        "date": day_label,
        "count": len(jobs),
        "limit": cap,
        "jobs": jobs,
        "recipients": get_daily_jobs_report_recipients(),
        "last_sent_date": last_sent_day(),
        "find_href": f"{_SITE}/?visit=jobs",
        "admin_href": f"{_SITE}/admin#daily-jobs-report",
    }


def render_daily_jobs_report_text(report: dict[str, Any]) -> str:
    day = report.get("date") or datetime.now(timezone.utc).date().isoformat()
    jobs = list(report.get("jobs") or [])
    lines = [
        f"Top {int(report.get('limit') or TOP_N)} robot jobs — {day}",
        "",
        "Named employers and the work. These are Job Cards, not SIGNAL buyers.",
        "",
    ]
    if not jobs:
        lines.append("  • No named-employer jobs in the live table yet.")
        lines.append("")
    for job in jobs:
        rank = int(job.get("rank") or 0)
        employer = job.get("employer") or "Employer"
        title = job.get("title") or "Work"
        locality = job.get("locality") or ""
        lines.append(f"{rank:2}. {employer} — {title}")
        if locality:
            lines.append(f"    {locality}")
    lines += [
        "",
        f"FIND: {report.get('find_href') or f'{_SITE}/?visit=jobs'}",
        f"Admin: {report.get('admin_href') or f'{_SITE}/admin#daily-jobs-report'}",
        "",
        "You receive this once per day.",
    ]
    return "\n".join(lines)


def render_daily_jobs_report_html(report: dict[str, Any]) -> str:
    day = html.escape(str(report.get("date") or datetime.now(timezone.utc).date().isoformat()))
    limit = int(report.get("limit") or TOP_N)
    jobs = list(report.get("jobs") or [])
    find_href = html.escape(str(report.get("find_href") or f"{_SITE}/?visit=jobs"))
    admin_href = html.escape(
        str(report.get("admin_href") or f"{_SITE}/admin#daily-jobs-report")
    )
    rows: list[str] = []
    for job in jobs:
        rank = int(job.get("rank") or 0)
        employer = html.escape(str(job.get("employer") or "Employer"))
        title = html.escape(str(job.get("title") or "Work"))
        locality = html.escape(str(job.get("locality") or ""))
        place = (
            f"<div style=\"color:#4b5563;font-size:13px\">{locality}</div>"
            if locality
            else ""
        )
        rows.append(
            "<tr>"
            f"<td style=\"padding:8px 12px;vertical-align:top;color:#6b7280;"
            f"font-family:ui-monospace,monospace\">{rank:02d}</td>"
            f"<td style=\"padding:8px 12px\">"
            f"<div style=\"font-weight:700;color:#047857\">{employer}</div>"
            f"<div style=\"color:#111827\">{title}</div>"
            f"{place}</td></tr>"
        )
    listing = (
        "<p>No named-employer jobs in the live table yet.</p>"
        if not jobs
        else f"<table style=\"width:100%;border-collapse:collapse\">{''.join(rows)}</table>"
    )
    return (
        "<div style=\"font-family:Georgia,serif;max-width:640px;color:#111827\">"
        f"<h1 style=\"font-size:20px;margin:0 0 8px\">"
        f"Top {limit} robot jobs — {day}</h1>"
        "<p style=\"color:#4b5563;font-size:14px;margin:0 0 16px\">"
        "Named employers and the work. These are Job Cards, not SIGNAL buyers.</p>"
        f"{listing}"
        f"<p style=\"margin:16px 0 0;font-size:13px\">"
        f"<a href=\"{find_href}\">FIND</a> · "
        f"<a href=\"{admin_href}\">Admin list</a></p>"
        "<p style=\"color:#6b7280;font-size:12px\">You receive this once per day.</p>"
        "</div>"
    )


def send_daily_jobs_report(
    db: Session,
    *,
    force: bool = False,
    limit: int = TOP_N,
) -> dict[str, Any]:
    recipients = get_daily_jobs_report_recipients()
    today = datetime.now(timezone.utc).date().isoformat()
    if not force and not _claim_report_day(today):
        return {
            "sent": False,
            "reason": "Already sent today",
            "date": today,
            "recipients": recipients,
        }
    report = compose_daily_jobs_report(db, limit=limit)
    subject = f"Top {report['limit']} robot jobs — {report['date']}"
    body = render_daily_jobs_report_text(report)
    html_body = render_daily_jobs_report_html(report)
    from app.services.resend_email import ResendEmailError, send_email_via_resend

    try:
        result = send_email_via_resend(
            to_email=recipients,
            subject=subject,
            body_text=body,
            body_html=html_body,
            from_display_name="Ready For Robots · Jobs ops",
            idempotency_key=f"daily-jobs-report-{today}",
        )
    except ResendEmailError as exc:
        logger.warning("daily jobs report email failed: %s", exc)
        if not force:
            _release_report_day(today)
        return {"sent": False, "reason": str(exc), "recipients": recipients}
    payload = {
        "date": today,
        "count": report["count"],
        "jobs": report["jobs"],
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }
    _mark_report_sent(today, payload)
    return {
        "sent": True,
        "date": today,
        "recipients": recipients,
        "count": report["count"],
        "resend_id": result.get("resend_id"),
        "jobs": report["jobs"],
    }


def daily_jobs_report_enabled() -> bool:
    if os.getenv("DAILY_JOBS_REPORT_ENABLED", "").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return False
    return os.getenv("ENABLE_SCHEDULED_DAILY_JOBS_REPORT", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def report_in_process_owner() -> Optional[str]:
    if not daily_jobs_report_enabled():
        return None
    from app.runtime_role import is_web_process, is_worker_process

    if is_worker_process():
        return "worker"
    web_backup = os.getenv("DAILY_JOBS_REPORT_WEB_BACKUP", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if is_web_process() and web_backup:
        return "web-backup"
    return None


def next_report_run_utc(*, hour: int = 14, minute: int = 0) -> datetime:
    now = datetime.now(timezone.utc)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target
