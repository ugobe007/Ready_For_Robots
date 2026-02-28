#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Run the FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload