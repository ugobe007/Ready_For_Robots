"""Tests for email address normalization."""
from app.services.email_address import normalize_recipient_email, recipient_email_error


def test_normalize_plain_email():
    assert normalize_recipient_email("Ops@LifePointHealth.COM") == "ops@lifepointhealth.com"


def test_normalize_named_format():
    assert normalize_recipient_email("LifePoint Health <procurement@lifepointhealth.com>") == (
        "procurement@lifepointhealth.com"
    )


def test_reject_company_name_only():
    assert normalize_recipient_email("LifePoint Health") is None
    assert "not an email" in (recipient_email_error("LifePoint Health") or "")


def test_reject_bare_domain():
    assert normalize_recipient_email("lifepointhealth.com") is None


def test_reject_missing_tld():
    assert normalize_recipient_email("ops@lifepoint") is None


def test_first_valid_from_list():
    assert normalize_recipient_email("bad name, ops@lifepointhealth.com") == "ops@lifepointhealth.com"
