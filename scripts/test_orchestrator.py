#!/usr/bin/env python3
"""
Test the scraper orchestrator with playwright
"""
import os
import sys

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

from app.scrapers.orchestrator import ScraperOrchestrator
from app.database import SessionLocal

def test_orchestrator():
    print("🚀 Testing Scraper Orchestrator")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Check if scrapers are importable
        from app.scrapers.news_scraper import NewsScraper
        from app.scrapers.job_board_scraper import JobBoardScraper
        from app.scrapers.serp_scraper import SERPScraper
        print("✓ All scraper modules imported successfully\n")
        
        # Check scrape targets
        from app.scrapers.scrape_targets import get_urls, get_news_queries
        news_urls = get_urls('news')
        job_urls = get_urls('job_board')
        queries = get_news_queries()
        
        print(f"📊 Available Scraper Targets:")
        print(f"  • News RSS Feeds: {len(news_urls)} sources")
        print(f"  • Job Boards: {len(job_urls)} sources")
        print(f"  • News Queries: {len(queries)} search strings")
        print(f"  • TOTAL: {len(news_urls) + len(job_urls)} active scraping targets")
        
        print(f"\n🎯 Sample Targets:")
        if news_urls:
            print(f"  📰 News: {news_urls[0].label}")
        if job_urls:
            print(f"  📋 Job Board: {job_urls[0].label}")
        if queries:
            print(f"  🔍 Query: {queries[0]['query']}")
        
        # Now test a VERY small scrape (just 1-2 sources)
        print(f"\n🧪 Running Minimal Test Scrape...")
        print("=" * 60)
        
        orchestrator = ScraperOrchestrator(db=db)
        
        # Test news scraper with just 1 query
        print("\n→ Testing News Scraper (1 query)...")
        news_scraper = NewsScraper(db=db)
        test_queries = ["warehouse automation investment 2026"]
        
        try:
            results = news_scraper.run_intent_queries(queries=test_queries)
            print(f"  ✓ News scraper executed")
            print(f"  Found: {len(results) if results else 0} results")
        except Exception as e:
            print(f"  ✗ News scraper error: {e}")
        
        # Test job board scraper with 1 URL
        print("\n→ Testing Job Board Scraper (1 URL)...")
        job_scraper = JobBoardScraper(db=db)
        test_urls = job_urls[:1] if job_urls else []
        
        try:
            if test_urls:
                results = job_scraper.run(test_urls)
                print(f"  ✓ Job board scraper executed")
                print(f"  Found: {len(results) if results else 0} results")
            else:
                print(f"  ⚠ No job board URLs configured")
        except Exception as e:
            print(f"  ✗ Job board scraper error: {e}")
        
        print(f"\n" + "=" * 60)
        print("✅ Orchestrator test complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    success = test_orchestrator()
    sys.exit(0 if success else 1)
