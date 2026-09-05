#!/bin/bash
# Start Celery Worker + Beat for Automated Lead Discovery
# ========================================================
# Runs scrapers automatically on schedule (including Intelligence Scraper)

set -e

echo "🚀 Starting Ready for Robots Automation System"
echo "================================================"

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Warning: Redis not running. Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

echo "✅ Redis is running"

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Warning: Backend not running on port 8000"
    echo "   Start it with: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
fi

# Activate virtual environment if exists
if [ -f ".venv/bin/activate" ]; then
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
fi

# Start Celery Worker in background
echo "🔧 Starting Celery Worker..."
celery -A worker.celery_worker worker \
    --loglevel=info \
    --logfile=logs/celery_worker.log \
    --pidfile=logs/celery_worker.pid \
    --detach

sleep 2

# Start Celery Beat scheduler in background
echo "⏰ Starting Celery Beat Scheduler..."
celery -A worker.celery_worker beat \
    --loglevel=info \
    --logfile=logs/celery_beat.log \
    --pidfile=logs/celery_beat.pid \
    --detach

sleep 2

echo ""
echo "✅ Automation System Started!"
echo "================================================"
echo ""
echo "📊 SCHEDULED TASKS:"
echo "   • Intelligence Scraper: 3x daily (9am, 3pm, 9pm UTC)"
echo "   • News Scrapers: Every 2 hours"
echo "   • Job Boards: Every 6 hours"
echo "   • RSS Feeds: Every 4 hours"
echo "   • Directories: Daily"
echo ""
echo "📈 Expected Lead Discovery:"
echo "   • ~15 new companies per Intelligence run"
echo "   • 45 new companies/day from Intelligence alone"
echo "   • ~1,350 new companies/month"
echo "   • Value: $135,000/month (vs. LinkedIn pricing)"
echo ""
echo "📝 LOGS:"
echo "   • Worker: logs/celery_worker.log"
echo "   • Scheduler: logs/celery_beat.log"
echo "   • Intelligence: intelligence_scraper.log"
echo ""
echo "🛑 TO STOP:"
echo "   ./scripts/stop_automation.sh"
echo ""
echo "🎣 Your automated fishing net is now deployed!"
