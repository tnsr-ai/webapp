#!/bin/bash

# Define the compose files
COMPOSE_FILES="-f dockercompose-db.yml -f dockercompose-app.yml -f dockercompose-monitoring.yml -f dockercompose-proxy.yml -f dockercompose-celery.yml"

# Stop the running containers
docker compose $COMPOSE_FILES stop

# Remove old containers to ensure clean rebuild
docker compose $COMPOSE_FILES rm -f

# Rebuild and start the containers
docker compose $COMPOSE_FILES up --build -d

# Wait for containers to be fully running before pruning
sleep 10

# Remove only dangling images (not unused ones)
docker image prune -f

# Remove build cache but keep recent builds
docker builder prune --keep-storage 1GB -f