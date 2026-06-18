#!/usr/bin/env python3
"""
Reclassify companies with industry Unknown using signal text + company name.
Run after a big scrape to reduce Unknown count in leads-by-industry.

Usage:
  python scripts/reclassify_unknown_industries.py

Uses DATABASE_URL from .env (same as run_intelligence_scraper.py).
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.company import Company
from app.services.industry_inference import effective_industry_for_lead


def main():
    db = SessionLocal()
    try:
        companies = (
            db.query(Company)
            .options(joinedload(Company.signals))
            .filter(
                (Company.industry == None)
                | (Company.industry == "")
                | (func.lower(Company.industry) == "unknown")
            )
            .all()
        )
        updated = 0
        by_industry = {}
        for c in companies:
            inferred = effective_industry_for_lead(
                c.name,
                c.industry,
                c.signals or [],
            )
            if inferred not in ("Unknown", "New", "Other") and inferred != (c.industry or "").strip():
                c.industry = inferred
                updated += 1
                by_industry[inferred] = by_industry.get(inferred, 0) + 1
        if updated:
            db.commit()
        unchanged = len(companies) - updated
        print("Reclassify Unknown industries")
        print(f"  Unknown leads considered: {len(companies)}")
        print(f"  Reclassified:            {updated}")
        print(f"  Still unknown:           {unchanged}")
        if by_industry:
            print("  New assignments:")
            for ind, count in sorted(by_industry.items(), key=lambda x: -x[1]):
                print(f"    {ind}: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
