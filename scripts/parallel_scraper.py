#!/usr/bin/env python3
"""
Run multiple scrapers in parallel to quickly populate Supabase
"""
import os
import sys
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# Set Supabase database
os.environ['DATABASE_URL'] = 'postgresql://postgres:J5GW9sTXA0CHU1Mq@db.lmoyydlhlgdyqbxkmkuz.supabase.co:5432/postgres'

def run_scraper(scraper_info):
    """Run a single scraper"""
    name, script = scraper_info
    print(f"\n🚀 Starting: {name}")
    try:
        result = subprocess.run(
            ['python3', script, '--commit'] if '--commit' in script else ['python3', script],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per scraper
        )
        if result.returncode == 0:
            print(f"✅ {name} completed")
            return (name, True, result.stdout)
        else:
            print(f"❌ {name} failed: {result.stderr[:200]}")
            return (name, False, result.stderr)
    except subprocess.TimeoutExpired:
        print(f"⏱️  {name} timed out")
        return (name, False, "Timeout")
    except Exception as e:
        print(f"❌ {name} error: {str(e)[:200]}")
        return (name, False, str(e))

# Scrapers to run
SCRAPERS = [
    ("Intelligence News", "scripts/run_intelligence_scraper.py"),
]

def main():
    print("=" * 60)
    print("🎯 PARALLEL SCRAPER RUNNER - SUPABASE")
    print("=" * 60)
    print(f"Database: {os.environ['DATABASE_URL'][:50]}...")
    print(f"Running {len(SCRAPERS)} scrapers in parallel\n")
    
    results = []
    
    # Run scrapers sequentially for now to avoid database conflicts
    for scraper_info in SCRAPERS:
        result = run_scraper(scraper_info)
        results.append(result)
        time.sleep(2)  # Small delay between scrapers
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SCRAPER SUMMARY")
    print("=" * 60)
    successful = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    for name, _, _ in successful:
        print(f"   - {name}")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}/{len(results)}")
        for name, _, error in failed:
            print(f"   - {name}: {error[:100]}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
