#! /usr/bin/env sh
set -e

HOST=${HOST:-0.0.0.0}
PORT=${PORT:-80}
LOG_LEVEL=${LOG_LEVEL:-info}

# Start Uvicorn with live reload
exec uvicorn --reload --host $HOST --port $PORT --log-level $LOG_LEVEL main:app
