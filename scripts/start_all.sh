#!/bin/bash
# Start all services: FastAPI app + Celery worker + Celery beat
# DB is not touched at deploy; first connection happens when a request needs it (browser/API).

set -e

# Run migrations in background so app starts immediately. No blocking on DB at deploy.
if [ -n "$DATABASE_URL" ]; then
  echo "Running database migrations in background..."
  (timeout 120 alembic upgrade head 2>&1 && echo "Migrations completed.") || echo "Migrations failed or skipped; run 'alembic upgrade head' if needed." &
fi

# Start Celery (non-blocking)
echo "Starting Celery beat..."
celery -A worker.celery_worker beat --loglevel=info &
echo "Starting Celery worker..."
celery -A worker.celery_worker worker --loglevel=info --concurrency=2 &

# Start uvicorn immediately — health checks and static pages work without DB
echo "Starting FastAPI on 0.0.0.0:8080..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
