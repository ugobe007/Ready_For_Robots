from types import SimpleNamespace

import pytest

from app.services.cal_outreach_send import parse_cal_draft, send_cal_intro_email
from app.services.resend_email import ResendEmailError


def test_parse_cal_draft_with_subject_line():
    draft = "Subject: Hello there\n\nBody line one\nBody line two"
    subject, body = parse_cal_draft(draft, "Acme")
    assert subject == "Hello there"
    assert "Body line one" in body


def test_parse_cal_draft_fallback_subject():
    subject, body = parse_cal_draft("Just a body", "Acme Robotics")
    assert subject == "Robot automation partnership — Acme Robotics"
    assert body == "Just a body"


def test_send_cal_intro_blocks_unverified_generic_role_inbox(monkeypatch):
    db = SimpleNamespace(add=lambda *_: None, flush=lambda: None)
    acct = SimpleNamespace(id=7, company_id=11, outreach_sent_at=None, outreach_stage=None)
    company = SimpleNamespace(id=11, crm_metadata={})

    called = {"n": 0}

    def _never_send(**_kwargs):
        called["n"] += 1
        return {"resend_id": "x", "from_email": "cal@readyforrobots.com"}

    monkeypatch.setattr("app.services.cal_outreach_send.send_cal_email_via_resend", _never_send)

    with pytest.raises(ResendEmailError, match="Blocked generic role inbox"):
        send_cal_intro_email(
            db,
            acct=acct,
            company=company,
            team_id=1,
            to_email="info@acme.com",
            subject="Hello",
            body_text="Body",
            idempotency_key="k1",
            email_source="domain_inferred",
        )

    assert called["n"] == 0


def test_send_cal_intro_allows_verified_source_for_generic_role_inbox(monkeypatch):
    db = SimpleNamespace(add=lambda *_: None, flush=lambda: None)
    acct = SimpleNamespace(id=9, company_id=12, outreach_sent_at=None, outreach_stage=None)
    company = SimpleNamespace(id=12, crm_metadata={})

    def _send_ok(**_kwargs):
        return {"resend_id": "r-123", "from_email": "cal@readyforrobots.com"}

    monkeypatch.setattr("app.services.cal_outreach_send.send_cal_email_via_resend", _send_ok)

    msg = send_cal_intro_email(
        db,
        acct=acct,
        company=company,
        team_id=1,
        to_email="info@acme.com",
        subject="Hello",
        body_text="Body",
        idempotency_key="k2",
        email_source="apollo",
    )
    assert msg.to_email == "info@acme.com"
