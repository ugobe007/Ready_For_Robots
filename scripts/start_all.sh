#!/bin/bash
# Start all services: FastAPI app + Celery worker + Celery beat
# DB is not touched at deploy; first connection happens when a request needs it (browser/API).

set -e

# Migrations on Fly.io run once per deploy via fly.toml [deploy].release_command (fast boot; no duplicate work).
# Outside Fly (local / docker-compose), run migrations here so the schema is ready before traffic.
if [ -n "$DATABASE_URL" ] && [ -z "${FLY_MACHINE_ID:-}" ]; then
  echo "Running database migrations (alembic upgrade head)..."
  if timeout 60 alembic upgrade head; then
    echo "Migrations completed."
  else
    echo "WARNING: alembic upgrade head failed or timed out — continuing startup."
    echo "         APIs that require schema changes may return 500 until next deploy."
  fi
elif [ -n "$FLY_MACHINE_ID" ]; then
  echo "Fly.io machine: migrations run at deploy (release_command); skipping boot migration."
fi

# Start Celery only if Redis is available AND web process is not API-only.
# On Fly.io the web machine should set SKIP_CELERY=1 — run workers on a separate machine.
if [ -z "${SKIP_CELERY:-}" ] && { [ -n "$REDIS_URL" ] || [ -n "$CELERY_BROKER_URL" ]; }; then
  echo "Starting Celery beat..."
  celery -A worker.celery_worker beat --loglevel=info &
  echo "Starting Celery worker..."
  # -Q scrapers,celery: must include 'scrapers' because celery_worker.py routes all
  # worker.tasks.* to the 'scrapers' queue via task_routes. Without -Q scrapers the
  # worker only consumes the default 'celery' queue and Beat tasks pile up unprocessed.
  celery -A worker.celery_worker worker --loglevel=info --concurrency=2 -Q scrapers,celery &
else
  echo "Celery skipped (SKIP_CELERY set or no Redis broker)."
fi

# Start uvicorn — always starts regardless of DB/Celery state
echo "Starting FastAPI on 0.0.0.0:8080..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
