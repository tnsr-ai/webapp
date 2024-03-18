#!/bin/bash
docker compose stop && docker compose up --build -d && docker image prune -f