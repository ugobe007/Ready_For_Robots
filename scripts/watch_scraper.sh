#!/bin/bash
# Automated lead monitoring - runs every 5 minutes
# Usage: Run this in background to track progress

echo "🔄 Starting automated monitoring (updates every 5 minutes)..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "================================================"
    echo "📊 LIVE SCRAPER DASHBOARD - $(date '+%H:%M:%S')"
    echo "================================================"
    echo ""
    
    # Check scraper status
    SCRAPER_PID=$(ps aux | grep "run_intelligence_scraper" | grep -v grep | awk '{print $2}' | head -1)
    
    if [ -n "$SCRAPER_PID" ]; then
        echo "✅ Scraper Status: RUNNING (PID: $SCRAPER_PID)"
        
        # Show latest activity
        echo ""
        echo "🔍 Recent Activity:"
        tail -30 logs/intelligence_scraper_*.log 2>/dev/null | grep -E "Query|NEW LEAD|✨" | tail -8
    else
        echo "❌ Scraper Status: STOPPED"
    fi
    
    echo ""
    echo "📊 Database Stats:"
    python3 -c "
import requests
try:
    r = requests.get('https://ready-2-robot.fly.dev/api/leads', timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f'  Total Leads: {len(data)}')
        hot = sum(1 for l in data if l.get('priority_tier') == 'HOT')
        print(f'  🔥 HOT Deals: {hot}')
        signals = sum(l.get('signal_count', 0) for l in data)
        print(f'  📡 Signals: {signals}')
    else:
        print(f'  API returned status: {r.status_code}')
except Exception as e:
    print(f'  Could not fetch data')
" 2>/dev/null
    
    echo ""
    echo "Next update in 5 minutes..."
    echo "================================================"
    
    sleep 300  # 5 minutes
done
