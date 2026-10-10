"""Newsletter headline must not duplicate the company name (CLLIX: CLLIX — CLLIX...)."""
from app.services.newsletter_service import (
    _editorial_headline,
    _public_edition_headline,
    _strip_leading_company,
)


def test_strip_leading_company_collapses_repeats():
    n = "CLLIX Apartments & Hotels"
    assert _strip_leading_company(f"{n}: {n} — {n} expands", n) == "expands"
    assert _strip_leading_company(f"{n} — some signal", n) == "some signal"
    assert _strip_leading_company(f"{n}: vacancy rate up", n) == "vacancy rate up"
    # No leading company → unchanged
    assert _strip_leading_company("Robots deployed in Q3", n) == "Robots deployed in Q3"
    # Empty / missing safe
    assert _strip_leading_company("", n) == ""
    assert _strip_leading_company("x", "") == "x"


def test_editorial_headline_does_not_duplicate_company():
    n = "CLLIX Apartments & Hotels"
    # Signal text that itself starts with the company name (the real-world case).
    h = _editorial_headline(
        n, "expansion", f"{n} is expanding to 50 new properties across three regions", "Hospitality"
    )
    # Company should appear exactly once at the start.
    assert h.count(n) == 1, h
    assert h.startswith(n)


def test_public_edition_headline_is_one_sentence():
    raw = (
        "Medline — to pilot warehouse automation platform from Symbotic. "
        "Medline to pilot warehouse automation platform"
    )
    headline = _public_edition_headline("Medline", raw)
    assert headline == "Medline to pilot warehouse automation platform from Symbotic"
    assert "...." not in headline
    assert not headline.split(" ", 1)[1][:1].isupper()
