"""company_name_presence — Wikidata gate helpers."""
import pytest

from app.services.company_name_presence import (
    infer_brand_domain_hosts,
    needs_wikidata_verification,
)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Boston Dynamics", False),
        ("Acme Very Long Synthetic Phrase About Robotics", True),
    ],
)
def test_needs_wikidata_verification(name, expected):
    assert needs_wikidata_verification(name) is expected


def test_infer_brand_domain_hosts_first_non_stop_word():
    assert infer_brand_domain_hosts("Acme Very Long Synthetic Phrase About Robotics") == [
        "acme.com",
        "www.acme.com",
    ]


def test_infer_brand_domain_hosts_skips_stop_words():
    assert infer_brand_domain_hosts("Future GlobalCo Robotics") == [
        "globalco.com",
        "www.globalco.com",
    ]
