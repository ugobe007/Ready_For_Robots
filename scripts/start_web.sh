#!/bin/bash
# Fly web process — HTTP API only. Background cache rebuilds run on the worker machine.
set -e

export RFR_PROCESS_ROLE=web
export SKIP_CELERY=1

if [ -n "$FLY_MACHINE_ID" ]; then
  echo "Fly web machine ${FLY_MACHINE_ID}: API-only (background jobs on worker process)."
fi

echo "Starting FastAPI on 0.0.0.0:8080..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
