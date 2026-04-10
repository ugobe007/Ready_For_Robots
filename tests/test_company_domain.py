"""Domain normalization and ordered dedupe (entity resolution)."""

from types import SimpleNamespace

from app.services.company_domain import dedupe_companies_ordered, normalize_website_domain


def test_normalize_strips_www_and_scheme():
    assert normalize_website_domain("https://WWW.Example.com/path") == "example.com"
    assert normalize_website_domain("example.com") == "example.com"


def test_dedupe_keeps_first_domain_then_skips_second():
    a = SimpleNamespace(name="Acme", website="https://acme.com", website_domain="acme.com", signals=[], scores=[])
    b = SimpleNamespace(name="Acme Inc", website="http://www.acme.com", website_domain="acme.com", signals=[], scores=[])
    assert dedupe_companies_ordered([a, b]) == [a]


def test_dedupe_keeps_first_name_without_domain_conflict():
    a = SimpleNamespace(name="Globex", website=None, website_domain=None, signals=[], scores=[])
    b = SimpleNamespace(name="Globex", website=None, website_domain=None, signals=[], scores=[])
    assert dedupe_companies_ordered([a, b]) == [a]
