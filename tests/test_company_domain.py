"""Domain normalization and ordered dedupe (entity resolution)."""

from types import SimpleNamespace

from app.services.company_domain import (
    company_entity_dedupe_keys,
    dedupe_companies_ordered,
    dedupe_lead_payloads_ordered,
    normalize_company_name_key,
    normalize_website_domain,
)


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


def test_normalize_company_name_key_airline_variants():
    assert normalize_company_name_key("Japan airline") == "japan airlines"
    assert normalize_company_name_key("Japan Airlines Co., Ltd.") == "japan airlines"
    assert normalize_company_name_key("Choice Hotels International") == "choice hotels"


def test_japan_airlines_duplicate_rows_collapse():
    a = SimpleNamespace(
        name="Japan Airlines",
        website="https://japan.com",
        website_domain="japan.com",
        signals=[],
        scores=[],
    )
    b = SimpleNamespace(
        name="Japan airline",
        website="https://www.jal.co.jp/en/",
        website_domain="jal.co.jp",
        signals=[],
        scores=[],
    )
    assert dedupe_companies_ordered([a, b]) == [a]
    keys_a = company_entity_dedupe_keys(a.name, a.website)
    keys_b = company_entity_dedupe_keys(b.name, b.website)
    assert keys_a.intersection(keys_b)


def test_choice_hotels_international_dedupes():
    rows = dedupe_lead_payloads_ordered(
        [
            {"id": 173, "company_name": "Choice Hotels", "website": "https://choice.com"},
            {
                "id": 112,
                "company_name": "Choice Hotels International",
                "website": "https://www.choicehotels.com",
            },
        ]
    )
    assert len(rows) == 1
