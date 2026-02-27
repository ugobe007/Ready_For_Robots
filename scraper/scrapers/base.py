"""Base scraper class for robot sales opportunity scrapers."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class Listing:
    """Represents a robot sales listing."""

    title: str
    price: Optional[str]
    url: str
    source: str
    location: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "price": self.price,
            "url": self.url,
            "source": self.source,
            "location": self.location,
            "description": self.description,
            "image_url": self.image_url,
            **self.extra,
        }


class BaseScraper(ABC):
    """Abstract base class for all robot sales scrapers."""

    name: str = "base"
    base_url: str = ""

    def __init__(
        self,
        keywords: List[str] = None,
        max_results: int = 50,
        timeout: int = 10,
        headers: dict = None,
        session: requests.Session = None,
    ):
        self.keywords = keywords or ["robot", "industrial robot", "robotic arm"]
        self.max_results = max_results
        self.timeout = timeout
        self.headers = headers or DEFAULT_HEADERS
        self.session = session or requests.Session()
        self.session.headers.update(self.headers)

    def get(self, url: str, params: dict = None) -> requests.Response:
        """Perform a GET request with error handling."""
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            logger.warning("Request failed for %s: %s", url, exc)
            raise

    def parse(self, html: str) -> BeautifulSoup:
        """Parse HTML into a BeautifulSoup object."""
        return BeautifulSoup(html, "lxml")

    @abstractmethod
    def search(self, keyword: str) -> List[Listing]:
        """Search for listings matching the given keyword."""

    def run(self) -> List[Listing]:
        """Run the scraper for all configured keywords and return deduplicated results."""
        seen_urls: set = set()
        results: List[Listing] = []
        for keyword in self.keywords:
            logger.info("[%s] Searching for: %s", self.name, keyword)
            try:
                listings = self.search(keyword)
                for listing in listings:
                    if listing.url not in seen_urls:
                        seen_urls.add(listing.url)
                        results.append(listing)
                        if len(results) >= self.max_results:
                            return results
            except Exception as exc:
                logger.error("[%s] Error during search for '%s': %s", self.name, keyword, exc)
        return results
