"""Utility helpers for the robot sales scraper."""

import csv
import json
import logging
import os
from typing import List

from .scrapers.base import Listing

logger = logging.getLogger(__name__)


def save_json(listings: List[Listing], filepath: str) -> None:
    """Save listings to a JSON file."""
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump([l.to_dict() for l in listings], fh, indent=2, ensure_ascii=False)
    logger.info("Saved %d listings to %s", len(listings), filepath)


def save_csv(listings: List[Listing], filepath: str) -> None:
    """Save listings to a CSV file."""
    if not listings:
        logger.warning("No listings to save.")
        return
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    fieldnames = list(listings[0].to_dict().keys())
    with open(filepath, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(l.to_dict() for l in listings)
    logger.info("Saved %d listings to %s", len(listings), filepath)


def print_listings(listings: List[Listing]) -> None:
    """Print listings to stdout in a human-readable format."""
    if not listings:
        print("No listings found.")
        return
    print(f"\n{'='*60}")
    print(f"  Found {len(listings)} robot sales opportunit{'y' if len(listings) == 1 else 'ies'}")
    print(f"{'='*60}\n")
    for i, listing in enumerate(listings, start=1):
        print(f"[{i}] {listing.title}")
        print(f"     Price   : {listing.price or 'N/A'}")
        print(f"     Source  : {listing.source}")
        print(f"     Location: {listing.location or 'N/A'}")
        print(f"     URL     : {listing.url}")
        print()
