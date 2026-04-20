#!/bin/bash
# Start all services: FastAPI app + Celery worker + Celery beat
# DB is not touched at deploy; first connection happens when a request needs it (browser/API).

set -e

# Run migrations with a 60-second timeout so a slow/unavailable DB never blocks startup.
# If alembic fails or times out, uvicorn still starts — static pages and health checks work.
if [ -n "$DATABASE_URL" ]; then
  echo "Running database migrations (alembic upgrade head)..."
  if timeout 60 alembic upgrade head; then
    echo "Migrations completed."
  else
    echo "WARNING: alembic upgrade head failed or timed out — continuing startup."
    echo "         APIs that require schema changes may return 500 until next deploy."
  fi
fi

# Start Celery only if Redis is available (skip gracefully on Fly.io without Redis)
if [ -n "$REDIS_URL" ] || [ -n "$CELERY_BROKER_URL" ]; then
  echo "Starting Celery beat..."
  celery -A worker.celery_worker beat --loglevel=info &
  echo "Starting Celery worker..."
  celery -A worker.celery_worker worker --loglevel=info --concurrency=2 &
else
  echo "No Redis/Celery broker configured — skipping Celery (scrapers run on schedule inside FastAPI)."
fi

# Start uvicorn — always starts regardless of DB/Celery state
echo "Starting FastAPI on 0.0.0.0:8080..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
