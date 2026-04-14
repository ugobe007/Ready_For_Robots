#!/bin/bash
# Start all services: FastAPI app + Celery worker + Celery beat
# DB is not touched at deploy; first connection happens when a request needs it (browser/API).

set -e

# Schema must match ORM before serving API (Company loads include all columns).
# Background migrations caused race: /api/leads and /homepage 500 until column exists.
if [ -n "$DATABASE_URL" ]; then
  echo "Running database migrations (alembic upgrade head)..."
  if alembic upgrade head; then
    echo "Migrations completed."
  else
    echo "ERROR: alembic upgrade head failed — API may return 500 until fixed."
    exit 1
  fi
fi

# Start Celery (non-blocking)
echo "Starting Celery beat..."
celery -A worker.celery_worker beat --loglevel=info &
echo "Starting Celery worker..."
celery -A worker.celery_worker worker --loglevel=info --concurrency=2 &

# Start uvicorn immediately — health checks and static pages work without DB
echo "Starting FastAPI on 0.0.0.0:8080..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
