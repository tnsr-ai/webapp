#!/bin/bash

# Define the compose files
COMPOSE_FILES="-f dockercompose-db.yml -f dockercompose-app.yml -f dockercompose-monitoring.yml -f dockercompose-proxy.yml -f dockercompose-celery.yml"

# Stop the running containers
docker compose $COMPOSE_FILES stop

# Rebuild and start the containers in the background
docker compose $COMPOSE_FILES up --build -d

# Remove unused images and build cache
docker image prune -af
docker builder prune -af

# docker compose -f dockercompose-db.yml -f dockercompose-app.yml -f dockercompose-monitoring.yml -f dockercompose-proxy.yml -f dockercompose-celery.yml up -d