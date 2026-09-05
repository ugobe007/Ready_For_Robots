#!/usr/bin/env python3
"""
Batch scraper runner for Supabase - ADDS leads (doesn't delete existing)
Run this once backups are restored to supplement with fresh scraped data
"""

import sys
import time
import subprocess
from datetime import datetime

# Scrapers to run (in order of priority)
SCRAPER_JOBS = [
    {
        "name": "Seed Leads v2 (Core Industries)",
        "script": "scripts/seed_leads_v2.py",
        "args": ["--commit"],
        "estimated_leads": 50,
        "priority": 1
    },
    {
        "name": "Seed Leads v3 (Extended)",
        "script": "scripts/seed_leads_v3.py", 
        "args": ["--commit"],
        "estimated_leads": 40,
        "priority": 2
    },
    {
        "name": "Job Board Scraper",
        "script": "app/scrapers/job_board_scraper.py",
        "args": [],
        "estimated_leads": 100,
        "priority": 3
    },
    {
        "name": "News Scraper",
        "script": "app/scrapers/news_scraper.py",
        "args": [],
        "estimated_leads": 80,
        "priority": 4
    },
    {
        "name": "Logistics Directory",
        "script": "app/scrapers/logistics_directory_scraper.py",
        "args": [],
        "estimated_leads": 60,
        "priority": 5
    },
    {
        "name": "Hotel Directory",
        "script": "app/scrapers/hotel_directory_scraper.py",
        "args": [],
        "estimated_leads": 50,
        "priority": 6
    }
]

def run_scraper(job):
    """Run a single scraper job"""
    print(f"\n{'='*70}")
    print(f"🚀 Starting: {job['name']}")
    print(f"   Script: {job['script']}")
    print(f"   Expected: ~{job['estimated_leads']} new leads")
    print(f"{'='*70}\n")
    
    start_time = time.time()
    
    try:
        cmd = ["/usr/bin/python3", job['script']] + job['args']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {job['name']} completed in {duration:.1f}s")
            print(result.stdout)
            return True
        else:
            print(f"❌ {job['name']} failed!")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️  {job['name']} timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"💥 {job['name']} crashed: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("🎯 SCRAPER BATCH RUNNER - Goal: 1,000 Leads")
    print("="*70)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 Jobs queued: {len(SCRAPER_JOBS)}")
    
    total_expected = sum(job['estimated_leads'] for job in SCRAPER_JOBS)
    print(f"🎲 Estimated new leads: ~{total_expected}")
    print("="*70)
    
    # Check if DATABASE_URL is set
    import os
    if not os.getenv('DATABASE_URL'):
        print("\n⚠️  WARNING: DATABASE_URL not set!")
        print("   Set it before running:")
        print('   export DATABASE_URL="postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres"')
        sys.exit(1)
    
    # Run jobs in priority order
    completed = 0
    failed = 0
    
    for i, job in enumerate(sorted(SCRAPER_JOBS, key=lambda x: x['priority']), 1):
        print(f"\n📊 Progress: {i}/{len(SCRAPER_JOBS)} jobs")
        
        if run_scraper(job):
            completed += 1
        else:
            failed += 1
            
        # Brief pause between jobs
        if i < len(SCRAPER_JOBS):
            print("\n⏸️  Cooling down for 5 seconds...")
            time.sleep(5)
    
    # Summary
    print("\n" + "="*70)
    print("🏁 BATCH RUN COMPLETE")
    print("="*70)
    print(f"✅ Completed: {completed}/{len(SCRAPER_JOBS)}")
    print(f"❌ Failed: {failed}/{len(SCRAPER_JOBS)}")
    print(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n💡 Run monitor_lead_count.sh to check total lead count")
    print("="*70)

if __name__ == "__main__":
    main()
