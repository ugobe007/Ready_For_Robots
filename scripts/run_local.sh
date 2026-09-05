#!/bin/bash

set -e
cd "$(dirname "$0")/.."

if [ ! -f venv/bin/activate ]; then
  echo "No venv found. Create it from the repo root:"
  echo "  python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# Activate the virtual environment
source venv/bin/activate

# Run the FastAPI application (python -m works even if uvicorn is not on PATH)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload