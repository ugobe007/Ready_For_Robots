"""Supply autonomy, onboarding email, founding customer helpers."""
from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from app.services.onboarding_email import welcome_email_body
from app.services.supply_autonomy import (
    append_signup_cta,
    outreach_template_fingerprint,
    supply_autonomy_enabled,
)


def test_supply_autonomy_enabled_default(monkeypatch):
    monkeypatch.delenv("SUPPLY_AUTONOMY_ENABLED", raising=False)
    monkeypatch.setenv("ENABLE_SCHEDULED_SUPPLY_AUTONOMY", "1")
    assert supply_autonomy_enabled() is True


def test_append_signup_cta_adds_signup_link():
    rc = SimpleNamespace(website=None)
    body = append_signup_cta("Hello vendor team.", rc)
    assert "readyforrobots.com/signup" in body


def test_append_signup_cta_uses_results_url_when_website():
    rc = SimpleNamespace(website="https://robots.example.com")
    body = append_signup_cta("Hello vendor team.", rc)
    assert "/results?url=" in body


def test_supply_template_fingerprint_stable(monkeypatch):
    monkeypatch.setenv("SUPPLY_TEMPLATE_VERSION", "test-1")
    fp1 = outreach_template_fingerprint()
    fp2 = outreach_template_fingerprint()
    assert fp1 == fp2
    assert len(fp1) == 20


def test_welcome_email_body_mentions_pipeline():
    body = welcome_email_body(display_name="Alex")
    assert "Alex" in body
    assert "/pipeline" in body
    assert "Ready For Robots" in body
