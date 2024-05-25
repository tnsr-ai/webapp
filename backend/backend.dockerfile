FROM python:3.9-slim

LABEL maintainer="Amit Bera <amitalokbera@gmail.com>"

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
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip

RUN pip3 install poetry

COPY ./start.sh /start.sh

RUN chmod +x /start.sh

COPY ./start-reload.sh /start-reload.sh

RUN chmod +x /start-reload.sh

RUN mkdir -p /app

COPY . /app

WORKDIR /app

RUN poetry config virtualenvs.create false

RUN poetry install --no-dev --no-interaction --no-ansi

ENV PYTHONPATH=/app

ENV OTEL_PYTHON_LOG_LEVEL="info"

ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED="true"

# Install Google Chrome
RUN curl -sSL https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt update && \
    apt install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

CMD ["/start.sh"]