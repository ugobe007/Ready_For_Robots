"""Watch a robot URL for new / changed jobs. Email opted-in users. Free is a taste."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.jobs_watch import JobsWatch, JobsWatchEvent
from app.services.plan_entitlements import PLAN_FREE, PLAN_PAID, resolve_plan_tier

logger = logging.getLogger(__name__)

JOBS_WATCH_FREE_ROBOTS = 1
JOBS_WATCH_FREE_ALERTS = 2
JOBS_WATCH_FREE_VISIBLE_EVENTS = 3
_SITE = (os.getenv("PUBLIC_SITE_URL") or "https://readyforrobots.com").rstrip("/")


def jobs_watch_limits(plan: str) -> dict[str, Any]:
    if plan == PLAN_PAID:
        return {
            "plan": plan,
            "robots_limit": None,
            "alerts_limit": None,
            "visible_events": 12,
            "upgrade_url": "/pricing",
        }
    return {
        "plan": plan or PLAN_FREE,
        "robots_limit": JOBS_WATCH_FREE_ROBOTS,
        "alerts_limit": JOBS_WATCH_FREE_ALERTS,
        "visible_events": JOBS_WATCH_FREE_VISIBLE_EVENTS,
        "upgrade_url": "/pricing",
    }


def can_email_watch(watch: JobsWatch, plan: str) -> bool:
    if not watch.opted_in:
        return False
    limits = jobs_watch_limits(plan)
    cap = limits["alerts_limit"]
    if cap is None:
        return True
    return int(watch.notify_count or 0) < int(cap)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _job_keys(jobs: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for job in jobs:
        if not isinstance(job, dict):
            continue
        key = str(job.get("job_key") or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def apply_search_result(
    db: Session,
    watch: JobsWatch,
    jobs: list[dict[str, Any]],
    *,
    plan: str,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Diff this search against the last snapshot. First run seeds without emailing."""
    now = now or _now()
    keys = _job_keys(jobs)
    prev = {str(k) for k in (watch.last_job_keys or []) if k}
    first_run = not prev
    new_jobs = []
    if not first_run:
        by_key = {
            str(j.get("job_key")): j
            for j in jobs
            if isinstance(j, dict) and j.get("job_key")
        }
        for key in keys:
            if key in prev:
                continue
            job = by_key.get(key) or {}
            event = JobsWatchEvent(
                watch_id=watch.id,
                job_key=key,
                title=str(job.get("title") or key)[:512],
                company_name=(str(job.get("company_name") or "")[:240] or None),
                kind="new",
            )
            db.add(event)
            new_jobs.append(event)
    watch.last_job_keys = keys
    watch.last_checked_at = now
    return {
        "first_run": first_run,
        "new_count": len(new_jobs),
        "new_jobs": new_jobs,
        "can_email": bool(new_jobs) and can_email_watch(watch, plan),
    }


def seed_saved_jobs(
    db: Session,
    watch: JobsWatch,
    jobs: list[dict[str, Any]],
) -> int:
    """Show the opted-in list in CRM immediately so the watch feels live."""
    existing = {
        str(e.job_key)
        for e in db.query(JobsWatchEvent)
        .filter(JobsWatchEvent.watch_id == watch.id, JobsWatchEvent.kind == "saved")
        .all()
    }
    added = 0
    keys = list(watch.last_job_keys or [])
    for job in jobs:
        if not isinstance(job, dict):
            continue
        key = str(job.get("job_key") or "").strip()
        if not key:
            continue
        if key not in keys:
            keys.append(key)
        if key in existing:
            continue
        db.add(
            JobsWatchEvent(
                watch_id=watch.id,
                job_key=key,
                title=str(job.get("title") or key)[:512],
                company_name=(str(job.get("company_name") or "")[:240] or None),
                kind="saved",
            )
        )
        existing.add(key)
        added += 1
    watch.last_job_keys = keys
    return added


def serialize_event(event: JobsWatchEvent, *, locked: bool = False) -> dict[str, Any]:
    if locked:
        return {
            "id": event.id,
            "kind": event.kind,
            "title": "New work for your robot",
            "company_name": None,
            "locked": True,
        }
    return {
        "id": event.id,
        "kind": event.kind,
        "job_key": event.job_key,
        "title": event.title,
        "company_name": event.company_name,
        "locked": False,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


def watch_status(
    db: Session,
    user: dict[str, Any],
    watches: list[JobsWatch],
) -> dict[str, Any]:
    plan = resolve_plan_tier(user, db=db)
    limits = jobs_watch_limits(plan)
    active = [w for w in watches if w.opted_in]
    events: list[dict[str, Any]] = []
    visible = int(limits["visible_events"])
    for watch in active:
        rows = (
            db.query(JobsWatchEvent)
            .filter(JobsWatchEvent.watch_id == watch.id)
            .order_by(JobsWatchEvent.created_at.desc())
            .limit(12)
            .all()
        )
        for i, row in enumerate(rows):
            locked = plan != PLAN_PAID and i >= visible
            events.append(serialize_event(row, locked=locked))
    primary = active[0] if active else None
    return {
        "opted_in": bool(primary),
        "plan": plan,
        "robot_url": primary.robot_url if primary else None,
        "product_name": primary.product_name if primary else None,
        "website_domain": primary.website_domain if primary else None,
        "last_checked_at": primary.last_checked_at.isoformat() if primary and primary.last_checked_at else None,
        "robots_used": len(active),
        "robots_limit": limits["robots_limit"],
        "alerts_sent": int(primary.notify_count or 0) if primary else 0,
        "alerts_limit": limits["alerts_limit"],
        "events": events[:12],
        "upgrade_url": limits["upgrade_url"],
        "free_taste": plan != PLAN_PAID,
    }


def upsert_watch(
    db: Session,
    *,
    user: dict[str, Any],
    robot_url: str,
    product_name: Optional[str] = None,
    seed_jobs: Optional[list[dict[str, Any]]] = None,
    opted_in: bool = True,
) -> JobsWatch:
    from app.services.company_domain import normalize_website_domain
    from app.services.robot_submission_service import record_robot_submission
    from app.services.robot_url_safety import assert_public_http_url

    safe = assert_public_http_url(robot_url)
    domain = (normalize_website_domain(safe) or "")[:240]
    if not domain:
        raise ValueError("Need a public robot URL to watch.")
    uid = UUID(str(user["uid"]))
    email = (user.get("email") or "").strip()
    if not email:
        raise ValueError("Need an email on the account to send job alerts.")
    plan = resolve_plan_tier(user, db=db)
    limits = jobs_watch_limits(plan)
    existing = (
        db.query(JobsWatch)
        .filter(JobsWatch.user_id == uid, JobsWatch.website_domain == domain)
        .one_or_none()
    )
    active_count = (
        db.query(JobsWatch)
        .filter(JobsWatch.user_id == uid, JobsWatch.opted_in.is_(True))
        .count()
    )
    cap = limits["robots_limit"]
    if opted_in and cap is not None and existing is None and active_count >= cap:
        raise PermissionError("Free watches 1 robot. Pro keeps every SKU on the cron.")
    if opted_in and cap is not None and existing is not None and not existing.opted_in and active_count >= cap:
        raise PermissionError("Free watches 1 robot. Pro keeps every SKU on the cron.")

    submission = record_robot_submission(
        db,
        url=safe,
        product_name=product_name,
        source="jobs_watch",
    )
    if existing is None:
        existing = JobsWatch(
            user_id=uid,
            email=email,
            robot_url=safe,
            website_domain=domain,
            product_name=(product_name or "")[:240] or None,
            robot_submission_id=submission.id if submission else None,
            opted_in=opted_in,
            last_job_keys=[],
            notify_count=0,
        )
        db.add(existing)
        db.flush()
    else:
        existing.email = email
        existing.robot_url = safe
        existing.product_name = (product_name or existing.product_name or "")[:240] or None
        existing.opted_in = opted_in
        if submission is not None:
            existing.robot_submission_id = submission.id
    if opted_in and seed_jobs:
        seed_saved_jobs(db, existing, seed_jobs)
    db.commit()
    db.refresh(existing)
    return existing


def build_watch_email(watch: JobsWatch, events: list[JobsWatchEvent], *, plan: str) -> tuple[str, str]:
    product = watch.product_name or watch.website_domain
    subject = f"New jobs for {product}"
    lines = [
        f"We checked {product} and found new work.",
        "",
    ]
    show = events[: 3 if plan == PLAN_PAID else 1]
    for event in show:
        place = f" — {event.company_name}" if event.company_name else ""
        lines.append(f"• {event.title}{place}")
    lines += [
        "",
        f"Open CRM: {_SITE}/crm",
        f"Open jobs: {_SITE}/",
    ]
    if plan != PLAN_PAID:
        lines += [
            "",
            "Free watches 1 robot and sends 2 alerts. Pro keeps every SKU on the cron.",
            f"Upgrade: {_SITE}/pricing",
        ]
    return subject, "\n".join(lines)


def send_watch_email(watch: JobsWatch, events: list[JobsWatchEvent], *, plan: str) -> bool:
    if not events:
        return False
    from app.services.resend_email import ResendEmailError, send_email_via_resend

    subject, body = build_watch_email(watch, events, plan=plan)
    try:
        send_email_via_resend(
            to_email=watch.email,
            subject=subject,
            body_text=body,
            from_display_name="ReadyForRobots",
        )
        return True
    except ResendEmailError as exc:
        logger.warning("jobs_watch_email_failed watch=%s err=%s", watch.id, exc)
        return False


SearchFn = Callable[..., dict[str, Any]]


def run_jobs_watch_cycle(
    db: Session,
    *,
    limit: int = 25,
    search_fn: Optional[SearchFn] = None,
    send: bool = True,
) -> dict[str, Any]:
    """Re-check opted-in robot URLs. Fail-open per watch."""
    from app.models.user_profile import UserProfile

    watches = (
        db.query(JobsWatch)
        .filter(JobsWatch.opted_in.is_(True))
        .order_by(JobsWatch.last_checked_at.asc())
        .limit(max(1, int(limit)))
        .all()
    )
    search = search_fn
    if search is None:
        from app.services.robot_job_search import compose_robot_job_search

        search = compose_robot_job_search

    checked = 0
    emailed = 0
    errors = 0
    new_total = 0
    now = _now()
    for watch in watches:
        try:
            result = search(watch.robot_url, product=watch.product_name)
            jobs = list(result.get("jobs") or result.get("top_jobs") or [])
            profile = None
            try:
                user_row = db.query(UserProfile).filter(UserProfile.id == watch.user_id).one_or_none()
                profile = {
                    "uid": str(watch.user_id),
                    "email": watch.email,
                    "plan_tier": getattr(user_row, "billing_tier", None) if user_row else None,
                }
            except Exception:
                profile = {"uid": str(watch.user_id), "email": watch.email}
            plan = resolve_plan_tier(profile, db=db)
            diff = apply_search_result(db, watch, jobs, plan=plan, now=now)
            checked += 1
            new_total += int(diff["new_count"])
            new_events: list[JobsWatchEvent] = diff["new_jobs"]
            if send and diff["can_email"] and new_events:
                if send_watch_email(watch, new_events, plan=plan):
                    emailed += 1
                    watch.notify_count = int(watch.notify_count or 0) + 1
                    watch.last_notified_at = now
                    for event in new_events:
                        event.emailed_at = now
        except Exception:
            errors += 1
            logger.exception("jobs_watch_cycle_failed watch=%s", getattr(watch, "id", None))
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("jobs_watch_cycle_commit_failed")
    return {
        "checked": checked,
        "emailed": emailed,
        "errors": errors,
        "new_jobs": new_total,
        "watches": len(watches),
    }
