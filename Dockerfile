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

# Run the application
CMD ["flask", "run", "--host=0.0.0.0"]
