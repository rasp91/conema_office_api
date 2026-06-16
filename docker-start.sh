#!/bin/sh

LOG_DIR=/app/logs
LOG_FILE=$LOG_DIR/startup.log
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Rochling Office API starting ==="

log "--- Running Alembic validation ---"
python alembic_validator.py >> "$LOG_FILE" 2>&1
VALID=$?

if [ "$VALID" -ne 0 ]; then
    log "Migrations not up to date or validation failed. Running: alembic upgrade head"
    python -m alembic upgrade head >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        log "ERROR: alembic upgrade head failed! Aborting startup."
        exit 1
    fi
    log "Migrations applied successfully."
else
    log "Database schema is up to date. No migrations needed."
fi

log "Starting uvicorn on port $APP_PORT"
exec uvicorn src.app:app --host 0.0.0.0 --port "$APP_PORT"
