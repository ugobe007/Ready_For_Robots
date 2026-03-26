#!/bin/bash
# Monitor intelligence scraper progress and lead count

echo "================================================"
echo "📊 SCRAPER MONITORING DASHBOARD"
echo "================================================"
echo ""

# Check if scraper is running
SCRAPER_PID=$(ps aux | grep "run_intelligence_scraper" | grep -v grep | awk '{print $2}' | head -1)

if [ -n "$SCRAPER_PID" ]; then
    echo "✅ Intelligence Scraper: RUNNING (PID: $SCRAPER_PID)"
else
    echo "❌ Intelligence Scraper: NOT RUNNING"
fi

echo ""
echo "📈 Latest Scraper Activity:"
echo "---"
tail -10 logs/intelligence_scraper_*.log 2>/dev/null | grep -E "Query|NEW LEAD|✨" | tail -5
echo ""

# Check lead count from API
echo "📊 Current Database Stats:"
python3 -c "
import requests
try:
    r = requests.get('https://ready-2-robot.fly.dev/api/leads', timeout=10)
    data = r.json()
    print(f'  Total Leads: {len(data)}')
    hot = sum(1 for l in data if l.get('priority_tier') == 'HOT')
    warm = sum(1 for l in data if l.get('priority_tier') == 'WARM')
    signals = sum(l.get('signal_count', 0) for l in data)
    print(f'  🔥 HOT: {hot}')
    print(f'  ⚡ WARM: {warm}')
    print(f'  📡 Total Signals: {signals}')
except Exception as e:
    print(f'  Error: {e}')
" 2>/dev/null

echo ""
echo "================================================"
echo "To watch live scraping:"
echo "  tail -f logs/intelligence_scraper_*.log"
echo ""
echo "To stop scraper:"
echo "  kill $SCRAPER_PID"
echo "================================================"
