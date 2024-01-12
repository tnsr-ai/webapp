#!/bin/sh

set -e 

celery -A celeryworker.celeryapp worker --loglevel=info &

python main.py