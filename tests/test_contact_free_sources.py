"""Tests for free contact discovery (Apollo alternative)."""
from unittest.mock import MagicMock, patch

from app.services.contact_free_sources import (
    apollo_contact_enabled,
    extract_emails_from_text,
    infer_person_email_from_decision_makers,
    pick_signal_outreach_email,
)
from app.services.lead_enrichment import resolve_outreach_email


def test_apollo_disabled_by_default_even_with_key():
    with patch.dict("os.environ", {"APOLLO_API_KEY": "secret"}, clear=False):
        assert apollo_contact_enabled() is False


def test_apollo_enabled_when_opt_in():
    with patch.dict(
        "os.environ",
        {"APOLLO_API_KEY": "secret", "CONTACT_USE_APOLLO": "true"},
        clear=False,
    ):
        assert apollo_contact_enabled() is True


def test_pick_signal_email_prefers_company_domain():
    text = "Reach ops at operations@acme.com or media@acme.com for comment."
    assert pick_signal_outreach_email([text], "acme.com") == "operations@acme.com"


def test_extract_emails_skips_noreply():
    emails = extract_emails_from_text("noreply@acme.com and sales@acme.com", domain="acme.com")
    assert emails == ["sales@acme.com"]


def test_person_email_from_decision_makers():
    company = MagicMock()
    company.crm_metadata = {
        "decision_makers": [{"first_name": "Jane", "last_name": "Doe", "title": "VP Operations"}]
    }
    email, pattern, title = infer_person_email_from_decision_makers(company, [], "acme.com")
    assert email == "jane.doe@acme.com"
    assert pattern == "first.last"
    assert title == "VP Operations"


@patch("app.services.lead_enrichment.hunter_contact_email", return_value=None)
def test_resolve_outreach_email_uses_signal_before_role_inbox(mock_hunter):
    company = MagicMock()
    company.name = "Acme"
    company.website = "https://acme.com"
    company.industry = "Logistics"
    company.crm_metadata = {}
    acct = MagicMock()
    acct.contact_email = None
    acct.website = None
    acct.industry = None

    with patch.dict("os.environ", {}, clear=True):
        email, source = resolve_outreach_email(
            company,
            acct,
            use_apollo=False,
            signal_texts=["Contact automation@acme.com for pilot details."],
        )[:2]
    assert email == "automation@acme.com"
    assert source == "signal_email"
