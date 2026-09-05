"""Trade / news outlets must never be treated as buyer companies."""
import pytest

from app.services.news_publications import (
    is_known_publication_name,
    publication_matches_rss_source,
    strip_trailing_news_attribution,
)
from app.services.lead_filter import is_junk


@pytest.mark.parametrize(
    "name",
    [
        "Textile Today",
        "Supply Chain Dive",
        "World Economic Forum",
        "The World Economic Forum",
        "Charlotte Business Journal",
        "Huntsville Business Journal",
        "Retail Dive",
        "FreightWaves",
    ],
)
def test_publication_names_flagged(name):
    assert is_known_publication_name(name) is True
    assert is_junk(name)[0] is True


@pytest.mark.parametrize(
    "title,source,expected_core",
    [
        (
            "Acme Logistics opens Texas DC - Supply Chain Dive",
            "Supply Chain Dive",
            "Acme Logistics opens Texas DC",
        ),
        (
            "Robot pilot expands | Textile Today",
            "Textile Today",
            "Robot pilot expands",
        ),
    ],
)
def test_strip_trailing_attribution(title, source, expected_core):
    assert strip_trailing_news_attribution(title, source) == expected_core


def test_publication_matches_rss_source_compact():
    assert publication_matches_rss_source("Supply Chain Dive", "SupplyChainDive") is True


@pytest.mark.parametrize(
    "name",
    [
        "Acme Textiles Inc",
        "Target Corporation",
        "Blue Supply Chain Partners",
    ],
)
def test_operating_companies_not_publications(name):
    assert is_known_publication_name(name) is False
    assert is_junk(name)[0] is False
