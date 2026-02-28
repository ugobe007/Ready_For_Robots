#!/bin/bash

# This script sets up the database schema and initial data for the Ready for Robots application.

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Run database migrations
alembic upgrade head

# Optionally, you can add commands to insert initial data here
# Example: python -m app.database seed_data.py

echo "Database setup complete."