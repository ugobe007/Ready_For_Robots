"""Cal autonomy — review email resolution and template fingerprint."""
from __future__ import annotations

import os

import pytest

from app.services.cal_autonomy import (
    _cal_buyer_eligible,
    cal_buyer_outreach_body,
    cal_buyer_sales_enabled,
    format_cal_draft_storage,
    get_cal_autonomy_status,
    get_cal_review_email,
    outreach_template_fingerprint,
    prioritize_unsent,
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


class _StubAcct:
    def __init__(self, sent_at=None):
        self.outreach_sent_at = sent_at


def _entry(cid, score):
    return (type("Co", (), {"id": cid, "name": f"Co{cid}"})(), score, "HOT")


def test_prioritize_unsent_moves_never_sent_to_front():
    # score order: c1 (sent), c2 (unsent), c3 (sent), c4 (unsent)
    companies = [_entry(1, 90), _entry(2, 80), _entry(3, 70), _entry(4, 60)]
    accts = {
        1: _StubAcct(sent_at="2026-07-01T00:00:00Z"),
        2: _StubAcct(sent_at=None),
        3: _StubAcct(sent_at="2026-07-02T00:00:00Z"),
        4: _StubAcct(sent_at=None),
    }
    ordered = prioritize_unsent(companies, accts)
    ids = [c.id for c, _, _ in ordered]
    # Unsent (2, 4) first in score order, then already-sent (1, 3) in score order.
    assert ids == [2, 4, 1, 3]


def test_prioritize_unsent_treats_missing_account_as_unsent():
    companies = [_entry(1, 90), _entry(2, 80)]
    accts = {1: _StubAcct(sent_at="2026-07-01T00:00:00Z")}  # c2 has no account yet
    ordered = prioritize_unsent(companies, accts)
    assert [c.id for c, _, _ in ordered] == [2, 1]


def test_prioritize_unsent_stable_when_all_unsent():
    companies = [_entry(1, 90), _entry(2, 80), _entry(3, 70)]
    accts = {1: _StubAcct(), 2: _StubAcct(), 3: _StubAcct()}
    ordered = prioritize_unsent(companies, accts)
    assert [c.id for c, _, _ in ordered] == [1, 2, 3]


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
    assert "ReadyForRobots" in body or "Ready For Robots" in body


def test_cal_vendor_outreach_body_sherpa_tone():
    from app.services.cal_autonomy import cal_vendor_outreach_body

    body = cal_vendor_outreach_body(
        type("Co", (), {"name": "DexMate Robotics", "industry": "Logistics"})(),
        fresh=False,
    )
    assert "DexMate Robotics" in body
    assert "PoC" in body or "PoCs" in body or "pilot" in body.lower()
    assert "engineer-led" in body.lower() or "guide" in body.lower()


def test_cal_buyer_sales_disabled_by_default(monkeypatch):
    monkeypatch.delenv("CAL_BUYER_SALES_ENABLED", raising=False)
    assert cal_buyer_sales_enabled() is False
    status = get_cal_autonomy_status()
    assert status["buyer_sales_enabled"] is False
    assert status["send_limit"] == 0
    assert status["draft_batch"] == 0


def test_cal_buyer_sales_enabled_when_flagged(monkeypatch):
    monkeypatch.setenv("CAL_BUYER_SALES_ENABLED", "1")
    monkeypatch.setenv("CAL_AUTONOMY_SEND_LIMIT", "25")
    monkeypatch.setenv("CAL_AUTONOMY_DRAFT_BATCH", "100")
    assert cal_buyer_sales_enabled() is True
    status = get_cal_autonomy_status()
    assert status["buyer_sales_enabled"] is True
    assert status["send_limit"] == 25
    assert status["draft_batch"] == 100
