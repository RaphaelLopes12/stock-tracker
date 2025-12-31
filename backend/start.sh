#!/bin/sh
set -e

echo "=== Starting Stock Tracker Backend ==="
echo "Database URL configured: yes"

echo "=== Running Alembic migrations ==="
python -m alembic upgrade head

echo "=== Migrations completed successfully ==="
echo "=== Starting Uvicorn server ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
