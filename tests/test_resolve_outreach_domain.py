"""Tests for resolve_outreach_domain brand-slug fallback."""
from unittest.mock import MagicMock

from app.services.company_domain import persist_company_domain, resolve_outreach_domain


def test_resolve_from_company_website():
    company = MagicMock()
    company.website = "https://www.acme.com/about"
    company.website_domain = None
    company.name = "Acme Corp"
    assert resolve_outreach_domain(company) == "acme.com"


def test_resolve_from_website_domain_column():
    company = MagicMock()
    company.website = None
    company.website_domain = "acme.com"
    company.name = "Acme Corp"
    assert resolve_outreach_domain(company) == "acme.com"


def test_brand_slug_disabled_by_default(monkeypatch):
    # Brand-slug inference fabricates domains that resolve but belong to someone else
    # (the dominant bounce class). It is OFF by default — a name with no real website
    # must not produce a domain.
    monkeypatch.delenv("CAL_ALLOW_BRAND_SLUG_DOMAIN", raising=False)
    company = MagicMock()
    company.website = None
    company.website_domain = None
    company.name = "Marriott International"
    assert resolve_outreach_domain(company) is None


def test_brand_slug_opt_in_when_flag_enabled(monkeypatch):
    monkeypatch.setenv("CAL_ALLOW_BRAND_SLUG_DOMAIN", "1")
    company = MagicMock()
    company.website = None
    company.website_domain = None
    company.name = "Marriott International"
    assert resolve_outreach_domain(company) == "marriott.com"


def test_resolve_from_acct_website():
    company = MagicMock()
    company.website = None
    company.website_domain = None
    company.name = "Unknown"
    acct = MagicMock()
    acct.website = "https://dhl.com"
    assert resolve_outreach_domain(company, acct) == "dhl.com"


def test_persist_company_domain_sets_website():
    company = MagicMock()
    company.website = None
    persist_company_domain(company, "marriott.com")
    assert company.website == "https://marriott.com"
    assert company.website_domain == "marriott.com"


def test_q_casino_does_not_resolve_to_casino_com():
    company = MagicMock()
    company.website = "https://casino.com"
    company.website_domain = None
    company.name = "Q Casino"
    assert resolve_outreach_domain(company) == "qcasinoandresort.com"


def test_generic_casino_com_is_untrusted():
    from app.services.company_domain import is_trusted_outreach_domain

    assert is_trusted_outreach_domain("casino.com") is False
    assert is_trusted_outreach_domain("qcasinoandresort.com") is True
