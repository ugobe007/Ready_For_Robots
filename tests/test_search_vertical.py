"""Search API — vertical intent demotes incidental keyword matches on wrong industries."""
import pytest

from app.api.search import _detect_query_vertical, _vertical_alignment_bucket


@pytest.mark.parametrize(
    "q,keywords,expected",
    [
        ("hotel leads", [], "Hospitality"),
        ("HOTELS", [], "Hospitality"),
        ("find me hospitality buyers", [], "Hospitality"),
        ("hospital staffing", [], "Healthcare"),
        ("warehouse automation", [], "Logistics"),
        ("grocery automation buyers", [], "Retail"),
        ("meat processing plant labor", [], "Food Processing & Manufacturing"),
        ("fast food franchise", [], "Food Service"),
        ("surgical robot vendor", [], "Medical Technology"),
        ("random plumbus widget", [], None),
        (None, ["Series A", "hotel"], "Hospitality"),
    ],
)
def test_detect_query_vertical(q, keywords, expected):
    assert _detect_query_vertical(q, keywords) == expected


def test_alignment_hospitality_retail_is_demoted():
    assert _vertical_alignment_bucket("Retail", "Retail", "Hospitality") == -1


def test_alignment_hospitality_hotel_chain_boosted():
    assert _vertical_alignment_bucket("Hospitality", "Hospitality", "Hospitality") == 2


def test_alignment_no_intent_neutral():
    assert _vertical_alignment_bucket("Retail", "Retail", None) == 0


def test_alignment_media_demoted_for_vertical_intent():
    assert _vertical_alignment_bucket("Media & Publishing", "Media & Publishing", "Hospitality") == -1


def test_alignment_food_processing_strong():
    assert (
        _vertical_alignment_bucket("Food Processing & Manufacturing", "Food", "Food Processing & Manufacturing")
        == 2
    )
