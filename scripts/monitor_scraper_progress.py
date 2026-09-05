#!/usr/bin/env python3
"""
Monitor scraper progress and show real-time updates
"""
import requests
import time
from datetime import datetime

API_URL = "https://ready-2-robot.fly.dev"

def get_lead_count():
    """Get current lead count"""
    try:
        response = requests.get(f"{API_URL}/api/leads/summary")
        data = response.json()
        return data.get('total', 0)
    except:
        return None

def main():
    print("\n" + "="*70)
    print("📊 SCRAPER PROGRESS MONITOR")
    print("="*70)
    print(f"Started monitoring at: {datetime.now().strftime('%I:%M:%S %p')}")
    print("="*70 + "\n")
    
    # Get initial count
    initial_count = get_lead_count()
    if initial_count is None:
        print("❌ Could not connect to API")
        return
    
    print(f"📈 Starting lead count: {initial_count}")
    print("\n⏳ Monitoring for new leads... (Press Ctrl+C to stop)\n")
    
    last_count = initial_count
    check_num = 0
    
    try:
        while True:
            time.sleep(30)  # Check every 30 seconds
            check_num += 1
            current_count = get_lead_count()
            
            if current_count is None:
                print(f"[{datetime.now().strftime('%I:%M:%S %p')}] ⚠️  Connection error")
                continue
            
            new_leads = current_count - last_count
            total_new = current_count - initial_count
            
            if new_leads > 0:
                print(f"[{datetime.now().strftime('%I:%M:%S %p')}] ✅ +{new_leads} new leads! (Total: {current_count}, +{total_new} since start)")
                last_count = current_count
            else:
                dots = "." * (check_num % 4)
                print(f"[{datetime.now().strftime('%I:%M:%S %p')}] ⏳ Checking{dots:<3} (Total: {current_count}, +{total_new} since start)")
    
    except KeyboardInterrupt:
        print(f"\n\n{'='*70}")
        print("📊 FINAL RESULTS")
        print("="*70)
        final_count = get_lead_count()
        if final_count:
            total_new = final_count - initial_count
            print(f"Starting leads: {initial_count}")
            print(f"Final leads:    {final_count}")
            print(f"New leads:      +{total_new}")
            if total_new > 0:
                print(f"\n🎉 Successfully scraped {total_new} new leads!")
        print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
