"""Generate and send internal calendar invites."""
from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Any

from app.models.calendar import CalendarEvent
from app.services.resend_email import send_email_via_resend


def _ics_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _escape_ics(value: str | None) -> str:
    text = str(value or "")
    return text.replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def calendar_event_ics(event: CalendarEvent, *, organizer_email: str | None = None) -> str:
    attendees = event.attendees or []
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//ReadyForRobots//Operator Calendar//EN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:{event.ics_uid}",
        f"DTSTAMP:{_ics_datetime(datetime.now(timezone.utc))}",
        f"DTSTART:{_ics_datetime(event.start_at)}",
        f"DTEND:{_ics_datetime(event.end_at)}",
        f"SUMMARY:{_escape_ics(event.title)}",
        f"DESCRIPTION:{_escape_ics(event.description)}",
        f"LOCATION:{_escape_ics(event.meeting_url or event.location)}",
        "STATUS:CONFIRMED" if event.status == "scheduled" else "STATUS:CANCELLED",
        "SEQUENCE:0",
    ]
    if organizer_email:
        lines.append(f"ORGANIZER:MAILTO:{organizer_email}")
    for attendee in attendees:
        email = str(attendee.get("email") if isinstance(attendee, dict) else attendee or "").strip()
        if "@" in email:
            name = str(attendee.get("name") or email) if isinstance(attendee, dict) else email
            lines.append(f"ATTENDEE;CN={_escape_ics(name)};ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:MAILTO:{email}")
    lines.extend(["END:VEVENT", "END:VCALENDAR"])
    return "\r\n".join(lines) + "\r\n"


def attendee_emails(attendees: list[Any]) -> list[str]:
    emails: list[str] = []
    seen: set[str] = set()
    for attendee in attendees or []:
        email = str(attendee.get("email") if isinstance(attendee, dict) else attendee or "").strip()
        if "@" not in email:
            continue
        key = email.lower()
        if key in seen:
            continue
        seen.add(key)
        emails.append(email)
    return emails


def send_calendar_invite(event: CalendarEvent, *, organizer_email: str | None = None) -> dict[str, Any]:
    recipients = attendee_emails(event.attendees or [])
    ics = calendar_event_ics(event, organizer_email=organizer_email)
    body = f"""You are invited to:
{event.title}

When: {event.start_at} to {event.end_at} {event.timezone or 'UTC'}
Location: {event.meeting_url or event.location or 'TBD'}

{event.description or ''}
"""
    return send_email_via_resend(
        to_email=recipients,
        subject=f"Calendar invite: {event.title}",
        body_text=body,
        from_display_name="Cal",
        attachments=[
            {
                "filename": "invite.ics",
                "content": base64.b64encode(ics.encode("utf-8")).decode("ascii"),
                "content_type": "text/calendar; method=REQUEST",
            }
        ],
        idempotency_key=f"calendar-invite/{event.id}",
    )
