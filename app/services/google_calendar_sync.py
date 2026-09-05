"""Google Calendar event sync for operator meetings."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import requests
from sqlalchemy.orm import Session

from app.models.calendar import CalendarEvent
from app.services.google_calendar_oauth import GoogleCalendarError, client_id, client_secret
from app.services.integration_connections import get_provider_token, PROVIDER_GOOGLE_CALENDAR, _find_connection
from app.services.integration_tokens import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"


def get_valid_access_token(db: Session, *, team_id: UUID) -> str:
    row = _find_connection(db, team_id, PROVIDER_GOOGLE_CALENDAR)
    if not row or row.status != "active":
        raise GoogleCalendarError("Google Calendar is not connected")
    access_token = get_provider_token(db, team_id=team_id, provider=PROVIDER_GOOGLE_CALENDAR)
    if not access_token:
        raise GoogleCalendarError("Google Calendar token missing")
    cfg = row.config or {}
    expires_at = float(cfg.get("expires_at") or 0)
    if expires_at and expires_at > datetime.now(timezone.utc).timestamp() + 60:
        return access_token

    refresh_cipher = cfg.get("refresh_token_ciphertext")
    if not refresh_cipher:
        return access_token

    refresh_token = decrypt_token(str(refresh_cipher))
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "grant_type": "refresh_token",
            "client_id": client_id(),
            "client_secret": client_secret(),
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    if resp.status_code >= 400:
        raise GoogleCalendarError(f"Google token refresh failed ({resp.status_code})")
    body = resp.json()
    new_access = (body.get("access_token") or "").strip()
    if not new_access:
        raise GoogleCalendarError("Google refresh did not return access token")
    cfg = dict(row.config or {})
    cfg["token_ciphertext"] = encrypt_token(new_access)
    cfg["expires_at"] = datetime.now(timezone.utc).timestamp() + float(body.get("expires_in") or 3600)
    row.config = cfg
    db.add(row)
    db.flush()
    return new_access


def create_google_event(db: Session, *, team_id: UUID, event: CalendarEvent) -> dict[str, Any]:
    token = get_valid_access_token(db, team_id=team_id)
    attendees = []
    for attendee in event.attendees or []:
        email = attendee.get("email") if isinstance(attendee, dict) else str(attendee)
        if email and "@" in email:
            attendees.append({"email": email})

    body: dict[str, Any] = {
        "summary": event.title,
        "description": event.description or "",
        "start": {"dateTime": event.start_at.isoformat(), "timeZone": event.timezone or "UTC"},
        "end": {"dateTime": event.end_at.isoformat(), "timeZone": event.timezone or "UTC"},
    }
    if event.location:
        body["location"] = event.location
    if attendees:
        body["attendees"] = attendees

    resp = requests.post(
        f"{GOOGLE_CALENDAR_API}/calendars/primary/events",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body,
        params={"sendUpdates": "all" if attendees else "none"},
        timeout=30,
    )
    if resp.status_code >= 400:
        raise GoogleCalendarError(f"Google Calendar create failed ({resp.status_code}): {resp.text[:300]}")
    data = resp.json()
    event.external_provider = "google"
    event.external_event_id = data.get("id")
    event.invite_status = "sent" if attendees else event.invite_status
    event.payload = {
        **(event.payload or {}),
        "google_html_link": data.get("htmlLink"),
        "google_meet_link": (data.get("conferenceData") or {}).get("entryPoints"),
    }
    db.add(event)
    return data


def list_google_events(db: Session, *, team_id: UUID, limit: int = 20) -> list[dict[str, Any]]:
    token = get_valid_access_token(db, team_id=team_id)
    now = datetime.now(timezone.utc).isoformat()
    resp = requests.get(
        f"{GOOGLE_CALENDAR_API}/calendars/primary/events",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "timeMin": now,
            "maxResults": limit,
            "singleEvents": "true",
            "orderBy": "startTime",
        },
        timeout=30,
    )
    if resp.status_code >= 400:
        raise GoogleCalendarError(f"Google Calendar list failed ({resp.status_code})")
    items = resp.json().get("items") or []
    out: list[dict[str, Any]] = []
    for item in items:
        start = item.get("start") or {}
        end = item.get("end") or {}
        out.append(
            {
                "id": f"google:{item.get('id')}",
                "title": item.get("summary") or "Google Calendar event",
                "description": item.get("description"),
                "start_at": start.get("dateTime") or start.get("date"),
                "end_at": end.get("dateTime") or end.get("date"),
                "timezone": start.get("timeZone") or "UTC",
                "location": item.get("location"),
                "meeting_url": item.get("htmlLink"),
                "attendees": [{"email": a.get("email"), "name": a.get("displayName")} for a in item.get("attendees") or []],
                "status": "scheduled",
                "invite_status": "external",
                "external_provider": "google",
                "external_event_id": item.get("id"),
                "payload": {"source": "google_calendar"},
            }
        )
    return out
