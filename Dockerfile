# ================================
# Multi-stage Build - Connectivity Layer
# Small, secure, production-ready Python image
# ================================

# Stage 1: Builder
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry==1.7.1 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main --no-root && \
    pip uninstall -y poetry

# Stage 2: Runtime
FROM python:3.10-slim

# ================================
# Build Arguments (Configuration)
# ================================

# Database
ARG DATABASE_URL=postgresql://iotflow:iotflowpass@postgres:5432/iotflow

# IoTDB
ARG IOTDB_HOST=localhost
ARG IOTDB_PORT=6667
ARG IOTDB_USERNAME=root
ARG IOTDB_PASSWORD=root
ARG IOTDB_DATABASE=root.iotflow

# Flask
ARG FLASK_ENV=production
ARG FLASK_DEBUG=False
ARG SECRET_KEY=change-this-in-production

# CORS
ARG ALLOWED_ORIGINS=http://localhost:3000

# Server
ARG HOST=0.0.0.0
ARG PORT=5000

# Logging
ARG LOG_LEVEL=INFO
ARG LOG_FILE=logs/iot_connectivity.log

# Timestamp
ARG TIMESTAMP_FORMAT=readable
ARG TIMESTAMP_TIMEZONE=UTC

# Rate Limiting
ARG RATE_LIMIT_PER_MINUTE=60
ARG RATE_LIMIT_BURST=10

# Security
ARG API_KEY_LENGTH=32
ARG SESSION_TIMEOUT=3600
ARG IOTFLOW_ADMIN_TOKEN=change-this-token

# Redis
ARG REDIS_URL=redis://localhost:6379/0

# MQTT
ARG MQTT_HOST=localhost
ARG MQTT_PORT=1883
ARG MQTT_TLS_PORT=8883
ARG MQTT_WEBSOCKET_PORT=9001
ARG MQTT_USERNAME=admin
ARG MQTT_PASSWORD=admin123
ARG MQTT_CLIENT_ID=iotflow_server
ARG MQTT_KEEPALIVE=60
ARG MQTT_CLEAN_SESSION=true
ARG MQTT_MAX_RETRIES=5
ARG MQTT_RETRY_DELAY=5
ARG MQTT_AUTO_RECONNECT=true
ARG MQTT_MAX_INFLIGHT_MESSAGES=20
ARG MQTT_MESSAGE_RETRY_SET=20
ARG MQTT_DEFAULT_QOS=1
ARG MQTT_USE_TLS=false
ARG MQTT_TLS_INSECURE=false

# ================================
# Environment Variables
# ================================

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    \
    DATABASE_URL=${DATABASE_URL} \
    \
    IOTDB_HOST=${IOTDB_HOST} \
    IOTDB_PORT=${IOTDB_PORT} \
    IOTDB_USERNAME=${IOTDB_USERNAME} \
    IOTDB_PASSWORD=${IOTDB_PASSWORD} \
    IOTDB_DATABASE=${IOTDB_DATABASE} \
    \
    FLASK_ENV=${FLASK_ENV} \
    FLASK_DEBUG=${FLASK_DEBUG} \
    SECRET_KEY=${SECRET_KEY} \
    \
    ALLOWED_ORIGINS=${ALLOWED_ORIGINS} \
    \
    HOST=${HOST} \
    PORT=${PORT} \
    \
    LOG_LEVEL=${LOG_LEVEL} \
    LOG_FILE=${LOG_FILE} \
    \
    TIMESTAMP_FORMAT=${TIMESTAMP_FORMAT} \
    TIMESTAMP_TIMEZONE=${TIMESTAMP_TIMEZONE} \
    \
    RATE_LIMIT_PER_MINUTE=${RATE_LIMIT_PER_MINUTE} \
    RATE_LIMIT_BURST=${RATE_LIMIT_BURST} \
    \
    API_KEY_LENGTH=${API_KEY_LENGTH} \
    SESSION_TIMEOUT=${SESSION_TIMEOUT} \
    IOTFLOW_ADMIN_TOKEN=${IOTFLOW_ADMIN_TOKEN} \
    \
    REDIS_URL=${REDIS_URL} \
    \
    MQTT_HOST=${MQTT_HOST} \
    MQTT_PORT=${MQTT_PORT} \
    MQTT_TLS_PORT=${MQTT_TLS_PORT} \
    MQTT_WEBSOCKET_PORT=${MQTT_WEBSOCKET_PORT} \
    MQTT_USERNAME=${MQTT_USERNAME} \
    MQTT_PASSWORD=${MQTT_PASSWORD} \
    MQTT_CLIENT_ID=${MQTT_CLIENT_ID} \
    MQTT_KEEPALIVE=${MQTT_KEEPALIVE} \
    MQTT_CLEAN_SESSION=${MQTT_CLEAN_SESSION} \
    MQTT_MAX_RETRIES=${MQTT_MAX_RETRIES} \
    MQTT_RETRY_DELAY=${MQTT_RETRY_DELAY} \
    MQTT_AUTO_RECONNECT=${MQTT_AUTO_RECONNECT} \
    MQTT_MAX_INFLIGHT_MESSAGES=${MQTT_MAX_INFLIGHT_MESSAGES} \
    MQTT_MESSAGE_RETRY_SET=${MQTT_MESSAGE_RETRY_SET} \
    MQTT_DEFAULT_QOS=${MQTT_DEFAULT_QOS} \
    MQTT_USE_TLS=${MQTT_USE_TLS} \
    MQTT_TLS_INSECURE=${MQTT_TLS_INSECURE}

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app.py ./
COPY src/ ./src/
COPY mqtt/ ./mqtt/

# Create non-root user and directories
RUN groupadd -r iotflow && \
    useradd -r -g iotflow iotflow && \
    mkdir -p logs instance mqtt/data mqtt/logs && \
    chown -R iotflow:iotflow /app

USER iotflow

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)" || exit 1

# Run with Python
CMD ["python", "app.py"]