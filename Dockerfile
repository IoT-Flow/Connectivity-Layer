# Dockerfile for Flask application
FROM python:3.12-slim

# Prevents Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Ensures that the Python output is sent straight to terminal without buffering
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock ./

COPY . .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false --local && \
    poetry install --no-interaction --no-ansi --only main
    

# Copy project

# Expose Flask port
EXPOSE 5000

# Environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Set default environment variables from .env.example
ENV DATABASE_URL=sqlite:///iotflow.db \
    DB_PRIMARY_PATH=instance/iotflow.db \
    DB_FALLBACK_PATH=iotflow.db \
    IOTDB_HOST=localhost \
    IOTDB_PORT=6667 \
    IOTDB_USERNAME=root \
    IOTDB_PASSWORD=root \
    IOTDB_DATABASE=root.iotflow \
    FLASK_APP=app.py \
    FLASK_ENV=development \
    FLASK_DEBUG=True \
    SECRET_KEY=your-secret-key-change-this-in-production \
    HOST=0.0.0.0 \
    PORT=5000 \
    LOG_LEVEL=INFO \
    LOG_FILE=logs/iot_connectivity.log \
    TIMESTAMP_FORMAT=readable \
    TIMESTAMP_TIMEZONE=UTC \
    SIMULATOR_TIMESTAMP_FORMAT=random \
    RATE_LIMIT_PER_MINUTE=60 \
    RATE_LIMIT_BURST=10 \
    API_KEY_LENGTH=32 \
    SESSION_TIMEOUT=3600 \
    IOTFLOW_ADMIN_TOKEN=test \
    REDIS_URL=redis://localhost:6379/0 \
    MQTT_HOST=localhost \
    MQTT_PORT=1883 \
    MQTT_TLS_PORT=8883 \
    MQTT_WEBSOCKET_PORT=9001 \
    MQTT_USERNAME=admin \
    MQTT_PASSWORD=admin123 \
    MQTT_CLIENT_ID=iotflow_server \
    MQTT_KEEPALIVE=60 \
    MQTT_CLEAN_SESSION=true \
    MQTT_MAX_RETRIES=5 \
    MQTT_RETRY_DELAY=5 \
    MQTT_AUTO_RECONNECT=true \
    MQTT_MAX_INFLIGHT_MESSAGES=20 \
    MQTT_MESSAGE_RETRY_SET=20 \
    MQTT_DEFAULT_QOS=1 \
    MQTT_USE_TLS=false \
    MQTT_TLS_INSECURE=false 
    

# Run the application using Gunicorn with gevent for better concurrency
# Gunicorn settings via environment variables
ENV GUNICORN_WORKERS=3
ENV GUNICORN_WORKER_CONNECTIONS=1000
ENV GUNICORN_TIMEOUT=120

# Generate .env from actual environment variables and start the app
ENTRYPOINT ["/bin/sh", "-c", \
    "for key in $(grep -E '^[A-Za-z_][A-Za-z_0-9_]*=' /app/.env.example | cut -d= -f1); do \
         val=$(printenv $key || echo); \
         printf '%s=%s\n' \"$key\" \"$val\" >> /app/.env; \
     done && \
     exec gunicorn -b 0.0.0.0:5000 --worker-class gevent --workers $GUNICORN_WORKERS --worker-connections $GUNICORN_WORKER_CONNECTIONS --timeout $GUNICORN_TIMEOUT app:app" ]
