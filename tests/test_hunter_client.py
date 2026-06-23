"""Tests for Hunter.io contact client."""
import pytest

from app.services.hunter_client import (
    HunterClient,
    HunterConfigError,
    hunter_contact_enabled,
    pick_best_domain_email,
)


class _Response:
    status_code = 200

    def __init__(self, data):
        self._data = data
        self.content = b"{}"
        self.text = str(data)

    def json(self):
        return self._data


def test_hunter_requires_api_key(monkeypatch):
    monkeypatch.delenv("HUNTER_API_KEY", raising=False)
    with pytest.raises(HunterConfigError):
        HunterClient()


def test_hunter_enabled_by_default_with_key(monkeypatch):
    monkeypatch.setenv("HUNTER_API_KEY", "secret")
    monkeypatch.delenv("CONTACT_USE_HUNTER", raising=False)
    assert hunter_contact_enabled() is True


def test_hunter_disabled_when_opt_out(monkeypatch):
    monkeypatch.setenv("HUNTER_API_KEY", "secret")
    monkeypatch.setenv("CONTACT_USE_HUNTER", "false")
    assert hunter_contact_enabled() is False


def test_find_email_returns_normalized_prospect(monkeypatch):
    def fake_get(url, params, timeout):
        assert params["domain"] == "acme.com"
        assert params["first_name"] == "Jane"
        return _Response(
            {
                "data": {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "email": "jane.doe@acme.com",
                    "score": 92,
                    "domain": "acme.com",
                    "position": "VP Operations",
                    "company": "Acme",
                }
            }
        )

    monkeypatch.setattr("app.services.hunter_client.requests.get", fake_get)
    result = HunterClient(api_key="test-key").find_email(
        domain="https://www.acme.com",
        first_name="Jane",
        last_name="Doe",
    )
    assert result["email"] == "jane.doe@acme.com"
    assert result["title"] == "VP Operations"
    assert result["source"] == "hunter_finder"


def test_pick_best_domain_email_prefers_operations(monkeypatch):
    emails = [
        {"email": "press@acme.com", "confidence": 90, "position": "PR Manager", "department": "communication"},
        {"email": "ops@acme.com", "confidence": 75, "position": "Director of Operations", "department": "operations"},
    ]
    best = pick_best_domain_email(emails, industry="Logistics")
    assert best["email"] == "ops@acme.com"
