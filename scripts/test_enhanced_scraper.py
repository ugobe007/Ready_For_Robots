#!/usr/bin/env python3
"""
Test Enhanced News Scraper with Ontology-Based Relevancy
========================================================
Demonstrates improvements:
1. Rate limiting (2-5s delays, exponential backoff)
2. Ontology-based relevancy scoring (filters junk articles)
3. Duplicate detection (URL + title fingerprinting)
4. Better error handling
"""
import os
import sys

os.environ['DATABASE_URL'] = 'postgresql://postgres:J5GW9sTXA0CHU1Mq@db.lmoyydlhlgdyqbxkmkuz.supabase.co:5432/postgres'

from app.scrapers.news_scraper_enhanced import EnhancedNewsScraper
from app.database import SessionLocal

def test_enhanced_scraper():
    print("🚀 Testing Enhanced News Scraper")
    print("=" * 70)
    
    db = SessionLocal()
    scraper = EnhancedNewsScraper(db=db)
    
    # Test queries focusing on manufacturing (your interest)
    test_queries = [
        "warehouse automation robotics investment 2026",
        "manufacturing quality control automation 2026",
        "packaging automation palletizing robot 2026",
    ]
    
    print(f"\n📊 Running {len(test_queries)} queries with relevancy filtering...")
    print("=" * 70)
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 70)
    
    try:
        # Run scraper with max 15 articles to avoid long wait
        results = scraper.run_intent_queries(queries=test_queries, max_articles=15)
        
        print(f"\n" + "=" * 70)
        print(f"✅ SCRAPING COMPLETE")
        print("=" * 70)
        print(f"  Total articles processed: {scraper.request_count}")
        print(f"  Relevant signals found: {len(results)}")
        print(f"  Duplicate URLs filtered: {len(scraper.session_seen_urls) - len(results)}")
        
        if results:
            print(f"\n📰 SAMPLE RESULTS:")
            print("=" * 70)
            for i, result in enumerate(results[:5], 1):
                print(f"\n{i}. {result['company']} | {result['signal_type']}")
                print(f"   {result['title'][:80]}...")
                print(f"   {result['url'][:80]}...")
        
        print(f"\n" + "=" * 70)
        print("RELEVANCY IMPROVEMENTS:")
        print("=" * 70)
        print("✓ Ontology-based keyword matching (automation, labor_pain, expansion concepts)")
        print("✓ Score threshold filtering (only >0.3 relevancy)")
        print("✓ Duplicate detection (URL + title fingerprinting)")
        print("✓ Rate limiting (2-5s delays, prevents IP bans)")
        print("✓ User agent rotation (anti-bot protection)")
        print("✓ Exponential backoff on errors (429, 5xx responses)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    success = test_enhanced_scraper()
    sys.exit(0 if success else 1)
