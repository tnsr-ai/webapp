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
    curl \
    ghostscript \
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

# Install Google Chrome
RUN curl -sSL https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt update && \
    apt install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

CMD ["bash", "worker-start.sh"]