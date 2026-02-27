"""eBay scraper for robot sales listings."""

import logging
from typing import List
from urllib.parse import urlencode

from .base import BaseScraper, Listing

logger = logging.getLogger(__name__)

EBAY_SEARCH_URL = "https://www.ebay.com/sch/i.html"


class EbayScraper(BaseScraper):
    """Scrapes eBay for robot sales listings."""

    name = "ebay"
    base_url = EBAY_SEARCH_URL

    def search(self, keyword: str) -> List[Listing]:
        """Search eBay for listings matching the given keyword."""
        params = {
            "_nkw": keyword,
            "_sacat": 0,
            "LH_BIN": 1,       # Buy It Now only
            "_sop": 12,        # Sort by newest first
        }
        listings: List[Listing] = []

        response = self.get(EBAY_SEARCH_URL, params=params)
        soup = self.parse(response.text)

        items = soup.select("li.s-item")
        for item in items:
            title_tag = item.select_one("div.s-item__title span[role='heading']")
            if title_tag is None:
                title_tag = item.select_one("div.s-item__title")
            if title_tag is None:
                continue

            title = title_tag.get_text(strip=True)
            # eBay injects a "Shop on eBay" ghost item at the top
            if "shop on ebay" in title.lower():
                continue

            link_tag = item.select_one("a.s-item__link")
            url = link_tag["href"].split("?")[0] if link_tag else ""

            price_tag = item.select_one("span.s-item__price")
            price = price_tag.get_text(strip=True) if price_tag else None

            location_tag = item.select_one("span.s-item__location")
            location = location_tag.get_text(strip=True) if location_tag else None

            image_tag = item.select_one("img.s-item__image-img")
            image_url = image_tag.get("src") if image_tag else None

            condition_tag = item.select_one("span.SECONDARY_INFO")
            condition = condition_tag.get_text(strip=True) if condition_tag else None

            listings.append(
                Listing(
                    title=title,
                    price=price,
                    url=url,
                    source=self.name,
                    location=location,
                    image_url=image_url,
                    extra={"condition": condition} if condition else {},
                )
            )

        logger.info("[%s] Found %d listings for '%s'", self.name, len(listings), keyword)
        return listings
