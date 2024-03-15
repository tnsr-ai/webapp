#! /usr/bin/env bash
set -e

celery -A celeryworker.celeryapp worker -Ofair --concurrency=8 --without-heartbeat --without-gossip --without-mingle --loglevel=info