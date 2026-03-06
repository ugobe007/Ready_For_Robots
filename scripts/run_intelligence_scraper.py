#!/usr/bin/env python3
"""
Run Intelligence News Scraper — FREE Lead Discovery
====================================================
Discovers new companies from news (no paid APIs needed).
Alternative to LinkedIn ($99/mo), Pitchbook ($20K/yr), CB Insights ($50K/yr).

Usage:
    python scripts/run_intelligence_scraper.py [--mode discover|enrich|both]
    
Options:
    --mode discover     Discover new companies from news (default)
    --mode enrich       Enrich existing companies with new signals
    --mode both         Run both discovery and enrichment
    --limit N           Max articles per query (default: 10)
"""
import sys
import os
import logging
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.scrapers.intelligence_news_scraper import IntelligenceNewsScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('intelligence_scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Run Intelligence News Scraper')
    parser.add_argument(
        '--mode',
        choices=['discover', 'enrich', 'both'],
        default='discover',
        help='Scraper mode (default: discover)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Max articles per query (default: 10)'
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("🎣 INTELLIGENCE NEWS SCRAPER")
    logger.info("="*60)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Articles per query: {args.limit}")
    logger.info("="*60)
    
    db = SessionLocal()
    scraper = IntelligenceNewsScraper(db=db)
    
    try:
        if args.mode in ['discover', 'both']:
            logger.info("\n🔍 Starting lead discovery...")
            stats = scraper.discover_leads(max_articles_per_query=args.limit)
            
            # Print summary
            print("\n" + "="*60)
            print("🎯 DISCOVERY RESULTS")
            print("="*60)
            print(f"  New Companies Found:    {stats['companies_discovered']}")
            print(f"  Companies Enriched:     {stats['companies_enriched']}")
            print(f"  Signals Created:        {stats['signals_created']}")
            print(f"  Articles Processed:     {stats['articles_processed']}")
            print("="*60)
            
            if stats['companies_discovered'] > 0:
                print(f"\n✨ SUCCESS! Found {stats['companies_discovered']} new leads")
                print(f"💰 Value: ${stats['companies_discovered'] * 100:,} saved")
                print("   (vs. LinkedIn Sales Navigator @ $99/mo per lead)")
        
        if args.mode in ['enrich', 'both']:
            logger.info("\n📈 Starting company enrichment...")
            stats = scraper.enrich_existing_companies(limit=50)
            
            print("\n" + "="*60)
            print("📈 ENRICHMENT RESULTS")
            print("="*60)
            print(f"  Companies Enriched:     {stats['companies_enriched']}")
            print(f"  Signals Created:        {stats['signals_created']}")
            print("="*60)
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  Scraper interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()
    
    logger.info("\n✅ Scraper completed successfully")


if __name__ == "__main__":
    main()
