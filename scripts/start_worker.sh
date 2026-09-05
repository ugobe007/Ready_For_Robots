#!/bin/bash
# Fly worker process — cache rebuilds, social posts, scrapers (no HTTP).
set -e

export RFR_PROCESS_ROLE=worker
export SKIP_CELERY=1
export SKIP_SOCIAL_INTERVAL_REFRESH=0

if [ -n "$FLY_MACHINE_ID" ]; then
  echo "Fly worker machine ${FLY_MACHINE_ID}: background jobs only."
fi

exec python -m worker.background_worker
