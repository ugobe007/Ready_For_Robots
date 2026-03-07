#!/usr/bin/env python3
"""
Analyze scraper performance and lead acquisition
"""
import requests
from datetime import datetime, timedelta
from collections import Counter

API_URL = "https://ready-2-robot.fly.dev"

def main():
    print("\n" + "="*70)
    print("📊 SCRAPER PERFORMANCE & LEAD ACQUISITION ANALYSIS")
    print("="*70)
    
    # Fetch leads
    print("\n⏳ Fetching leads...")
    response = requests.get(f"{API_URL}/api/leads?limit=500")
    leads = response.json()
    
    print(f"✅ Loaded {len(leads)} leads\n")
    
    # Overall stats
    print("📈 OVERALL DATABASE:")
    print("-" * 70)
    hot = sum(1 for l in leads if l.get('priority_tier') == 'HOT')
    warm = sum(1 for l in leads if l.get('priority_tier') == 'WARM')
    cold = sum(1 for l in leads if l.get('priority_tier') == 'COLD')
    
    print(f"  Total Leads:  {len(leads)}")
    print(f"  🔥 HOT:       {hot:>3} ({hot/len(leads)*100:>5.1f}%)")
    print(f"  🟡 WARM:      {warm:>3} ({warm/len(leads)*100:>5.1f}%)")
    print(f"  ❄️  COLD:      {cold:>3} ({cold/len(leads)*100:>5.1f}%)")
    
    # Time-based analysis
    today = datetime.now().date()
    last_7_days = today - timedelta(days=7)
    last_30_days = today - timedelta(days=30)
    
    new_today = []
    new_7d = []
    new_30d = []
    
    for lead in leads:
        created = lead.get('created_at', '')
        if created:
            try:
                created_date = datetime.fromisoformat(created.replace('Z', '+00:00')).date()
                if created_date == today:
                    new_today.append(lead)
                if created_date >= last_7_days:
                    new_7d.append(lead)
                if created_date >= last_30_days:
                    new_30d.append(lead)
            except:
                pass
    
    print(f"\n📅 NEW LEADS BY TIMEFRAME:")
    print("-" * 70)
    print(f"  Today:        {len(new_today):>3}")
    print(f"  Last 7 days:  {len(new_7d):>3}")
    print(f"  Last 30 days: {len(new_30d):>3}")
    
    if new_7d:
        # Industry breakdown
        print(f"\n🏭 LAST 7 DAYS - BY INDUSTRY:")
        print("-" * 70)
        industries = Counter([l.get('industry', 'Unknown') for l in new_7d])
        for ind, count in industries.most_common(15):
            pct = count / len(new_7d) * 100
            print(f"  {ind:<35} {count:>3} ({pct:>5.1f}%)")
        
        # Signal activity
        print(f"\n⚡ LAST 7 DAYS - SIGNAL ACTIVITY:")
        print("-" * 70)
        signal_count = sum([len(l.get('signals', [])) for l in new_7d])
        print(f"  Total Signals Detected: {signal_count}")
        
        all_signals = []
        for l in new_7d:
            for sig in l.get('signals', []):
                all_signals.append(sig.get('signal_type', 'unknown'))
        
        if all_signals:
            print(f"\n  Signal Types:")
            sig_types = Counter(all_signals)
            for sig, count in sig_types.most_common(15):
                pct = count / len(all_signals) * 100
                print(f"    {sig:<30} {count:>3} ({pct:>5.1f}%)")
        
        # Top HOT leads
        print(f"\n🔥 TOP 10 HOT LEADS (Last 7 Days):")
        print("-" * 70)
        hot_recent = [l for l in new_7d if l.get('priority_tier') == 'HOT']
        hot_recent.sort(key=lambda x: x.get('score', {}).get('overall_score', 0), reverse=True)
        
        for i, lead in enumerate(hot_recent[:10], 1):
            score = lead.get('score', {}).get('overall_score', 0)
            signals = len(lead.get('signals', []))
            company = lead.get('company_name', 'Unknown')[:40]
            industry = lead.get('industry', 'Unknown')[:25]
            print(f"  {i:>2}. {company:<40} | {industry:<25}")
            print(f"      Score: {int(score):>3} | Signals: {signals:>2}")
    
    # Industry distribution (all time)
    print(f"\n🌎 ALL-TIME INDUSTRY DISTRIBUTION:")
    print("-" * 70)
    all_industries = Counter([l.get('industry', 'Unknown') for l in leads])
    for ind, count in all_industries.most_common(15):
        pct = count / len(leads) * 100
        bar_length = int(pct / 2)
        bar = '█' * bar_length
        print(f"  {ind:<35} {count:>3} ({pct:>5.1f}%) {bar}")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
