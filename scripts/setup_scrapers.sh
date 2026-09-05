#!/bin/bash
# Setup scraper environment - fixes broken venv and installs dependencies

set -e

cd "$(dirname "$0")/.."

echo "================================================"
echo "🔧 SCRAPER ENVIRONMENT SETUP"
echo "================================================"

# Check if .venv exists and works (pip scripts may have wrong shebang if project was moved)
VENV_BROKEN=0
if [ -d .venv ]; then
    # pip is the canary - it has hardcoded path in shebang
    if ! .venv/bin/pip --version 2>/dev/null; then
        VENV_BROKEN=1
        echo "  Detected broken .venv (pip/interpreter path wrong - project may have been moved)"
    elif ! .venv/bin/python -c "import sqlalchemy" 2>/dev/null; then
        VENV_BROKEN=1
        echo "  Detected .venv missing dependencies"
    fi
fi

if [ $VENV_BROKEN -eq 1 ] || [ ! -d .venv ]; then
    echo ""
    echo "Creating fresh virtual environment..."
    
    if [ -d .venv ]; then
        echo "  Backing up broken .venv to .venv.broken"
        mv .venv .venv.broken
    fi
    
    python3 -m venv .venv
    echo "  ✓ venv created"
fi

echo ""
echo "Installing dependencies..."
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements.txt
echo "  ✓ Python packages installed"

# Playwright for job board scraper (optional - can skip if not using job boards)
if .venv/bin/python -m playwright install chromium 2>/dev/null; then
    echo "  ✓ Playwright Chromium installed"
else
    echo "  ⚠ Playwright install skipped (run: .venv/bin/python -m playwright install chromium)"
fi

echo ""
echo "Verifying..."
if .venv/bin/python -c "
import sqlalchemy
from app.database import SessionLocal
print('  ✓ SQLAlchemy OK')
print('  ✓ Database module OK')
"; then
    echo ""
    echo "================================================"
    echo "✅ SETUP COMPLETE"
    echo "================================================"
    echo ""
    echo "Run scrapers:"
    echo "  ./scripts/run_scrapers_supabase.sh"
    echo ""
    echo "Or test manually:"
    echo "  .venv/bin/python scripts/run_intelligence_scraper.py --limit 2"
    echo ""
else
    echo "  ✗ Verification failed - check errors above"
    exit 1
fi
