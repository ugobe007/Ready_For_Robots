"""Craigslist scraper for robot sales listings."""

import logging
from typing import List
from urllib.parse import urljoin

from .base import BaseScraper, Listing

logger = logging.getLogger(__name__)

# Common Craigslist city base URLs to scrape
DEFAULT_CITIES = [
    "https://sfbay.craigslist.org",
    "https://newyork.craigslist.org",
    "https://losangeles.craigslist.org",
    "https://chicago.craigslist.org",
    "https://seattle.craigslist.org",
]

SEARCH_PATH = "/search/sss"  # "for sale" section


class CraigslistScraper(BaseScraper):
    """Scrapes Craigslist for robot sales listings."""

    name = "craigslist"

    def __init__(self, cities: List[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.cities = cities or DEFAULT_CITIES

    def search(self, keyword: str) -> List[Listing]:
        """Search Craigslist across configured cities for the given keyword."""
        listings: List[Listing] = []

        for city_url in self.cities:
            search_url = city_url.rstrip("/") + SEARCH_PATH
            params = {"query": keyword, "sort": "date"}
            try:
                response = self.get(search_url, params=params)
                city_listings = self._parse_results(response.text, city_url)
                listings.extend(city_listings)
                logger.info(
                    "[%s] Found %d listings in %s for '%s'",
                    self.name,
                    len(city_listings),
                    city_url,
                    keyword,
                )
            except Exception as exc:
                logger.warning("[%s] Skipping %s: %s", self.name, city_url, exc)

        return listings

    def _parse_results(self, html: str, city_url: str) -> List[Listing]:
        """Parse Craigslist search results HTML."""
        soup = self.parse(html)
        listings: List[Listing] = []

        for item in soup.select("li.cl-search-result"):
            title_tag = item.select_one("a.cl-app-anchor span.label")
            if title_tag is None:
                # Fallback for older Craigslist HTML
                title_tag = item.select_one("a.result-title")
            if title_tag is None:
                continue

            title = title_tag.get_text(strip=True)

            link_tag = item.select_one("a.cl-app-anchor") or item.select_one("a.result-title")
            href = link_tag["href"] if link_tag else ""
            url = href if href.startswith("http") else urljoin(city_url, href)

            price_tag = item.select_one("span.priceinfo") or item.select_one("span.result-price")
            price = price_tag.get_text(strip=True) if price_tag else None

            location_tag = (
                item.select_one("div.meta span.separator + span")
                or item.select_one("span.result-hood")
            )
            location = location_tag.get_text(strip=True).strip("() ") if location_tag else None

            image_tag = item.select_one("img")
            image_url = image_tag.get("src") if image_tag else None

            listings.append(
                Listing(
                    title=title,
                    price=price,
                    url=url,
                    source=self.name,
                    location=location,
                    image_url=image_url,
                )
            )

        return listings
