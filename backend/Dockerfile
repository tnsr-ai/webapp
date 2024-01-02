# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV ENV "development"
ENV TNSR_DOMAIN "https//localhost3000"
ENV CONTENT_EXPIRE "86400"
ENV JWT_SECRET "dcc9aef90f841fbf5bdfcc4eb15a3a45bf644ddfe1c88927c45af177e2db49e3"
ENV JWT_REFRESH_SECRET "653197c40bddf183fbb3bad4bde9f976e908f1c462651903bf742170509d386f"
ENV JWT_ALGORITHM "HS256"
ENV JWT_ACCESS_TOKEN_EXPIRE_MINUTES "2880"
ENV JWT_REFRESH_TOKEN_EXPIRE_MINUTES "60 * 24 * 7"
ENV JWT_AUTH_TOKEN "NwBH9UcQ6m0I6zRp+UqJ0VeVoGOdbMX+ijKYOmWz//"

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