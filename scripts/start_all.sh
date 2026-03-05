#!/bin/bash
# Start all services: FastAPI app + Celery worker + Celery beat + Next.js SSR server

set -e  # Exit on error

# Start Celery beat in background
echo "Starting Celery beat scheduler..."
celery -A worker.celery_worker beat --loglevel=info &
BEAT_PID=$!
echo "Celery beat started with PID $BEAT_PID"

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A worker.celery_worker worker --loglevel=info --concurrency=2 &
WORKER_PID=$!
echo "Celery worker started with PID $WORKER_PID"

# Start Next.js server in background (for server-side rendering)
echo "Starting Next.js server on port 3000..."
cd /code/frontend && NODE_ENV=production npm start &
NEXTJS_PID=$!
echo "Next.js server started with PID $NEXTJS_PID"

# Give services a moment to start
sleep 3

# Start uvicorn in foreground (keeps container running)
echo "Starting FastAPI application on 0.0.0.0:8080..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
