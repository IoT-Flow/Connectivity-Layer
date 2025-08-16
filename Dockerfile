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

# Run the application using Gunicorn with gevent for better concurrency
# Gunicorn settings via environment variables
ENV GUNICORN_WORKERS=3
ENV GUNICORN_WORKER_CONNECTIONS=1000
ENV GUNICORN_TIMEOUT=120

# Run the application using Gunicorn
CMD gunicorn -b 0.0.0.0:5000 \
    --worker-class gevent \
    --workers $GUNICORN_WORKERS \
    --worker-connections $GUNICORN_WORKER_CONNECTIONS \
    --timeout $GUNICORN_TIMEOUT \
    app:app
