#! /usr/bin/env sh
set -e

# Start with uvicorn directly for proper OpenTelemetry logging integration
# For production with multiple workers, you can use gunicorn, but it requires additional configuration
# for proper log correlation. Using uvicorn directly is recommended for observability.
exec python main.py
