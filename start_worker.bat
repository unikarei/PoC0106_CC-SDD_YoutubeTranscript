@echo off
REM Worker startup script for Windows local development

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Start Celery worker
celery -A backend.worker worker --loglevel=info --concurrency=2 --pool=solo --queues=transcription,correction
