#! /usr/bin/env bash
set -e

# Start Celery worker in the background
celery -A celeryworker.celeryapp worker -Ofair --concurrency=8 --without-heartbeat --without-gossip --without-mingle --loglevel=info -E --statedb=/var/run/celery/worker.state