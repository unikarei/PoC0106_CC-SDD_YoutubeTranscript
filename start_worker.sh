#!/bin/bash
# Worker startup script for local development

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start Celery worker
celery -A backend.worker worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=1000 \
    --queues=transcription,correction
