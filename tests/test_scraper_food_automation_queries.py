"""Restaurant scraper queries must target food automation, not store-opening expansion."""
from __future__ import annotations

import re

from app.scrapers import scrape_targets
from app.scrapers.serp_scraper import EXPANSION_QUERIES as SERP_QUERIES
from app.scrapers.serp_scraper_enhanced import EXPANSION_QUERIES as SERP_ENHANCED_QUERIES

_BAD_RESTAURANT = re.compile(
    r"(opens?\s+new\s+locations?|new\s+locations?\s+expansion|new\s+unit\s+growth|"
    r"expansion\s+opening\s+sites)",
    re.I,
)
_FOOD_QUERY = re.compile(
    r"(automation|robot|kitchen|labor|food\s+prep|delivery\s+robot|staffing)",
    re.I,
)


def _assert_food_automation_queries(queries: list[str], *, label: str) -> None:
    food = [q for q in queries if re.search(r"restaurant|qsr|fast\s+food", q, re.I)]
    assert food, f"{label}: expected at least one restaurant/QSR query"
    for q in food:
        assert not _BAD_RESTAURANT.search(q), f"{label} still has expansion junk: {q!r}"
        assert _FOOD_QUERY.search(q), f"{label} missing automation intent: {q!r}"


def test_serp_scraper_restaurant_queries_are_automation_focused():
    _assert_food_automation_queries(SERP_QUERIES, label="serp_scraper")


def test_serp_scraper_enhanced_restaurant_queries_are_automation_focused():
    _assert_food_automation_queries(SERP_ENHANCED_QUERIES, label="serp_scraper_enhanced")


def test_scrape_targets_restaurant_news_queries_are_automation_focused():
    food_rows = [
        row["query"]
        for row in scrape_targets.NEWS_QUERIES
        if "Food Service" in (row.get("industries") or [])
        and re.search(r"restaurant|qsr|mcdonald|chipotle|yum", row["query"], re.I)
    ]
    assert food_rows
    for q in food_rows:
        if _BAD_RESTAURANT.search(q):
            raise AssertionError(f"scrape_targets NEWS_QUERIES expansion junk: {q!r}")
    # Named-chain row must be automation, not unit expansion
    chain = [
        row
        for row in scrape_targets.NEWS_QUERIES
        if "McDonald" in row.get("query", "")
    ]
    assert chain and "automation" in chain[0]["query"].lower()
