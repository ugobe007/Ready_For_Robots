"""Tests for lead enrichment waterfall."""
from unittest.mock import MagicMock, patch

from app.services.lead_enrichment import (
    infer_sales_email,
    outreach_recipient_trusted,
    persist_outreach_contact,
    resolve_outreach_email,
    verify_email_deliverable,
)


def _company(name="Hawaiian Airlines", website="https://hawaiianairlines.com", website_domain=None):
    c = MagicMock()
    c.name = name
    c.website = website
    c.website_domain = website_domain
    return c


def test_recipient_trusted_rejects_guessed_domain():
    # "Hawaiian Airlines" real site is hawaiianairlines.com; hawaiian.com is a name-guess.
    ok, reason = outreach_recipient_trusted(
        _company(), None, "automation@hawaiian.com", "domain_inferred"
    )
    assert ok is False
    assert "unverified" in reason


def test_recipient_trusted_rejects_guessed_role_inbox_on_real_domain():
    # Hardened: a guessed role inbox even on the real domain is NOT trusted —
    # info@/sales@ frequently do not exist and were the dominant bounce class.
    ok, reason = outreach_recipient_trusted(
        _company(), None, "sales@hawaiianairlines.com", "domain_inferred"
    )
    assert ok is False
    assert "unverified" in reason


def test_recipient_trusted_allows_hunter_domain_hit():
    # Hunter domain-search hits are verified real people at the company.
    ok, _ = outreach_recipient_trusted(
        _company(), None, "christian.nice@hawaiianairlines.com", "hunter_domain"
    )
    assert ok is True


def test_recipient_trusted_allows_verified_provider_any_domain():
    # Apollo/Hunter emails are verified even if the domain differs from the website field.
    ok, _ = outreach_recipient_trusted(_company(), None, "cto@corp-mail.com", "apollo")
    assert ok is True


def test_recipient_trusted_rejects_when_no_website():
    ok, reason = outreach_recipient_trusted(
        _company(website=None), None, "facilities@voluntary.com", "crm_contact"
    )
    assert ok is False
    assert "no-website" in reason


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
