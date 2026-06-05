"""HubSpot OAuth sync settings tests."""
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.hubspot_oauth import get_sync_settings, is_configured, update_sync_settings


def test_is_configured_false_without_env():
    with patch.dict("os.environ", {}, clear=True):
        assert is_configured() is False


def test_sync_settings_defaults_when_disconnected():
    db = MagicMock()
    with patch("app.services.hubspot_oauth._find_connection", return_value=None):
        payload = get_sync_settings(db, team_id=uuid4())
    assert payload["connected"] is False
    assert payload["sync_mode"] == "auto_all"


def test_update_sync_settings_requires_connection():
    db = MagicMock()
    with patch("app.services.hubspot_oauth._find_connection", return_value=None):
        try:
            update_sync_settings(db, team_id=uuid4(), sync_mode="auto_all", sync_lead_ids=[])
            assert False, "expected error"
        except Exception as exc:
            assert "Connect HubSpot" in str(exc)
