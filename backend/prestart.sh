#! /usr/bin/env bash

# Run migrations
alembic revision --autogenerate -m "Initial migrate" 
alembic upgrade head