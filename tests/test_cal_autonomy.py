"""Cal autonomy — review email resolution and template fingerprint."""
from __future__ import annotations

import os

import pytest

from app.services.cal_autonomy import (
    cal_buyer_outreach_body,
    format_cal_draft_storage,
    get_cal_review_email,
    outreach_template_fingerprint,
)


def test_get_cal_review_email_prefers_admin_email(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "ops@example.com")
    monkeypatch.setenv("ADMIN_EMAILS", "other@example.com")
    assert get_cal_review_email() == "ops@example.com"


def test_get_cal_review_email_falls_back_to_admin_emails(monkeypatch):
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.setenv("ADMIN_EMAILS", "first@example.com,second@example.com")
    assert get_cal_review_email() == "first@example.com"


def test_outreach_template_fingerprint_stable(monkeypatch):
    monkeypatch.setenv("CAL_TEMPLATE_VERSION", "test-1")
    fp1 = outreach_template_fingerprint()
    fp2 = outreach_template_fingerprint()
    assert fp1 == fp2
    assert len(fp1) == 20


def test_format_cal_draft_storage_includes_subject():
    text = format_cal_draft_storage("Hello there", "Body line")
    assert text.startswith("Subject: Hello there")
    assert "Body line" in text


def test_cal_buyer_outreach_body_mentions_cal():
    body = cal_buyer_outreach_body(
        type("Co", (), {"name": "Acme Logistics", "industry": "Logistics"})(),
        fresh=False,
    )
    assert "Cal from Ready For Robots" in body
    assert "Acme Logistics" in body
    assert "Ready For Robots" in body


def test_cal_vendor_outreach_body_sherpa_tone():
    from app.services.cal_autonomy import cal_vendor_outreach_body

    body = cal_vendor_outreach_body(
        type("Co", (), {"name": "DexMate Robotics", "industry": "Logistics"})(),
        fresh=False,
    )
    assert "DexMate Robotics" in body
    assert "PoC" in body or "PoCs" in body or "pilot" in body.lower()
    assert "engineer-led" in body.lower() or "guide" in body.lower()
