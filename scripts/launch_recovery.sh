#!/bin/bash
# Data Recovery & Scraper Launcher
# This script launches all scrapers via PM2 to rebuild the lead database

echo "================================================"
echo "🚀 LEAD RECOVERY - LAUNCHING SCRAPERS VIA PM2"
echo "================================================"

# Force local SQLite database
export DATABASE_URL="sqlite:///./ready_for_robots.db"

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "❌ PM2 not found. Installing PM2..."
    npm install -g pm2
fi

# Navigate to project root
cd "$(dirname "$0")/.." || exit

# Stop any existing PM2 processes
echo ""
echo "1️⃣  Stopping existing PM2 processes..."
pm2 delete all 2>/dev/null || echo "   No existing processes"

# Start seed scripts first (one-time recovery)
echo ""
echo "2️⃣  Running seed scripts for immediate recovery..."
echo "   🗄️  Database: LOCAL SQLite (ready_for_robots.db)"
echo ""
echo "   Starting seed_leads_v2..."
DATABASE_URL="sqlite:///./ready_for_robots.db" pm2 start python3 --name seed-leads-v2 --no-autorestart -- scripts/seed_leads_v2.py --commit

sleep 5

echo "   Starting seed_leads_v3..."
DATABASE_URL="sqlite:///./ready_for_robots.db" pm2 start python3 --name seed-leads-v3 --no-autorestart -- scripts/seed_leads_v3.py --commit

# Wait for seeds to complete
echo ""
echo "⏳ Waiting for seed scripts to complete (this may take 2-3 minutes)..."
sleep 180

# Start continuous scrapers
echo ""
echo "3️⃣  Starting continuous scrapers..."

# Check if scrapers exist before starting
if [ -f "app/scrapers/job_board_scraper.py" ]; then
    echo "   Starting job-board-scraper..."
    pm2 start python3 --name job-board-scraper -- app/scrapers/job_board_scraper.py
fi

if [ -f "app/scrapers/news_scraper.py" ]; then
    echo "   Starting news-scraper..."
    pm2 start python3 --name news-scraper -- app/scrapers/news_scraper.py
fi

if [ -f "app/scrapers/logistics_directory_scraper.py" ]; then
    echo "   Starting logistics-directory-scraper..."
    pm2 start python3 --name logistics-directory-scraper -- app/scrapers/logistics_directory_scraper.py
fi

if [ -f "app/scrapers/hotel_directory_scraper.py" ]; then
    echo "   Starting hotel-directory-scraper..."
    pm2 start python3 --name hotel-directory-scraper -- app/scrapers/hotel_directory_scraper.py
fi

# Show status
echo ""
echo "4️⃣  PM2 Process Status:"
pm2 list

# Save PM2 process list
pm2 save

# Setup PM2 startup script
echo ""
echo "5️⃣  Setting up PM2 to auto-start on reboot..."
pm2 startup

echo ""
echo "================================================"
echo "✅ RECOVERY LAUNCHED!"
echo "================================================"
echo ""
echo "📊 Monitor progress:"
echo "   pm2 list              - Show all processes"
echo "   pm2 logs              - View all logs"
echo "   pm2 logs seed-leads-v2 - View seed v2 logs"
echo "   pm2 monit             - Live monitoring dashboard"
echo ""
echo "🔍 Check database:"
echo "   sqlite3 ready_for_robots.db \"SELECT COUNT(*) FROM companies;\""
echo "   curl http://localhost:8000/api/leads | python3 -m json.tool | grep -c company_name"
echo ""
echo "⏱️  Estimated recovery time:"
echo "   - Seed scripts: 3-5 minutes (150+ leads)"
echo "   - Job board scraper: 30-60 minutes (50-100 leads)"
echo "   - News scraper: 20-40 minutes (20-50 leads)"
echo "   - Directory scrapers: 1-2 hours (50-100 leads)"
echo ""
echo "🎯 Expected total recovery: 270-400 leads within 2 hours"
echo ""
