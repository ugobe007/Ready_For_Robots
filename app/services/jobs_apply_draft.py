"""Prepare a Jobs CRM application draft for OEM/distributor review.

Operator reviews and sends. We do not auto-email employers.
No invented emails. No LinkedIn/Apollo scrape.
"""
from __future__ import annotations

import re
from typing import Any

from app.services.email_address import normalize_recipient_email
from app.services.robot_youtube_evidence import find_robot_youtube_evidence

CONTACTS_EMPTY_NOTE = (
    "No employer email on this Job Card or stored public page. We will not invent one."
)
OPERATOR_SENDS_NOTE = (
    "This is a draft. Review it. You send. We do not email the employer until you do."
)

_EMAIL_KEYS = (
    "employer_email",
    "contact_email",
    "company_email",
    "email",
    "public_email",
    "page_email",
)
_LIST_KEYS = (
    "contacts",
    "contact_emails",
    "emails",
    "public_emails",
    "page_emails",
    "employer_page_emails",
)


def _robot_label(name: str | None) -> str:
    text = re.sub(r"\s+", " ", (name or "").strip())
    if not text or re.fullmatch(r"your robot|this robot", text, flags=re.I):
        return "this robot"
    return text


def apply_why(
    *,
    robot_name: str,
    employer: str | None,
    work: str | None,
    workplace: str | None = None,
) -> str:
    """Short recruiter why. Names the robot. Not machine voice."""
    who = _robot_label(robot_name)
    shop = re.sub(r"\s+", " ", (employer or "").strip()) or "this employer"
    job = re.sub(r"\s+", " ", (work or "").strip())
    place = re.sub(r"\s+", " ", (workplace or "").strip())
    if job and place:
        return (
            f"We're putting {who} forward for {job} at {shop} ({place}). "
            f"{who} already does this work."
        )
    if job:
        return (
            f"We're putting {who} forward for {job} at {shop}. "
            f"{who} already does this work."
        )
    return f"We're putting {who} forward at {shop}. {who} already does this work."


def _add_email(out: list[dict[str, str]], seen: set[str], raw: Any, source: str) -> None:
    if not isinstance(raw, str):
        return
    hit = normalize_recipient_email(raw)
    if not hit or hit in seen:
        return
    seen.add(hit)
    out.append({"email": hit, "source": source})


def _walk_mapping(obj: dict[str, Any], out: list[dict[str, str]], seen: set[str], source: str) -> None:
    for key in _EMAIL_KEYS:
        _add_email(out, seen, obj.get(key), source)
    for key in _LIST_KEYS:
        raw = obj.get(key)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str):
                    _add_email(out, seen, item, source)
                elif isinstance(item, dict):
                    _walk_mapping(item, out, seen, source)
        elif isinstance(raw, str):
            _add_email(out, seen, raw, source)
    nested = obj.get("employer")
    if isinstance(nested, dict):
        _walk_mapping(nested, out, seen, "employer_record")


def employer_contacts_from_job(job: dict[str, Any] | None) -> list[dict[str, str]]:
    """Real emails already on the Job Card or stored public employer page. Never invent."""
    if not isinstance(job, dict):
        return []
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    _walk_mapping(job, out, seen, "job_card")
    return out


def compose_apply_draft(
    *,
    robot_name: str,
    models: list[str],
    employer: str,
    work: str,
    workplace: str | None = None,
    monthly_price: str = "",
    poc: str = "",
    why: str = "",
    video_url: str | None = None,
    video_note: str = "",
    clip_description: str | None = None,
    contacts: list[dict[str, str]] | None = None,
    video_search_url: str = "",
    accept_url: str | None = None,
    interview_url: str | None = None,
    decline_url: str | None = None,
    document_lines: list[str] | None = None,
) -> dict[str, Any]:
    who = _robot_label(robot_name)
    shop = (employer or "this employer").strip() or "this employer"
    job = (work or "this job").strip() or "this job"
    why_text = (why or "").strip() or apply_why(
        robot_name=who, employer=shop, work=job, workplace=workplace
    )
    people = [c for c in (contacts or []) if isinstance(c, dict) and c.get("email")]
    emails = [str(c["email"]) for c in people]
    subject = f"Applying {who} to {job} at {shop}"
    place = f" at {workplace}" if workplace else ""
    lines = [
        f"We're applying {who} to {job}{place}.",
        "",
        why_text,
        "",
        f"Model(s) we will use: {', '.join(models) if models else '(no catalogued model selected)'}",
        f"PoC proof: {poc or '(not provided)'}",
        f"Proposed monthly price we would charge (our offer, not a site rate): {monthly_price or '(you still need to quote this)'}",
    ]
    clip = (clip_description or "").strip()
    if clip:
        lines.extend(["", f"Clip: {clip}"])
    if video_url:
        lines.extend(["", f"Video résumé: {video_url}"])
    else:
        lines.extend(["", video_note or "No public YouTube clip. Video field is empty."])
        if video_search_url:
            lines.append(f"YouTube search: {video_search_url}")
    if document_lines:
        lines.extend(["", *document_lines])
    if emails:
        lines.extend(["", "Contact on file: " + ", ".join(emails)])
    else:
        lines.extend(["", CONTACTS_EMPTY_NOTE])
    if accept_url or interview_url or decline_url:
        lines.extend(["", "Evaluate this application (no Ready For Robots account required):"])
        if accept_url:
            lines.append(f"Accept: {accept_url}")
        if interview_url:
            lines.append(f"Set up interview: {interview_url}")
        if decline_url:
            lines.append(f"Decline: {decline_url}")
    lines.extend(["", OPERATOR_SENDS_NOTE])
    return {
        "subject": subject,
        "body": "\n".join(lines),
        "video_url": video_url,
        "video_search_url": video_search_url,
        "video_note": video_note,
        "clip_description": clip,
        "why": why_text,
        "contacts": people,
        "operator_sends": True,
    }


def resolve_apply_video(
    *,
    pasted_url: str | None,
    company: str | None,
    sku: str | None,
    robot: str | None,
) -> dict[str, Any]:
    from app.services.poc_video_url import normalize_poc_video_url

    pasted = None
    if pasted_url:
        pasted = normalize_poc_video_url(pasted_url)
    evidence = find_robot_youtube_evidence(company=company, sku=sku, robot=robot)
    if pasted:
        return {
            "video_url": pasted,
            "video_search_url": evidence.get("video_search_url") or "",
            "video_note": "Using the video URL you pasted.",
            "clip_description": evidence.get("clip_description"),
            "source": "pasted",
        }
    return evidence
