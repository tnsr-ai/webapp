#!/bin/bash

# Stop the running containers
docker compose stop

# Rebuild and start the containers in the background
docker compose up --build -d

# Remove unused images and build cache
docker image prune -af
docker builder prune -af