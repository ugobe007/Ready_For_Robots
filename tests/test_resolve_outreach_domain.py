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


def test_resolve_from_brand_slug_when_no_website():
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
