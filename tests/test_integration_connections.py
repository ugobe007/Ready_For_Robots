"""Integration connect/disconnect service tests."""
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.integration_connections import (
    PROVIDER_GITHUB,
    PROVIDER_HUBSPOT,
    IntegrationError,
    connect_provider,
    disconnect_provider,
    get_provider_token,
    serialize_provider_status,
    verify_provider_token,
)
from app.services.integration_tokens import decrypt_token, encrypt_token


def test_token_roundtrip():
    raw = "pat-na1-test-token-12345"
    assert decrypt_token(encrypt_token(raw)) == raw


@patch("app.services.integration_connections.requests.get")
def test_verify_github_token(mock_get):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"login": "acme", "name": "Acme", "type": "User"})
    result = verify_provider_token(PROVIDER_GITHUB, "ghp_test")
    assert result["account_login"] == "acme"
    mock_get.assert_called_once()


@patch("app.services.integration_connections.requests.get")
def test_verify_hubspot_token_rejects_401(mock_get):
    mock_get.return_value = MagicMock(status_code=401)
    try:
        verify_provider_token(PROVIDER_HUBSPOT, "bad-token")
        assert False, "expected IntegrationError"
    except IntegrationError as exc:
        assert "rejected" in str(exc).lower()


@patch("app.services.integration_connections.verify_provider_token")
def test_connect_and_disconnect_provider(mock_verify):
    mock_verify.return_value = {"verified": True, "account_login": "acme"}
    db = MagicMock()
    team_id = uuid4()
    user_id = uuid4()

    row = connect_provider(
        db,
        team_id=team_id,
        user_id=user_id,
        provider=PROVIDER_GITHUB,
        token="ghp_test",
    )
    assert row.status == "active"
    assert row.config["provider"] == PROVIDER_GITHUB
    db.commit.assert_called()

    with patch("app.services.integration_connections._find_connection", return_value=row):
        token = get_provider_token(db, team_id=team_id, provider=PROVIDER_GITHUB)
        assert token == "ghp_test"

        assert disconnect_provider(db, team_id=team_id, provider=PROVIDER_GITHUB) is True
        db.delete.assert_called_with(row)


def test_serialize_provider_status_not_connected():
    payload = serialize_provider_status(PROVIDER_HUBSPOT, row=None, entitled=False, entitlement_message="Upgrade")
    assert payload["connected"] is False
    assert payload["entitled"] is False
    assert payload["docs_url"]
