"""Brand isolation: Cal must never cross StageGate <-> Ready For Robots."""
from types import SimpleNamespace

import pytest

from app.services.brand import (
    BRAND_RFR,
    BRAND_STAGEGATE,
    BrandViolation,
    assert_send_brand_consistent,
    company_brand,
    content_brand,
    sender_brand,
)


def test_content_brand_detects_stagegate():
    assert content_brand("Sales channel signals for Keenon", "I'm Cal with StageGate") == BRAND_STAGEGATE
    assert content_brand("Register at onstage.bot") == BRAND_STAGEGATE
    assert content_brand("we help with bonded warehousing") == BRAND_STAGEGATE


def test_content_brand_defaults_to_rfr():
    assert content_brand("Buyer matches for Acme", "3 buyer leads from Ready For Robots") == BRAND_RFR


def test_sender_brand_by_domain():
    assert sender_brand("signal@readyforrobots.com") == BRAND_RFR
    assert sender_brand("supply+tok@reply.readyforrobots.com") == BRAND_RFR
    assert sender_brand("cal@onstage.bot") == BRAND_STAGEGATE
    assert sender_brand("Cal <cal@onstage.bot>") == BRAND_STAGEGATE
    assert sender_brand("someone@unknown.example") is None


def test_company_brand_from_metadata_and_source():
    stagegate_acct = SimpleNamespace(crm_metadata={"outreach_pipeline": "stagegate"})
    assert company_brand(acct=stagegate_acct) == BRAND_STAGEGATE
    stagegate_co = SimpleNamespace(data_source="stagegate_oem", crm_metadata={})
    assert company_brand(company=stagegate_co) == BRAND_STAGEGATE
    mi_co = SimpleNamespace(market_intelligence={"stagegate_oem": {"oem_need_score": 80}}, crm_metadata={})
    assert company_brand(company=mi_co) == BRAND_STAGEGATE
    buyer = SimpleNamespace(crm_metadata={}, data_source="serp", market_intelligence={})
    assert company_brand(company=buyer) == BRAND_RFR


def test_stagegate_copy_from_rfr_domain_is_blocked():
    with pytest.raises(BrandViolation):
        assert_send_brand_consistent(
            from_email="signal@readyforrobots.com",
            subject="Sales channel signals for Keenon Robotics",
            body_text="I'm Cal with StageGate — onstage.bot",
        )


def test_rfr_copy_from_stagegate_domain_is_blocked():
    with pytest.raises(BrandViolation):
        assert_send_brand_consistent(
            from_email="cal@onstage.bot",
            subject="Buyer matches for Acme",
            body_text="Here are 3 buyer leads from Ready For Robots.",
        )


def test_matching_brands_pass():
    # StageGate copy from a StageGate address is allowed.
    assert_send_brand_consistent(
        from_email="cal@onstage.bot",
        subject="Show logistics for CES",
        body_text="StageGate can stage and test your robots. onstage.bot",
    )
    # RFR copy from RFR address is allowed.
    assert_send_brand_consistent(
        from_email="signal@readyforrobots.com",
        subject="Buyer matches for Acme",
        body_text="3 buyer leads from Ready For Robots.",
    )


def test_stagegate_content_from_unknown_sender_is_blocked():
    # Unknown sender defaults to RFR identity, so StageGate content is still blocked.
    with pytest.raises(BrandViolation):
        assert_send_brand_consistent(
            from_email="whoever@unknown.example",
            subject="hi",
            body_text="register at onstage.bot",
        )


def test_send_guard_blocks_stagegate_from_rfr(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "test")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "signal@readyforrobots.com")
    from app.services.resend_email import ResendEmailError, send_email_via_resend

    with pytest.raises(ResendEmailError) as exc:
        send_email_via_resend(
            to_email="x@example.com",
            subject="Sales channel signals for Keenon",
            body_text="I'm Cal with StageGate · onstage.bot",
        )
    assert "brand isolation" in str(exc.value).lower()


def test_cal_buyer_loop_rejects_stagegate_account():
    from app.services.cal_autonomy import _cal_buyer_eligible

    company = SimpleNamespace(
        name="Keenon Robotics",
        website="https://keenonrobot.com",
        industry="Robotics",
        sub_industry="",
        crm_metadata={"outreach_pipeline": "stagegate"},
        data_source="stagegate_oem",
        market_intelligence={"stagegate_oem": {}},
    )
    eligible, reason = _cal_buyer_eligible(company, None)
    assert eligible is False
    assert "stagegate" in reason.lower()
