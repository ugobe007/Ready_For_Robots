#!/bin/bash
# Start Celery worker + beat for automated scraper scheduling
# Requires: Redis running (brew install redis && brew services start redis)
#
# Usage:
#   ./scripts/start_scraper_scheduler.sh       # Normal start (persists schedule)
#   ./scripts/start_scraper_scheduler.sh --dev # Dev mode: reset schedule, fire overdue tasks now

set -e
cd "$(dirname "$0")/.."

# Load env
[ -f .env ] && export $(grep -v '^#' .env | xargs)

# --dev: reset beat schedule so overdue tasks fire immediately (no long "stuck" wait)
if [ "$1" = "--dev" ]; then
    rm -f celerybeat-schedule celerybeat-schedule.db 2>/dev/null || true
    echo "Dev mode: reset beat schedule (overdue tasks will run now)"
fi

# Use project Python
if [ -x .venv/bin/python ]; then
    PYTHON=".venv/bin/python"
elif [ -x .venv_new/bin/python ]; then
    PYTHON=".venv_new/bin/python"
else
    echo "⚠️  No project venv. Run: ./scripts/setup_scrapers.sh"
    PYTHON="python3"
fi

# Ensure Celery and scraper deps are installed
if ! $PYTHON -c "import celery" 2>/dev/null; then
    echo "Installing celery and redis..."
    $PYTHON -m pip install -q celery redis
fi
if ! $PYTHON -c "import bs4" 2>/dev/null; then
    echo "Installing beautifulsoup4..."
    $PYTHON -m pip install -q beautifulsoup4
fi
if ! $PYTHON -c "import playwright" 2>/dev/null; then
    echo "Installing playwright..."
    $PYTHON -m pip install -q playwright
    $PYTHON -m playwright install chromium
fi
if ! $PYTHON -c "import sqlalchemy" 2>/dev/null; then
    echo "Installing sqlalchemy..."
    $PYTHON -m pip install -q sqlalchemy psycopg2-binary
fi

# Check Redis (celery needs it as broker)
REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
if ! $PYTHON -c "
import socket
from urllib.parse import urlparse
u = urlparse('$REDIS_URL')
host = u.hostname or 'localhost'
port = u.port or 6379
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect((host, port))
    s.close()
except: raise SystemExit(1)
" 2>/dev/null; then
    echo "❌ Redis not reachable at $REDIS_URL"
    echo "   Install: brew install redis"
    echo "   Start:   brew services start redis"
    exit 1
fi
echo "✓ Redis OK"

# Run worker + beat in one process (shows tasks in same output, no background confusion)
# Use -c 3 to avoid SIGSEGV on macOS
echo "Starting Celery worker + beat (concurrency=3)..."
exec $PYTHON -m celery -A worker.celery_worker worker --loglevel=info -Q scrapers -c 3 --beat
