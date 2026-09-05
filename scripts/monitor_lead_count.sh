#!/bin/bash
# Monitor lead count progress toward 1,000 leads goal

echo "📊 LEAD COUNT MONITOR - Goal: 1,000 leads"
echo "=========================================="
echo ""

# Check Fly.io deployment (connected to Supabase)
echo "🔍 Checking Supabase via Fly.io API..."
RESULT=$(curl -s 'https://ready-2-robot.fly.dev/api/leads' | python3 -c '
import sys, json
try:
    leads = json.load(sys.stdin)
    real = [l for l in leads if not l.get("is_internal")]
    test = [l for l in leads if l.get("is_internal")]
    signals = sum(len(l.get("signals", [])) for l in leads)
    
    # Industry breakdown
    industries = {}
    for lead in real:
        ind = lead.get("industry", "Unknown")
        industries[ind] = industries.get(ind, 0) + 1
    
    print(f"TOTAL:{len(leads)}")
    print(f"REAL:{len(real)}")
    print(f"TEST:{len(test)}")
    print(f"SIGNALS:{signals}")
    print(f"PROGRESS:{len(real)/1000*100:.1f}")
    
    # Top 3 industries
    top_industries = sorted(industries.items(), key=lambda x: -x[1])[:3]
    for ind, count in top_industries:
        print(f"IND:{ind}:{count}")
        
except Exception as e:
    print(f"ERROR:{e}")
    sys.exit(1)
')

# Parse results
TOTAL=$(echo "$RESULT" | grep "^TOTAL:" | cut -d: -f2)
REAL=$(echo "$RESULT" | grep "^REAL:" | cut -d: -f2)
TEST=$(echo "$RESULT" | grep "^TEST:" | cut -d: -f2)
SIGNALS=$(echo "$RESULT" | grep "^SIGNALS:" | cut -d: -f2)
PROGRESS=$(echo "$RESULT" | grep "^PROGRESS:" | cut -d: -f2)

if [ -z "$TOTAL" ]; then
    echo "❌ Failed to retrieve lead count"
    exit 1
fi

echo "📈 Current Status:"
echo "  Total leads: $TOTAL"
echo "  ✨ Real leads: $REAL"
echo "  🧪 Test data: $TEST"
echo "  ⚡ Signals: $SIGNALS"
echo ""
echo "🎯 Progress to 1,000 leads:"
echo "  Current: $REAL / 1,000"
echo "  Progress: $PROGRESS%"
echo "  Remaining: $((1000 - REAL)) leads needed"
echo ""

# Show top industries
echo "🏭 Top Industries:"
echo "$RESULT" | grep "^IND:" | while IFS=: read -r _ industry count; do
    echo "  • $industry: $count leads"
done

echo ""
echo "=========================================="

# Progress bar
FILLED=$((REAL / 10))
EMPTY=$((100 - FILLED))
printf "["
printf "%${FILLED}s" | tr ' ' '█'
printf "%${EMPTY}s" | tr ' ' '░'
printf "] $PROGRESS%%\n"

if [ "$REAL" -ge 1000 ]; then
    echo ""
    echo "🎉 GOAL ACHIEVED! You have $REAL leads!"
else
    echo ""
    echo "💪 Keep restoring backups! $((1000 - REAL)) more to go!"
fi
