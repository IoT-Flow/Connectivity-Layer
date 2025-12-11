#!/bin/bash

# Script to run CI checks locally with required services
# This mimics the GitHub Actions CI pipeline

set -e

echo "🚀 Starting local CI pipeline..."
echo ""

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not running"
    exit 1
fi

# Determine docker compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Function to check if services are running
check_services() {
    echo "🔍 Checking if required services are running..."
    
    # Check PostgreSQL
    if ! docker ps | grep -q iotflow_postgres; then
        echo "⚠️  PostgreSQL is not running"
        return 1
    fi
    
    # Check Redis
    if ! docker ps | grep -q iotflow_redis; then
        echo "⚠️  Redis is not running"
        return 1
    fi
    
    echo "✅ All required services are running"
    return 0
}

# Start services if not running
if ! check_services; then
    echo ""
    echo "🐳 Starting required services (PostgreSQL and Redis)..."
    $DOCKER_COMPOSE up -d postgres redis
    
    echo "⏳ Waiting for services to be healthy..."
    sleep 5
    
    # Wait for PostgreSQL
    echo "   Waiting for PostgreSQL..."
    for i in {1..30}; do
        if docker exec iotflow_postgres pg_isready -U iotflow &> /dev/null; then
            echo "   ✅ PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "   ❌ PostgreSQL failed to start"
            exit 1
        fi
        sleep 1
    done
    
    # Wait for Redis
    echo "   Waiting for Redis..."
    for i in {1..30}; do
        if docker exec iotflow_redis redis-cli ping &> /dev/null; then
            echo "   ✅ Redis is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "   ❌ Redis failed to start"
            exit 1
        fi
        sleep 1
    done
fi

echo ""
echo "🔧 Setting up test environment variables..."
export DATABASE_URL="postgresql://iotflow:iotflowpass@localhost:5432/iotflow"
export REDIS_URL="redis://localhost:6379/0"
export FLASK_ENV="testing"

echo ""
echo "📦 Checking Poetry installation..."
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install it first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

echo ""
echo "📥 Installing dependencies..."
poetry install --no-interaction

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Running CI Checks"
echo "═══════════════════════════════════════════════════════════"

# Run the CI checks using make
make ci

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ Local CI Pipeline Completed Successfully! 🎉"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Your code is ready to be pushed to the repository."
echo ""
echo "To stop the services, run:"
echo "  $DOCKER_COMPOSE down"
