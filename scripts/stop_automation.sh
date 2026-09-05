#!/bin/bash
# Stop Celery Worker + Beat
# ==========================

set -e

echo "🛑 Stopping Automation System..."

# Stop Celery Beat
if [ -f "logs/celery_beat.pid" ]; then
    echo "⏰ Stopping Celery Beat..."
    kill $(cat logs/celery_beat.pid) 2>/dev/null || echo "   Already stopped"
    rm -f logs/celery_beat.pid
fi

# Stop Celery Worker
if [ -f "logs/celery_worker.pid" ]; then
    echo "🔧 Stopping Celery Worker..."
    kill $(cat logs/celery_worker.pid) 2>/dev/null || echo "   Already stopped"
    rm -f logs/celery_worker.pid
fi

# Alternative: Kill by process name (fallback)
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true

echo ""
echo "✅ Automation System Stopped"
echo ""
echo "To restart: ./scripts/start_automation.sh"
