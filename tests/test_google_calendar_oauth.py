"""Google Calendar OAuth helpers."""
from unittest.mock import MagicMock, patch

from app.services.google_calendar_oauth import (
    GoogleCalendarError,
    redirect_uri,
    verify_google_calendar_access_token,
)


def test_redirect_uri_defaults_to_fly_callback(monkeypatch):
    monkeypatch.delenv("GOOGLE_CALENDAR_REDIRECT_URI", raising=False)
    monkeypatch.delenv("PUBLIC_API_URL", raising=False)
    assert redirect_uri() == "https://ready-2-robot.fly.dev/api/integrations/google-calendar/callback"


@patch("app.services.google_calendar_oauth.requests.get")
def test_verify_uses_primary_events_not_calendar_list(mock_get):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"items": []})
    result = verify_google_calendar_access_token("ya29.test")
    assert result["verified"] is True
    called_url = mock_get.call_args[0][0]
    assert "/calendars/primary/events" in called_url
    assert "calendarList" not in called_url


@patch("app.services.google_calendar_oauth.requests.get")
def test_verify_rejects_401(mock_get):
    mock_get.return_value = MagicMock(status_code=401, text="Unauthorized")
    try:
        verify_google_calendar_access_token("bad")
        assert False, "expected GoogleCalendarError"
    except GoogleCalendarError as exc:
        assert "rejected" in str(exc).lower()
