"""Helpers for scripts/reattribute_mismatched_signals.py"""

from scripts.reattribute_mismatched_signals import (
    extracted_name_is_trustworthy,
    mismatch_confidence,
    names_match,
    stored_name_is_credited_in_tail,
)

NIKE_TYSON = (
    "Nike Axes 775 Warehouse Jobs As Robots Replace Workers "
    "— Joining GM and Tyson in Automation Wave"
)


def test_names_match_variants():
    assert names_match("Marriott International", "Marriott")
    assert names_match("Tyson Foods", "Tyson Foods Inc.")
    assert not names_match("Tyson Foods", "Nike")


def test_nike_tyson_headline_is_high_confidence_mismatch():
    assert mismatch_confidence("Tyson Foods", "Nike", NIKE_TYSON) == "high"
    assert mismatch_confidence("Tyson", "Nike", NIKE_TYSON) == "high"


def test_matching_names_are_none_confidence():
    assert mismatch_confidence("Nike", "Nike", NIKE_TYSON) == "none"


def test_trustworthy_extracted_names():
    lookup = {"tyson foods": ("Tyson Foods", "Food")}
    assert extracted_name_is_trustworthy("Nike", lookup)
    assert not extracted_name_is_trustworthy("Modernization", lookup)
    assert not extracted_name_is_trustworthy("News Why", lookup)


def test_stored_name_in_tail_skips_mismatch():
    text = "Bowling Green, KY Bacon Facility - Tyson Foods"
    assert stored_name_is_credited_in_tail(text, "Tyson Foods")
    assert not stored_name_is_credited_in_tail(NIKE_TYSON, "Tyson Foods")
