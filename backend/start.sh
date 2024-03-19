#! /usr/bin/env sh
set -e

# Start Gunicorn
rm -rf multiproc-tmp
mkdir multiproc-tmp
export PROMETHEUS_MULTIPROC_DIR=multiproc-tmp
exec gunicorn -c gunicorn_conf.py --workers 4 -k uvicorn.workers.UvicornWorker  --name fastapi-backend main:app
