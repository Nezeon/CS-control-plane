#!/bin/bash
echo "=== CS Control Plane Starting ==="
echo "PORT=$PORT"
echo "DATABASE_URL is set: $([ -n "$DATABASE_URL" ] && echo YES || echo NO)"
echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --timeout-keep-alive 30 --log-level info
