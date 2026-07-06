"""Cal autonomy — review email resolution and template fingerprint."""
from __future__ import annotations

import os

import pytest

from app.services.cal_autonomy import (
    _cal_buyer_eligible,
    cal_buyer_outreach_body,
    format_cal_draft_storage,
    get_cal_review_email,
    outreach_template_fingerprint,
)


class _StubCompany:
    def __init__(self, name, industry="", sub_industry="", website=None, website_domain=None):
        self.name = name
        self.industry = industry
        self.sub_industry = sub_industry
        self.website = website
        self.website_domain = website_domain


def test_cal_buyer_eligible_blocks_robot_vendor():
    ok, reason = _cal_buyer_eligible(_StubCompany("Fanuc America", "Automation"))
    assert ok is False
    assert "junk/vendor" in reason


def test_cal_buyer_eligible_blocks_pure_publisher():
    ok, reason = _cal_buyer_eligible(
        _StubCompany("Globex Holdings", "Publishing", website="https://globexholdings.com")
    )
    assert ok is False
    assert "off-ICP" in reason


def test_cal_buyer_eligible_allows_hospitality_service_robot_buyer():
    # Hotels/airlines/casinos are deliberate service/cleaning-robot buyers and
    # must be eligible when they have a real domain (send-time gates handle safety).
    ok, _ = _cal_buyer_eligible(
        _StubCompany("Marriott International", "Hospitality", website="https://marriott.com")
    )
    assert ok is True


def test_cal_buyer_eligible_blocks_no_domain_fragment():
    ok, reason = _cal_buyer_eligible(_StubCompany("The 15 coolest things I saw", "Media"))
    assert ok is False
    assert "domain" in reason


def test_cal_buyer_eligible_allows_real_buyer():
    ok, _ = _cal_buyer_eligible(
        _StubCompany("LifePoint Health", "Healthcare", website="https://lifepointhealth.net")
    )
    assert ok is True


def test_cal_buyer_eligible_in_icp_override_beats_mislabeled_industry():
    # "Amazon Fulfillment" mislabeled as hospitality must still qualify.
    ok, _ = _cal_buyer_eligible(
        _StubCompany("Amazon Fulfillment", "Hospitality", website="https://amazon.com")
    )
    assert ok is True


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
    assert "Cal" in body
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
