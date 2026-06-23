"""Tests for lead enrichment waterfall."""
from unittest.mock import MagicMock, patch

from app.services.lead_enrichment import (
    infer_sales_email,
    persist_outreach_contact,
    resolve_outreach_email,
    verify_email_deliverable,
)


def test_persist_outreach_contact_writes_row_and_metadata():
    company = MagicMock()
    company.id = 42
    company.crm_metadata = {}
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    created = persist_outreach_contact(
        company,
        db,
        email="operations@acme.com",
        source="domain_inferred",
    )
    assert created is True
    assert company.crm_metadata["outreach_email"] == "operations@acme.com"
    assert company.crm_metadata["outreach_email_source"] == "domain_inferred"
    db.add.assert_called()


def test_infer_sales_email():
    assert infer_sales_email("acme.com") == "operations@acme.com"
    assert infer_sales_email("acme.com", "Logistics") == "plantmanager@acme.com"
    assert infer_sales_email(None) is None


def test_resolve_outreach_email_prefers_crm_contact():
    company = MagicMock()
    company.name = "Acme"
    company.website = "https://acme.com"
    company.industry = "Logistics"
    acct = MagicMock()
    acct.contact_email = "buyer@acme.com"
    acct.website = None
    acct.industry = None

    email, source = resolve_outreach_email(company, acct, use_apollo=False)[:2]
    assert email == "buyer@acme.com"
    assert source == "crm_contact"


def test_resolve_outreach_email_falls_back_to_domain():
    company = MagicMock()
    company.name = "Acme"
    company.website = "https://www.acme.com"
    company.industry = "Logistics"
    acct = MagicMock()
    acct.contact_email = None
    acct.website = None
    acct.industry = None

    with patch.dict("os.environ", {}, clear=True):
        email, source = resolve_outreach_email(company, acct, use_apollo=False)[:2]
    assert email == "plantmanager@acme.com"
    assert source == "domain_inferred"
    assert acct.contact_email == "plantmanager@acme.com"


def test_resolve_outreach_email_uses_acct_website():
    company = MagicMock()
    company.name = "Acme"
    company.website = None
    company.industry = "Logistics"
    acct = MagicMock()
    acct.contact_email = None
    acct.website = "https://acme.com"
    acct.industry = None

    with patch.dict("os.environ", {}, clear=True):
        email, source = resolve_outreach_email(company, acct, use_apollo=False)[:2]
    assert email == "plantmanager@acme.com"
    assert source == "domain_inferred"


@patch("app.services.lead_enrichment.apollo_contact_email")
def test_resolve_outreach_email_uses_apollo(mock_apollo):
    mock_apollo.return_value = {"email": "vp@acme.com", "email_status": "verified"}
    company = MagicMock()
    company.name = "Acme"
    company.website = "https://acme.com"
    company.industry = "Logistics"
    acct = MagicMock()
    acct.contact_email = None
    acct.website = None
    acct.industry = None

    with patch.dict("os.environ", {"APOLLO_API_KEY": "test-key", "CONTACT_USE_APOLLO": "true"}):
        email, source = resolve_outreach_email(company, acct, use_apollo=True)[:2]
    assert email == "vp@acme.com"
    assert source == "apollo"
    assert acct.contact_email == "vp@acme.com"


def test_verify_email_rejects_bad_format():
    ok, reason = verify_email_deliverable("not-an-email")
    assert ok is False
    assert reason == "invalid_format"


def test_verify_email_rejects_noreply():
    ok, reason = verify_email_deliverable("noreply@example.com")
    assert ok is False
    assert reason == "role_blocked"
