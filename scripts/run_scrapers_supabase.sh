#!/bin/bash
# Run all scrapers with Supabase connection
# This ensures all leads are saved to production database

set -e

cd "$(dirname "$0")/.."

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs) 2>/dev/null || true
fi
export PYTHONPATH="$(cd "$(dirname "$0")/.." && pwd)"

# Prefer .venv_new (documented in SCRAPER_FIX_GUIDE); fall back to .venv
if [ -x .venv_new/bin/python ]; then
    PYTHON=".venv_new/bin/python"
elif [ -x .venv/bin/python ]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python3"
    echo "⚠️  No project venv found. Using system python3."
    echo "   Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    echo ""
fi

echo "================================================"
echo "🚀 RUNNING SCRAPERS → SUPABASE"
echo "================================================"
echo "Python: $PYTHON"
echo "Database: ${DATABASE_URL:0:50}..."
echo ""

# Kill any existing scraper processes
echo "1️⃣  Stopping any existing scrapers..."
pkill -f "seed_leads" 2>/dev/null || true
pkill -f "intelligence_scraper" 2>/dev/null || true
sleep 2

# Create logs directory
mkdir -p logs

echo ""
echo "2️⃣  Running seed scripts to populate Supabase..."
echo ""

# Run seed_leads_v2
echo "   📥 Seed Leads v2 (Core Industries)..."
$PYTHON scripts/seed_leads_v2.py --commit 2>&1 | tee logs/seed_v2_$(date +%Y%m%d_%H%M%S).log
echo "   ✅ Complete"
echo ""

# Run seed_leads_v3  
echo "   📥 Seed Leads v3 (Extended)..."
$PYTHON scripts/seed_leads_v3.py --commit 2>&1 | tee logs/seed_v3_$(date +%Y%m%d_%H%M%S).log
echo "   ✅ Complete"
echo ""

echo "3️⃣  Starting continuous intelligence scraper..."
nohup $PYTHON scripts/run_intelligence_scraper.py > logs/intelligence_scraper.log 2>&1 &
SCRAPER_PID=$!
echo "   ✅ Intelligence scraper running (PID: $SCRAPER_PID)"
echo ""

echo "================================================"
echo "✅ SCRAPERS DEPLOYED TO SUPABASE"
echo "================================================"
echo ""
echo "Monitor logs:"
echo "  tail -f logs/intelligence_scraper.log"
echo ""
echo "Check lead count:"
echo "  curl https://ready-2-robot.fly.dev/api/leads | jq length"
echo ""
