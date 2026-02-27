"""
Robot Sales Opportunity Scraper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Discovers robot sales listings from eBay and Craigslist.

Usage:
    python main.py [options]

Options:
    --keywords  Comma-separated list of search keywords (default: "robot,robotic arm,industrial robot")
    --sources   Comma-separated list of sources to scrape: ebay, craigslist (default: all)
    --max       Maximum number of results per source (default: 50)
    --output    Output file path. Extension determines format: .json or .csv (default: print to stdout)
    --cities    Comma-separated Craigslist base URLs to search (overrides defaults)
"""

import argparse
import logging
import sys
from typing import List

from scraper.scrapers.base import Listing
from scraper.scrapers.craigslist import CraigslistScraper
from scraper.scrapers.ebay import EbayScraper
from scraper.utils import print_listings, save_csv, save_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scrape robot sales opportunities from eBay and Craigslist."
    )
    parser.add_argument(
        "--keywords",
        default="robot,robotic arm,industrial robot",
        help="Comma-separated search keywords (default: %(default)s)",
    )
    parser.add_argument(
        "--sources",
        default="ebay,craigslist",
        help="Comma-separated sources to scrape: ebay, craigslist (default: %(default)s)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=50,
        dest="max_results",
        help="Max results per source (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (.json or .csv). Omit to print to stdout.",
    )
    parser.add_argument(
        "--cities",
        default=None,
        help="Comma-separated Craigslist base URLs to search.",
    )
    return parser


def run_scrapers(
    keywords: List[str],
    sources: List[str],
    max_results: int,
    cities: List[str] = None,
) -> List[Listing]:
    all_listings: List[Listing] = []

    if "ebay" in sources:
        scraper = EbayScraper(keywords=keywords, max_results=max_results)
        all_listings.extend(scraper.run())

    if "craigslist" in sources:
        kwargs = {}
        if cities:
            kwargs["cities"] = cities
        scraper = CraigslistScraper(keywords=keywords, max_results=max_results, **kwargs)
        all_listings.extend(scraper.run())

    return all_listings


def main(argv: List[str] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
    cities = (
        [c.strip() for c in args.cities.split(",") if c.strip()] if args.cities else None
    )

    unknown_sources = set(sources) - {"ebay", "craigslist"}
    if unknown_sources:
        logger.error("Unknown sources: %s. Valid sources are: ebay, craigslist", unknown_sources)
        return 1

    logger.info(
        "Starting scrape — keywords: %s | sources: %s | max per source: %d",
        keywords,
        sources,
        args.max_results,
    )

    listings = run_scrapers(keywords, sources, args.max_results, cities)
    logger.info("Total listings found: %d", len(listings))

    if args.output:
        if args.output.endswith(".csv"):
            save_csv(listings, args.output)
        else:
            save_json(listings, args.output)
    else:
        print_listings(listings)

    return 0


if __name__ == "__main__":
    sys.exit(main())
