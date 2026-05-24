"""Tests for lead enrichment waterfall."""
from unittest.mock import MagicMock, patch

from app.services.lead_enrichment import (
    infer_sales_email,
    resolve_outreach_email,
    verify_email_deliverable,
)


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

    email, source = resolve_outreach_email(company, acct, use_apollo=False)
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
        email, source = resolve_outreach_email(company, acct, use_apollo=False)
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

    with patch.dict("os.environ", {"APOLLO_API_KEY": "test-key"}):
        email, source = resolve_outreach_email(company, acct, use_apollo=True)
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
