"""Daily top-25 Robot Job sales cards — operator email + admin list.

Named employers and real work only. Not SIGNAL buyers. No paid LLM.
Never invent a decision-maker name or an operations@company.com mailbox.
"""
from __future__ import annotations

import html
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import quote

from sqlalchemy import case, desc
from sqlalchemy.orm import Session

from app.services.oem_job_intro import (
    employer_intro_from_sales_card,
    intro_from_sales_card,
)

logger = logging.getLogger(__name__)

TOP_N = 25
POOL = 200
DEFAULT_RECIPIENT = "ugobe07@gmail.com"
_SITE = (os.getenv("PUBLIC_SITE_URL") or "https://readyforrobots.com").rstrip("/")
_REDIS_SENT_KEY = "jobs:daily_report:last_sent_date"
_REDIS_PAYLOAD_KEY = "jobs:daily_report:latest"
_CLAIM_TTL_SEC = 60 * 60 * 48
# A living send holds the NX lock. After this, a crashed worker no longer
# looks like a delivered email — GHA / catch-up may steal and send.
_STALE_CLAIM_SEC = 40 * 60
DESCRIPTION_MAX = 360
DECISION_MAKER_EMPTY = "Not named on the posting"
DECISION_MAKER_HUNTER_MISS = "Hunter.io found no named person"
CONTACT_EMPTY = "No page email or apply URL. We will not invent one."
CONTACT_HUNTER_MISS = "Hunter.io found no verified email"
TIMING_EMPTY = "Timing not on the posting"
_INVENTED_LEAD_RE = re.compile(r"^operational lead\b", re.I)


def _claim_key(day: str) -> str:
    return f"jobs:daily_report:claimed:{day}"


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
    from app.services.phelan_autonomy import _redis_client as client_fn

    return client_fn()


def _parse_claim_at(raw: Any) -> Optional[datetime]:
    text = str(raw or "").strip()
    if not text:
        return None
    # Date-only leftover from claim-before-send is not a living lock.
    if "T" not in text and " " not in text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _claim_report_day(day: str) -> bool:
    """Atomically lock today's send. Yesterday's last_sent_date must not block today.

    The lock value is an ISO timestamp. A leftover day-only value from the old
    claim-before-send path is treated as stale so a hung Hunter run cannot fake
    Gmail delivery. Fresh locks younger than `_STALE_CLAIM_SEC` stay exclusive.
    """
    client = _redis_client()
    if not client:
        return True
    stamp = datetime.now(timezone.utc).isoformat()
    key = _claim_key(day)
    try:
        if client.set(key, stamp, nx=True, ex=_CLAIM_TTL_SEC):
            return True
        raw = client.get(key)
        claimed_at = _parse_claim_at(raw)
        if claimed_at is None:
            logger.warning("daily jobs report: stealing unparseable claim for %s", day)
            if client.set(key, stamp, xx=True, ex=_CLAIM_TTL_SEC, get=True) == raw:
                return True
            return False
        age = (datetime.now(timezone.utc) - claimed_at).total_seconds()
        if age >= _STALE_CLAIM_SEC:
            logger.warning(
                "daily jobs report: stealing stale claim for %s age_sec=%.0f",
                day,
                age,
            )
            if client.set(key, stamp, xx=True, ex=_CLAIM_TTL_SEC, get=True) == raw:
                return True
            return False
        return False
    except Exception:
        return True


def _release_report_day(day: str) -> None:
    client = _redis_client()
    if not client:
        return
    try:
        client.delete(_claim_key(day))
    except Exception:
        pass


def _mark_report_sent(day: str, payload: dict[str, Any]) -> None:
    client = _redis_client()
    if not client:
        return
    try:
        client.set(_REDIS_SENT_KEY, day, ex=_CLAIM_TTL_SEC)
        client.set(
            _claim_key(day),
            datetime.now(timezone.utc).isoformat(),
            ex=_CLAIM_TTL_SEC,
        )
        client.set(_REDIS_PAYLOAD_KEY, json.dumps(payload), ex=_CLAIM_TTL_SEC)
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


def last_sent_payload() -> dict[str, Any]:
    """Last successful Resend payload. Empty if the day was only claimed."""
    client = _redis_client()
    if not client:
        return {}
    try:
        raw = client.get(_REDIS_PAYLOAD_KEY)
        if not raw:
            return {}
        parsed = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _as_map(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip().startswith("{"):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _clean(value: Any, *, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _job_type(row: Any) -> str:
    action = _clean(getattr(row, "action", ""), limit=80)
    if action:
        return action.replace("_", " ").title()
    return "Operational work"


def _job_description(row: Any) -> str:
    for attr in ("observed_workflow", "why_job", "robot_compatible_task"):
        text = _clean(getattr(row, attr, ""), limit=DESCRIPTION_MAX)
        if text:
            return text
    return _job_type(row)


def _timing(row: Any) -> str:
    created = getattr(row, "created_at", None)
    if not isinstance(created, datetime):
        return TIMING_EMPTY
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    day = created.astimezone(timezone.utc).date()
    age = (datetime.now(timezone.utc).date() - day).days
    label = f"First seen {day.isoformat()}"
    if age <= 7:
        return f"{label} · new this week"
    if age <= 30:
        return f"{label} · this month"
    return label


def _page_name_title(row: Any) -> tuple[str, str]:
    """Page-sourced name/title only. Skip matcher-invented Operational Lead rows."""
    blob: dict[str, Any] = {}
    if isinstance(row, dict):
        blob.update(_as_map(row.get("requirements")))
        blob.update(_as_map(row.get("provenance")))
    else:
        blob.update(_as_map(getattr(row, "requirements", None)))
        blob.update(_as_map(getattr(row, "provenance", None)))
    name = _clean(
        blob.get("contact_name")
        or blob.get("decision_maker_name")
        or blob.get("hiring_contact_name"),
        limit=120,
    )
    title = _clean(
        blob.get("contact_title")
        or blob.get("decision_maker_title")
        or blob.get("hiring_contact_title"),
        limit=160,
    )
    if name and _INVENTED_LEAD_RE.search(name):
        name = ""
        title = ""
    return name, title


def _is_invented_ops_email(email: str, employer: str) -> bool:
    """Matcher used to mint operations@{squeezed-employer}.com. Never surface those."""
    raw = (email or "").strip().lower()
    if "@" not in raw:
        return True
    local, _, domain = raw.partition("@")
    if local != "operations":
        return False
    slug = re.sub(r"[^a-z0-9]", "", (employer or "").lower())
    host = re.sub(r"[^a-z0-9]", "", domain.rsplit(".", 1)[0] if "." in domain else domain)
    return bool(slug) and (slug in host or host in slug)


def _contact_fields(row: Any) -> dict[str, Optional[str]]:
    employer = _clean(getattr(row, "company_name", ""), limit=240)
    email = _clean(getattr(row, "employer_email", ""), limit=320).lower() or None
    if email and _is_invented_ops_email(email, employer):
        email = None
    contact_url = _clean(getattr(row, "contact_url", ""), limit=1024) or None
    apply_url = _clean(getattr(row, "apply_url", ""), limit=1024) or None
    return {
        "email": email,
        "contact_url": contact_url,
        "apply_url": apply_url,
    }


def _hunter_checked(row: Any) -> bool:
    blob: dict[str, Any] = {}
    blob.update(_as_map(getattr(row, "requirements", None)))
    blob.update(_as_map(getattr(row, "provenance", None)))
    return bool(blob.get("hunter_checked_at") or blob.get("contact_source") == "hunter_domain")


def _contact_source(row: Any) -> Optional[str]:
    blob: dict[str, Any] = {}
    blob.update(_as_map(getattr(row, "requirements", None)))
    blob.update(_as_map(getattr(row, "provenance", None)))
    src = str(blob.get("contact_source") or "").strip()
    return src or None


def _dm_agent_fields(row: Any) -> tuple[list[str], Optional[str]]:
    blob: dict[str, Any] = {}
    blob.update(_as_map(getattr(row, "requirements", None)))
    blob.update(_as_map(getattr(row, "provenance", None)))
    titles_raw = blob.get("dm_target_titles") or []
    titles = [str(t).strip() for t in titles_raw if str(t).strip()][:6]
    why = _clean(blob.get("dm_match_why"), limit=200) or None
    return titles, why


def _decision_maker_line(name: str, title: str, *, hunter_checked: bool = False) -> str:
    if name and title:
        return f"{name} · {title}"
    if name:
        return name
    if title:
        return title
    if hunter_checked:
        return DECISION_MAKER_HUNTER_MISS
    return DECISION_MAKER_EMPTY


def _contact_line(
    contact: dict[str, Optional[str]], *, hunter_checked: bool = False
) -> str:
    parts = [
        p
        for p in (contact.get("email"), contact.get("contact_url"), contact.get("apply_url"))
        if p
    ]
    if parts:
        return " · ".join(parts)
    if hunter_checked:
        return CONTACT_HUNTER_MISS
    return CONTACT_EMPTY


def job_card_href(job_key: str) -> str:
    key = str(job_key or "").strip()
    if not key:
        return f"{_SITE}/?visit=jobs"
    return f"{_SITE}/?job={quote(key, safe='')}"


def _family_for_action(action: str, title: str) -> str:
    """Letter tokens only. `arm` in pharmacy is not a gripper; `pallet_move` is a pallet."""
    tokens = re.findall(r"[a-z]+", f"{action} {title}".lower())

    def has(*stems: str) -> bool:
        return any(token.startswith(stem) for token in tokens for stem in stems)

    if has("pallet", "stack", "case"):
        return "pallet"
    if has("scrub", "clean", "evs", "floor"):
        return "scrub"
    if has("inspect", "vision", "audit"):
        return "inspect"
    if has("pick", "grip", "manipul") or "arm" in tokens:
        return "gripper"
    if has("cart", "tote"):
        return "cart"
    return "transport"


def public_job_card(db: Session, job_key: str) -> Optional[dict[str, Any]]:
    """Named-employer Robot Job for `/?job=`. No invented people or dollars."""
    from app.models.robot_directed_discovery import RobotJob
    from app.services.robot_job_extract import is_job_employer_name
    from app.services.robot_requirement_match import is_named_robot_job

    key = str(job_key or "").strip()
    if not key:
        return None
    try:
        row = db.query(RobotJob).filter(RobotJob.job_key == key).one_or_none()
    except Exception:
        logger.debug("public job card lookup skipped", exc_info=True)
        return None
    if row is None:
        return None
    employer = str(getattr(row, "company_name", "") or "").strip()
    locality = str(getattr(row, "locality", "") or "").strip()
    title = str(getattr(row, "robot_compatible_task", "") or "").strip()
    if not is_named_robot_job(employer, locality):
        return None
    if not is_job_employer_name(employer, title=title):
        return None
    serialized = _serialize_job(row, 0)
    return {
        "key": serialized["job_key"],
        "title": serialized["title"],
        "employer": serialized["employer"],
        "locality": serialized["locality"],
        "description": serialized["description"],
        "job_type": serialized["job_type"],
        "action": serialized["action"],
        "family": _family_for_action(serialized["action"], serialized["title"]),
        "path": locality or "WORKSITE → WORKSITE",
        "industry": " · ".join(
            p for p in (serialized["employer"], serialized["locality"]) if p
        ),
        "card_href": serialized["card_href"],
    }


def _serialize_job(row: Any, rank: int) -> dict[str, Any]:
    title = _clean(getattr(row, "robot_compatible_task", ""), limit=240)
    action = _clean(getattr(row, "action", ""), limit=80)
    if not title:
        title = action.replace("_", " ") or "Operational work"
    created = getattr(row, "created_at", None)
    name, dm_title = _page_name_title(row)
    contact = _contact_fields(row)
    hunter_checked = _hunter_checked(row)
    target_titles, match_why = _dm_agent_fields(row)
    card = {
        "rank": rank,
        "job_key": str(getattr(row, "job_key", "") or ""),
        "employer": _clean(getattr(row, "company_name", ""), limit=240),
        "title": title,
        "locality": _clean(getattr(row, "locality", ""), limit=240),
        "action": action,
        "job_type": _job_type(row),
        "description": _job_description(row),
        "decision_maker": _decision_maker_line(
            name, dm_title, hunter_checked=hunter_checked
        ),
        "decision_maker_name": name or None,
        "decision_maker_title": dm_title or None,
        "timing": _timing(row),
        "contact": _contact_line(contact, hunter_checked=hunter_checked),
        "employer_email": contact.get("email"),
        "contact_url": contact.get("contact_url"),
        "apply_url": contact.get("apply_url"),
        "contact_source": _contact_source(row),
        "target_titles": target_titles,
        "match_why": match_why,
        "investigate_status": str(getattr(row, "investigate_status", "") or ""),
        "created_at": created.isoformat() if created else None,
        "card_href": job_card_href(str(getattr(row, "job_key", "") or "")),
    }
    card["intro"] = intro_from_sales_card(card)
    card["employer_intro"] = employer_intro_from_sales_card(card)
    return card


def select_daily_report_rows(db: Session, *, limit: int = TOP_N) -> list[Any]:
    """Named-employer Robot Jobs in the same order as the operator cards."""
    from app.models.robot_directed_discovery import RobotJob
    from app.services.robot_job_extract import is_job_employer_name
    from app.services.robot_requirement_match import is_named_robot_job

    cap = max(1, min(int(limit), 50))
    status_rank = case(
        (RobotJob.investigate_status == "yes", 2),
        (RobotJob.investigate_status == "weak", 1),
        else_=0,
    )
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
        return []
    picked: list[Any] = []
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
        picked.append(row)
        if len(picked) >= cap:
            break
    return picked


def compose_daily_jobs_report(db: Session, *, limit: int = TOP_N) -> dict[str, Any]:
    """Rank named-employer Robot Jobs the same way FIND accepts them."""
    cap = max(1, min(int(limit), 50))
    day_label = datetime.now(timezone.utc).date().isoformat()
    jobs = [
        _serialize_job(row, rank)
        for rank, row in enumerate(select_daily_report_rows(db, limit=cap), start=1)
    ]
    last = last_sent_payload()
    return {
        "date": day_label,
        "count": len(jobs),
        "limit": cap,
        "jobs": jobs,
        "recipients": get_daily_jobs_report_recipients(),
        "last_sent_date": last_sent_day(),
        "last_sent_at": last.get("sent_at"),
        "last_resend_id": last.get("resend_id"),
        "find_href": f"{_SITE}/?visit=jobs",
        "admin_href": f"{_SITE}/admin#daily-jobs-report",
    }


def _job_name_line(job: dict[str, Any]) -> str:
    title = str(job.get("title") or job.get("job_type") or "Work").strip()
    desc = str(job.get("description") or "").strip()
    if desc and desc != title:
        return f"{title} — {desc}"
    return title


def _decision_maker_inline(job: dict[str, Any]) -> str:
    parts = [str(job.get("decision_maker") or DECISION_MAKER_EMPTY)]
    titles = [str(t).strip() for t in (job.get("target_titles") or []) if str(t).strip()]
    if titles and not job.get("decision_maker_name"):
        parts.append("Looked for: " + ", ".join(titles[:3]))
    why = str(job.get("match_why") or "").strip()
    if why:
        parts.append(why)
    return " · ".join(parts)


def render_daily_jobs_report_text(report: dict[str, Any]) -> str:
    day = report.get("date") or datetime.now(timezone.utc).date().isoformat()
    jobs = list(report.get("jobs") or [])
    lines = [
        f"Top {int(report.get('limit') or TOP_N)} hot job opportunities — {day}",
        "",
        "Named-employer Robot Jobs. Decision maker and contact as stored. We do not invent people or emails.",
        "",
    ]
    if not jobs:
        lines.append("No named-employer jobs in the live table yet.")
        lines.append("")
    for job in jobs:
        rank = int(job.get("rank") or 0)
        employer = job.get("employer") or "Employer"
        locality = str(job.get("locality") or "").strip()
        head = f"{rank:02d}  {employer}"
        if locality:
            head = f"{head} · {locality}"
        lines.append(head)
        lines.append(f"    {_job_name_line(job)}")
        lines.append(f"    Decision maker: {_decision_maker_inline(job)}")
        lines.append(f"    Contact: {job.get('contact') or CONTACT_EMPTY}")
        href = str(job.get("card_href") or job_card_href(str(job.get("job_key") or "")))
        lines.append(f"    Job card: {href}")
        intro = str(job.get("intro") or intro_from_sales_card(job) or "").strip()
        if intro:
            lines.append("    [5] Intro to the robot company")
            for intro_line in intro.splitlines():
                lines.append(f"        {intro_line}")
        employer_intro = str(
            job.get("employer_intro") or employer_intro_from_sales_card(job) or ""
        ).strip()
        if employer_intro:
            lines.append("    [6] Intro to the employer")
            for intro_line in employer_intro.splitlines():
                lines.append(f"        {intro_line}")
        lines.append("")
    lines += [
        f"FIND: {report.get('find_href') or f'{_SITE}/?visit=jobs'}",
        f"Admin: {report.get('admin_href') or f'{_SITE}/admin#daily-jobs-report'}",
        "",
        "You receive this once per day. Email now on Admin sends a catch-up.",
    ]
    return "\n".join(lines)


def _mailto_or_link(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if "@" in raw and "://" not in raw and " " not in raw:
        href = html.escape(f"mailto:{raw}")
        return f'<a href="{href}">{html.escape(raw)}</a>'
    if raw.startswith(("http://", "https://")):
        href = html.escape(raw)
        return f'<a href="{href}">{html.escape(raw)}</a>'
    return html.escape(raw)


def _contact_html(job: dict[str, Any]) -> str:
    bits = [
        _mailto_or_link(str(job.get("employer_email") or "")),
        _mailto_or_link(str(job.get("contact_url") or "")),
        _mailto_or_link(str(job.get("apply_url") or "")),
    ]
    bits = [b for b in bits if b]
    if bits:
        return " · ".join(bits)
    return html.escape(str(job.get("contact") or CONTACT_EMPTY))


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
        locality = html.escape(str(job.get("locality") or "").strip())
        head = f"{rank:02d} {employer}"
        if locality:
            head = f"{head} · {locality}"
        href = str(job.get("card_href") or job_card_href(str(job.get("job_key") or "")))
        card = html.escape(href)
        rows.append(
            "<p style=\"margin:0 0 12px;padding:0;font-size:14px;line-height:1.45\">"
            f"<strong>{head}</strong><br>"
            f"{html.escape(_job_name_line(job))}<br>"
            f"Decision maker: {html.escape(_decision_maker_inline(job))}<br>"
            f"Contact: {_contact_html(job)}<br>"
            f"<a href=\"{card}\">Job card</a>"
            "</p>"
        )
    listing = (
        "<p style=\"margin:0;padding:0\">No named-employer jobs in the live table yet.</p>"
        if not jobs
        else "".join(rows)
    )
    return (
        "<div style=\"font-family:Georgia,serif;max-width:640px;color:#111827;"
        "margin:0;padding:0\">"
        f"<p style=\"font-size:16px;font-weight:700;margin:0 0 8px;padding:0\">"
        f"Top {limit} hot job opportunities — {day}</p>"
        "<p style=\"color:#4b5563;font-size:13px;margin:0 0 12px;padding:0\">"
        "Named-employer Robot Jobs. Decision maker and contact as stored. "
        "We do not invent people or emails.</p>"
        f"{listing}"
        f"<p style=\"margin:12px 0 0;padding:0;font-size:13px\">"
        f"<a href=\"{find_href}\">FIND</a> · "
        f"<a href=\"{admin_href}\">Admin</a></p>"
        "<p style=\"color:#6b7280;font-size:12px;margin:8px 0 0;padding:0\">"
        "You receive this once per day. Email now on Admin sends a catch-up.</p>"
        "</div>"
    )


def _idempotency_key(day: str, *, force: bool) -> str:
    if force:
        stamp = datetime.now(timezone.utc).strftime("%H%M%S")
        return f"daily-jobs-report-{day}-force-{stamp}"
    return f"daily-jobs-report-{day}-cards-v2"


def _already_sent_response(
    *, today: str, recipients: list[str], payload: dict[str, Any]
) -> dict[str, Any]:
    return {
        "sent": False,
        "reason": "Already sent today",
        "date": today,
        "recipients": recipients,
        "resend_id": payload.get("resend_id"),
        "sent_at": payload.get("sent_at"),
        "count": payload.get("count"),
    }


def send_daily_jobs_report(
    db: Session,
    *,
    force: bool = False,
    limit: int = TOP_N,
) -> dict[str, Any]:
    recipients = get_daily_jobs_report_recipients()
    today = datetime.now(timezone.utc).date().isoformat()
    payload = last_sent_payload()
    if not force and last_sent_day() == today:
        return _already_sent_response(
            today=today, recipients=recipients, payload=payload
        )
    if not force and not _claim_report_day(today):
        return {
            "sent": False,
            "reason": "Send already in progress",
            "date": today,
            "recipients": recipients,
            "last_sent_date": last_sent_day(),
            "resend_id": payload.get("resend_id"),
            "sent_at": payload.get("sent_at"),
        }
    hunter: dict[str, Any] = {}
    try:
        try:
            from app.services.daily_jobs_hunter import enrich_daily_jobs_with_hunter

            hunter = enrich_daily_jobs_with_hunter(
                db, limit=limit, scrape_pages=True
            )
        except Exception:
            logger.warning("Hunter.io daily-jobs enrich skipped", exc_info=True)
            hunter = {"ok": False, "reason": "hunter_enrich_failed"}
        report = compose_daily_jobs_report(db, limit=limit)
        subject = f"Top {report['limit']} hot job opportunities — {report['date']}"
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
                idempotency_key=_idempotency_key(today, force=force),
            )
        except ResendEmailError as exc:
            logger.warning("daily jobs report email failed: %s", exc)
            if not force:
                _release_report_day(today)
            return {"sent": False, "reason": str(exc), "recipients": recipients}
        sent_payload = {
            "date": today,
            "count": report["count"],
            "jobs": report["jobs"],
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "resend_id": result.get("resend_id"),
            "recipients": recipients,
        }
        _mark_report_sent(today, sent_payload)
        return {
            "sent": True,
            "date": today,
            "recipients": recipients,
            "count": report["count"],
            "resend_id": result.get("resend_id"),
            "jobs": report["jobs"],
            "hunter": hunter,
        }
    except Exception:
        if not force:
            _release_report_day(today)
        raise


def maybe_send_missed_daily_jobs_report(db: Session) -> dict[str, Any]:
    """If today's 14:00 UTC send was missed (deploy after the hour), send once."""
    today = datetime.now(timezone.utc).date().isoformat()
    if last_sent_day() == today:
        payload = last_sent_payload()
        return _already_sent_response(
            today=today,
            recipients=get_daily_jobs_report_recipients(),
            payload=payload,
        )
    return send_daily_jobs_report(db, force=False)


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
