from datetime import datetime, timezone
import uuid

import app.models  # noqa: F401
from app.models.calendar import CalendarEvent
from app.services import calendar_invite
from app.services.calendar_invite import attendee_emails, calendar_event_ics, send_calendar_invite


def _event():
    return CalendarEvent(
        id=uuid.uuid4(),
        team_id=uuid.uuid4(),
        title="Intro call",
        description="Discuss next steps.",
        start_at=datetime(2026, 5, 16, 17, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 5, 16, 17, 30, tzinfo=timezone.utc),
        timezone="UTC",
        meeting_url="https://meet.example.com/abc",
        attendees=[{"email": "buyer@example.com", "name": "Buyer"}],
        ics_uid="event-1@readyforrobots.com",
    )


def test_calendar_event_ics_contains_invite_fields():
    ics = calendar_event_ics(_event(), organizer_email="operator@example.com")

    assert "BEGIN:VCALENDAR" in ics
    assert "METHOD:REQUEST" in ics
    assert "SUMMARY:Intro call" in ics
    assert "ATTENDEE;CN=Buyer" in ics
    assert "MAILTO:buyer@example.com" in ics


def test_attendee_emails_dedupes_values():
    assert attendee_emails([{"email": "buyer@example.com"}, "buyer@example.com", "ops@example.com"]) == [
        "buyer@example.com",
        "ops@example.com",
    ]


def test_send_calendar_invite_uses_ics_attachment(monkeypatch):
    sent = {}

    def fake_send(**kwargs):
        sent.update(kwargs)
        return {"resend_id": "email_invite"}

    monkeypatch.setattr(calendar_invite, "send_email_via_resend", fake_send)

    result = send_calendar_invite(_event(), organizer_email="operator@example.com")

    assert result["resend_id"] == "email_invite"
    assert sent["to_email"] == ["buyer@example.com"]
    assert sent["attachments"][0]["filename"] == "invite.ics"
    assert sent["attachments"][0]["content_type"].startswith("text/calendar")
