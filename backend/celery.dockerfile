FROM python:3.9.9-slim

RUN apt update && apt install -y \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    ffmpeg \
    libsm6 \ 
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip

RUN pip3 install poetry

RUN mkdir -p /app

COPY . /app

WORKDIR /app

RUN poetry config virtualenvs.create false

RUN poetry install --no-dev --no-interaction --no-ansi

ENV C_FORCE_ROOT=1

ENV PYTHONPATH=/app

# Create the /var/run/celery directory and set permissions
RUN mkdir -p /var/run/celery && chown -R nobody:nogroup /var/run/celery

RUN chmod +x worker-start.sh

CMD ["bash", "worker-start.sh"]