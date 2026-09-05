"""Internal calendar API for operator meetings."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.auth_deps import _require_user
from app.database import get_db
from app.models.calendar import CalendarEvent
from app.models.crm import TeamMember
from app.models.sales_agent import SalesOpportunity
from app.services.calendar_invite import attendee_emails, send_calendar_invite

logger = logging.getLogger(__name__)

router = APIRouter()


class CalendarEventIn(BaseModel):
    title: str = Field(..., max_length=240)
    description: Optional[str] = None
    start_at: datetime
    end_at: datetime
    timezone: str = Field("UTC", max_length=80)
    location: Optional[str] = Field(None, max_length=320)
    meeting_url: Optional[str] = Field(None, max_length=500)
    attendees: list[dict[str, Any] | str] = Field(default_factory=list)
    sales_opportunity_id: Optional[str] = None
    send_invites: bool = False
    sync_google: bool = True


def _uid_uuid(user: dict) -> uuid.UUID:
    return uuid.UUID(str(user["uid"]))


def _db_uuid(db: Session, value: uuid.UUID | str | None):
    if value is None:
        return None
    if db.bind and db.bind.dialect.name == "sqlite":
        return str(value)
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _team_ids_for_user(db: Session, uid: uuid.UUID) -> list[Any]:
    rows = db.query(TeamMember.team_id).filter(TeamMember.user_id == uid).all()
    return [_db_uuid(db, row[0]) for row in rows]


def _primary_team_id(db: Session, uid: uuid.UUID):
    team_ids = _team_ids_for_user(db, uid)
    return team_ids[0] if team_ids else None


def _normalize_attendees(attendees: list[dict[str, Any] | str]) -> list[dict[str, str]]:
    normalized = []
    seen: set[str] = set()
    for attendee in attendees or []:
        if isinstance(attendee, dict):
            email = str(attendee.get("email") or "").strip()
            name = str(attendee.get("name") or email).strip()
        else:
            email = str(attendee or "").strip()
            name = email
        if "@" not in email:
            continue
        key = email.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append({"email": email, "name": name or email})
    return normalized


def _serialize_event(row: CalendarEvent) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "team_id": str(row.team_id),
        "owner_user_id": str(row.owner_user_id) if row.owner_user_id else None,
        "sales_opportunity_id": str(row.sales_opportunity_id) if row.sales_opportunity_id else None,
        "crm_account_id": str(row.crm_account_id) if row.crm_account_id else None,
        "robot_company_id": row.robot_company_id,
        "title": row.title,
        "description": row.description,
        "start_at": row.start_at.isoformat() if row.start_at else None,
        "end_at": row.end_at.isoformat() if row.end_at else None,
        "timezone": row.timezone,
        "location": row.location,
        "meeting_url": row.meeting_url,
        "attendees": row.attendees or [],
        "status": row.status,
        "invite_status": row.invite_status,
        "ics_uid": row.ics_uid,
        "external_provider": row.external_provider,
        "external_event_id": row.external_event_id,
        "payload": row.payload or {},
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _event_or_404(db: Session, event_id: str, team_ids: list[Any]) -> CalendarEvent:
    row = db.query(CalendarEvent).filter(CalendarEvent.id == _db_uuid(db, event_id)).first()
    if not row or row.team_id not in team_ids:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    return row


@router.get("/events")
def list_events(db: Session = Depends(get_db), user: dict = Depends(_require_user)):
    team_ids = _team_ids_for_user(db, _uid_uuid(user))
    if not team_ids:
        return []
    rows = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.team_id.in_(team_ids))
        .order_by(CalendarEvent.start_at, desc(CalendarEvent.created_at))
        .limit(200)
        .all()
    )
    events = [_serialize_event(row) for row in rows]
    try:
        from uuid import UUID

        from app.services.google_calendar_sync import list_google_events

        raw_tid = team_ids[0]
        tid = raw_tid if isinstance(raw_tid, UUID) else UUID(str(raw_tid))
        events.extend(list_google_events(db, team_id=tid, limit=15))
    except Exception:
        logger.debug("Google Calendar merge skipped", exc_info=True)
    events.sort(key=lambda row: row.get("start_at") or "")
    return events[:200]


@router.post("/events")
def create_event(payload: CalendarEventIn, db: Session = Depends(get_db), user: dict = Depends(_require_user)):
    uid = _uid_uuid(user)
    team_id = _primary_team_id(db, uid)
    if not team_id:
        raise HTTPException(status_code=404, detail="No workspace found for user")
    if payload.end_at <= payload.start_at:
        raise HTTPException(status_code=400, detail="Meeting end time must be after start time")
    opportunity = None
    if payload.sales_opportunity_id:
        opportunity = (
            db.query(SalesOpportunity)
            .filter(SalesOpportunity.id == _db_uuid(db, payload.sales_opportunity_id), SalesOpportunity.team_id == team_id)
            .first()
        )
        if not opportunity:
            raise HTTPException(status_code=404, detail="Sales opportunity not found")
    event = CalendarEvent(
        id=str(uuid.uuid4()) if db.bind and db.bind.dialect.name == "sqlite" else uuid.uuid4(),
        team_id=team_id,
        owner_user_id=_db_uuid(db, uid),
        sales_opportunity_id=opportunity.id if opportunity else None,
        crm_account_id=opportunity.crm_account_id if opportunity else None,
        robot_company_id=opportunity.robot_company_id if opportunity and opportunity.robot_company_id else None,
        title=payload.title.strip(),
        description=payload.description,
        start_at=payload.start_at,
        end_at=payload.end_at,
        timezone=payload.timezone or "UTC",
        location=payload.location,
        meeting_url=payload.meeting_url,
        attendees=_normalize_attendees(payload.attendees),
        ics_uid=f"{uuid.uuid4()}@readyforrobots.com",
        payload={"source": "operator_calendar"},
    )
    db.add(event)
    db.flush()
    google_synced = False
    if payload.sync_google:
        try:
            from uuid import UUID

            from app.services.google_calendar_sync import create_google_event

            tid = team_id if isinstance(team_id, UUID) else UUID(str(team_id))
            create_google_event(db, team_id=tid, event=event)
            google_synced = True
        except Exception as exc:
            logger.warning("Google Calendar sync failed: %s", exc)
    if payload.send_invites and attendee_emails(event.attendees) and not google_synced:
        result = send_calendar_invite(event, organizer_email=user.get("email"))
        event.invite_status = "sent"
        event.payload = {**(event.payload or {}), "invite_resend_id": result.get("resend_id")}
    db.commit()
    db.refresh(event)
    return _serialize_event(event)


@router.post("/events/{event_id}/send-invite")
def send_invite(event_id: str, db: Session = Depends(get_db), user: dict = Depends(_require_user)):
    row = _event_or_404(db, event_id, _team_ids_for_user(db, _uid_uuid(user)))
    if not attendee_emails(row.attendees or []):
        raise HTTPException(status_code=400, detail="Add at least one attendee email before sending invites")
    result = send_calendar_invite(row, organizer_email=user.get("email"))
    row.invite_status = "sent"
    row.payload = {**(row.payload or {}), "invite_resend_id": result.get("resend_id"), "invite_sent_at": datetime.now(timezone.utc).isoformat()}
    db.commit()
    db.refresh(row)
    return _serialize_event(row)


@router.post("/events/{event_id}/cancel")
def cancel_event(event_id: str, db: Session = Depends(get_db), user: dict = Depends(_require_user)):
    row = _event_or_404(db, event_id, _team_ids_for_user(db, _uid_uuid(user)))
    row.status = "cancelled"
    db.commit()
    db.refresh(row)
    return _serialize_event(row)
