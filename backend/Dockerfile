# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set work directory
WORKDIR /app
COPY . /app

# Exclude the virtual environment directory from being copied
COPY . /app
COPY .dockerignore ./

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc && apt-get install -y ffmpeg  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN rm -rf /app/env

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Install Poetry and project dependencies
RUN pip install poetry
RUN poetry install --no-dev --no-ansi

# Command to run the application
CMD ["uvicorn", "main:app", "--port", "8000", "--host", "0.0.0.0"]