"""Tests for the robot sales opportunity scraper."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import responses as responses_lib

from scraper.scrapers.base import BaseScraper, Listing
from scraper.scrapers.craigslist import CraigslistScraper
from scraper.scrapers.ebay import EbayScraper
from scraper.utils import print_listings, save_csv, save_json


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

EBAY_HTML = """
<html><body>
<ul>
  <li class="s-item">
    <div class="s-item__title"><span role="heading">KUKA Industrial Robotic Arm KR 6</span></div>
    <a class="s-item__link" href="https://www.ebay.com/itm/123456789?some=param"></a>
    <span class="s-item__price">$4,500.00</span>
    <span class="s-item__location">Located in: Detroit, MI</span>
    <img class="s-item__image-img" src="https://i.ebayimg.com/img1.jpg" />
    <span class="SECONDARY_INFO">Used</span>
  </li>
  <li class="s-item">
    <div class="s-item__title"><span role="heading">Shop on eBay</span></div>
    <a class="s-item__link" href="https://www.ebay.com/itm/ghost"></a>
    <span class="s-item__price">$0.00</span>
  </li>
  <li class="s-item">
    <div class="s-item__title"><span role="heading">Fanuc Robot M-710iC/50</span></div>
    <a class="s-item__link" href="https://www.ebay.com/itm/987654321"></a>
    <span class="s-item__price">$12,000.00</span>
  </li>
</ul>
</body></html>
"""

CRAIGSLIST_HTML = """
<html><body>
<ul>
  <li class="cl-search-result">
    <a class="cl-app-anchor" href="https://sfbay.craigslist.org/sss/d/robot/1234.html">
      <span class="label">ABB IRB 2400 Industrial Robot</span>
    </a>
    <span class="priceinfo">$8,500</span>
    <div class="meta"><span>2 hours ago</span><span class="separator"> </span><span>(San Jose)</span></div>
    <img src="https://images.craigslist.org/img1.jpg" />
  </li>
  <li class="cl-search-result">
    <a class="cl-app-anchor" href="/sss/d/robot-arm/5678.html">
      <span class="label">Motoman Robot Arm UP6</span>
    </a>
    <span class="priceinfo">$3,200</span>
  </li>
</ul>
</body></html>
"""


# ---------------------------------------------------------------------------
# Listing tests
# ---------------------------------------------------------------------------

class TestListing:
    def test_to_dict_basic(self):
        listing = Listing(title="Test Robot", price="$100", url="http://example.com", source="test")
        d = listing.to_dict()
        assert d["title"] == "Test Robot"
        assert d["price"] == "$100"
        assert d["url"] == "http://example.com"
        assert d["source"] == "test"

    def test_to_dict_with_extra(self):
        listing = Listing(
            title="Robot", price="$50", url="http://x.com", source="ebay",
            extra={"condition": "Used"},
        )
        d = listing.to_dict()
        assert d["condition"] == "Used"

    def test_optional_fields_default_none(self):
        listing = Listing(title="R", price=None, url="u", source="s")
        assert listing.location is None
        assert listing.description is None
        assert listing.image_url is None


# ---------------------------------------------------------------------------
# BaseScraper tests
# ---------------------------------------------------------------------------

class ConcreteScraper(BaseScraper):
    """Concrete subclass for testing the abstract base."""
    name = "test"

    def search(self, keyword: str):
        return [
            Listing(title=f"{keyword} robot", price="$1", url=f"http://example.com/{keyword}", source=self.name)
        ]


class TestBaseScraper:
    def test_run_deduplicates(self):
        scraper = ConcreteScraper(keywords=["robot", "robot"])
        results = scraper.run()
        urls = [r.url for r in results]
        assert len(urls) == len(set(urls))

    def test_run_respects_max_results(self):
        scraper = ConcreteScraper(keywords=["a", "b", "c", "d", "e"], max_results=3)
        results = scraper.run()
        assert len(results) <= 3

    def test_run_handles_search_exception(self):
        scraper = ConcreteScraper(keywords=["bad"])
        scraper.search = MagicMock(side_effect=RuntimeError("network error"))
        results = scraper.run()
        assert results == []


# ---------------------------------------------------------------------------
# EbayScraper tests
# ---------------------------------------------------------------------------

class TestEbayScraper:
    @responses_lib.activate
    def test_search_returns_listings(self):
        responses_lib.add(
            responses_lib.GET,
            "https://www.ebay.com/sch/i.html",
            body=EBAY_HTML,
            status=200,
        )
        scraper = EbayScraper(keywords=["robot"])
        listings = scraper.search("robot")
        assert len(listings) == 2
        assert listings[0].title == "KUKA Industrial Robotic Arm KR 6"
        assert listings[0].price == "$4,500.00"
        assert listings[0].url == "https://www.ebay.com/itm/123456789"
        assert listings[0].source == "ebay"
        assert listings[0].location == "Located in: Detroit, MI"
        assert listings[0].extra.get("condition") == "Used"

    @responses_lib.activate
    def test_search_filters_ghost_items(self):
        responses_lib.add(
            responses_lib.GET,
            "https://www.ebay.com/sch/i.html",
            body=EBAY_HTML,
            status=200,
        )
        scraper = EbayScraper(keywords=["robot"])
        listings = scraper.search("robot")
        titles = [l.title for l in listings]
        assert all("shop on ebay" not in t.lower() for t in titles)

    @responses_lib.activate
    def test_search_http_error_raises(self):
        responses_lib.add(
            responses_lib.GET,
            "https://www.ebay.com/sch/i.html",
            status=503,
        )
        scraper = EbayScraper(keywords=["robot"])
        with pytest.raises(Exception):
            scraper.search("robot")


# ---------------------------------------------------------------------------
# CraigslistScraper tests
# ---------------------------------------------------------------------------

class TestCraigslistScraper:
    @responses_lib.activate
    def test_search_returns_listings(self):
        responses_lib.add(
            responses_lib.GET,
            "https://sfbay.craigslist.org/search/sss",
            body=CRAIGSLIST_HTML,
            status=200,
        )
        scraper = CraigslistScraper(
            keywords=["robot"],
            cities=["https://sfbay.craigslist.org"],
        )
        listings = scraper.search("robot")
        assert len(listings) == 2
        assert listings[0].title == "ABB IRB 2400 Industrial Robot"
        assert listings[0].price == "$8,500"
        assert listings[0].source == "craigslist"

    @responses_lib.activate
    def test_search_relative_url_resolved(self):
        responses_lib.add(
            responses_lib.GET,
            "https://sfbay.craigslist.org/search/sss",
            body=CRAIGSLIST_HTML,
            status=200,
        )
        scraper = CraigslistScraper(
            keywords=["robot"],
            cities=["https://sfbay.craigslist.org"],
        )
        listings = scraper.search("robot")
        for listing in listings:
            assert listing.url.startswith("http")

    @responses_lib.activate
    def test_search_skips_failed_city(self):
        responses_lib.add(
            responses_lib.GET,
            "https://sfbay.craigslist.org/search/sss",
            status=200,
            body=CRAIGSLIST_HTML,
        )
        responses_lib.add(
            responses_lib.GET,
            "https://chicago.craigslist.org/search/sss",
            status=500,
        )
        scraper = CraigslistScraper(
            keywords=["robot"],
            cities=["https://sfbay.craigslist.org", "https://chicago.craigslist.org"],
        )
        listings = scraper.search("robot")
        # Should still return results from sfbay despite Chicago failing
        assert len(listings) > 0


# ---------------------------------------------------------------------------
# Utility tests
# ---------------------------------------------------------------------------

SAMPLE_LISTINGS = [
    Listing(title="Robot A", price="$100", url="http://a.com", source="ebay", location="NY"),
    Listing(title="Robot B", price="$200", url="http://b.com", source="craigslist"),
]


class TestUtils:
    def test_save_json(self, tmp_path):
        filepath = str(tmp_path / "results.json")
        save_json(SAMPLE_LISTINGS, filepath)
        assert os.path.exists(filepath)
        with open(filepath) as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["title"] == "Robot A"

    def test_save_csv(self, tmp_path):
        filepath = str(tmp_path / "results.csv")
        save_csv(SAMPLE_LISTINGS, filepath)
        assert os.path.exists(filepath)
        with open(filepath) as f:
            content = f.read()
        assert "Robot A" in content
        assert "Robot B" in content

    def test_save_csv_empty(self, tmp_path, caplog):
        filepath = str(tmp_path / "empty.csv")
        save_csv([], filepath)
        assert not os.path.exists(filepath)

    def test_print_listings(self, capsys):
        print_listings(SAMPLE_LISTINGS)
        captured = capsys.readouterr()
        assert "Robot A" in captured.out
        assert "Robot B" in captured.out

    def test_print_listings_empty(self, capsys):
        print_listings([])
        captured = capsys.readouterr()
        assert "No listings found." in captured.out


# ---------------------------------------------------------------------------
# main() integration tests
# ---------------------------------------------------------------------------

class TestMain:
    def test_unknown_source_returns_1(self):
        from main import main
        result = main(["--sources", "unknown_source"])
        assert result == 1

    def test_main_returns_0_with_mocked_scrapers(self):
        from main import main
        with patch("main.run_scrapers", return_value=SAMPLE_LISTINGS):
            result = main(["--sources", "ebay", "--keywords", "robot"])
        assert result == 0

    def test_main_saves_json(self, tmp_path):
        from main import main
        output = str(tmp_path / "out.json")
        with patch("main.run_scrapers", return_value=SAMPLE_LISTINGS):
            result = main(["--output", output, "--sources", "ebay"])
        assert result == 0
        assert os.path.exists(output)

    def test_main_saves_csv(self, tmp_path):
        from main import main
        output = str(tmp_path / "out.csv")
        with patch("main.run_scrapers", return_value=SAMPLE_LISTINGS):
            result = main(["--output", output, "--sources", "ebay"])
        assert result == 0
        assert os.path.exists(output)
