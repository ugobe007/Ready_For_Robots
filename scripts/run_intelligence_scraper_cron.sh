#!/bin/bash
# Cron wrapper for intelligence scraper - uses project venv
# Add to crontab for automated runs, e.g.:
#   0 9,15,21 * * * /path/to/Ready_For_Robots/scripts/run_intelligence_scraper_cron.sh

cd "$(dirname "$0")/.."

# Load env
[ -f .env ] && export $(grep -v '^#' .env | xargs)

# Use project Python
if [ -x .venv/bin/python ]; then
    PYTHON=".venv/bin/python"
elif [ -x .venv_new/bin/python ]; then
    PYTHON=".venv_new/bin/python"
else
    PYTHON="python3"
fi

mkdir -p logs
LOG="logs/intelligence_scraper_$(date +%Y%m%d).log"

# Target 30-50 new leads per run: more articles/query + both discover+enrich
$PYTHON scripts/run_intelligence_scraper.py --mode both --limit 35 >> "$LOG" 2>&1
