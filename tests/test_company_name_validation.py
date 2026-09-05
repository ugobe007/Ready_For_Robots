"""End-of-pipeline company name heuristics (news, addresses, headline scrapes)."""
import pytest

from app.services.company_name_validation import reject_as_non_company_name
from app.services.lead_filter import is_junk


@pytest.mark.parametrize(
    "name,snippet",
    [
        ("CBS NEWS", "broadcast"),
        ("NBC News", "broadcast"),
        ("LUCAS SYSTEM FETCH", "SYSTEM FETCH"),
        ("HOTEL DRIVE", "address"),
        ("TWIN CITIES THAI RESTAURANT", "shout-case venue"),
        ("SOME HEADLINE REPORT", "wire tail"),
        ("Source: Reuters Staff", "attribution prefix"),
        ("press@newswire.example.com", "email pattern"),
        ("Nursing Homes", "facility sector stub"),
        ("Senior Living", "sector stub two-word"),
        ("Long-Term Care Facility", "facility sector stub hyphenated"),
    ],
)
def test_reject_examples(name, snippet):
    bad, reason = reject_as_non_company_name(name)
    assert bad is True, f"expected reject for {snippet}: {reason}"


@pytest.mark.parametrize(
    "name",
    [
        "Lucasfilm Ltd",
        "Acme Logistics LLC",
        "Marriott International",
        "Twin Cities Automation Inc",
        "Brookdale Senior Living",
        "Sunrise Senior Living",
        "Clayton Homes",
    ],
)
def test_allow_realistic_names(name):
    assert reject_as_non_company_name(name)[0] is False
    assert is_junk(name)[0] is False


def test_is_junk_includes_validation():
    assert is_junk("CBS NEWS")[0] is True
