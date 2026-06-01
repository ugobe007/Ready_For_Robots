#!/usr/bin/env python3
"""Apply catalog product_url values to humanoid_benchmarks."""
from __future__ import annotations

from app.database import SessionLocal
from app.services.humanoid_vendor_catalog import sync_product_urls_from_catalog


def main() -> None:
    with SessionLocal() as db:
        stats = sync_product_urls_from_catalog(db)
    print(stats)


if __name__ == "__main__":
    main()
