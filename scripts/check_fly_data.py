#!/usr/bin/env python3
"""Check Supabase database via Fly.io deployment"""

import requests
import json

print("🔍 Checking Supabase database via Fly.io deployment...")
print("=" * 60)

try:
    response = requests.get("https://ready-2-robot.fly.dev/api/leads", timeout=10)
    leads = response.json()
    
    real_leads = [l for l in leads if not l.get('is_internal', False)]
    test_leads = [l for l in leads if l.get('is_internal', False)]
    
    print(f"\n📊 Total leads from API: {len(leads)}")
    print(f"✨ Real leads (is_internal=false): {len(real_leads)}")
    print(f"🧪 Test leads (is_internal=true): {len(test_leads)}")
    
    # Count signals
    total_signals = sum(len(l.get('signals', [])) for l in leads)
    print(f"⚡ Total signals: {total_signals}")
    
    if real_leads:
        print(f"\n🎯 Sample real leads from restored backup:")
        for lead in real_leads[:10]:
            company = lead.get('company_name', 'Unknown')
            industry = lead.get('industry', 'N/A')
            signals = len(lead.get('signals', []))
            print(f"   • {company} ({industry}) - {signals} signals")
        
        print(f"\n🎉 SUCCESS! Database restored with {len(real_leads)} real leads!")
    else:
        print("\n⚠️  No real leads found - backup may not have restored yet")
        print("    Check Supabase dashboard to verify restore completed")
    
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error: {e}")
