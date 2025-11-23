.PHONY: help install test lint format clean docker-build docker-run ci-test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	poetry install

install-dev: ## Install development dependencies
	poetry install --with dev
	pre-commit install

test: ## Run tests
	poetry run pytest tests/ -v

test-cov: ## Run tests with coverage
	poetry run pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-fast: ## Run tests without slow tests
	poetry run pytest tests/ -v -m "not slow"

lint: ## Run linting checks
	poetry run flake8 src tests
	poetry run mypy src --ignore-missing-imports --exclude 'src/models/__init__.py'

format: ## Format code
	poetry run black src tests
	poetry run isort src tests

format-check: ## Check code formatting
	poetry run black --check src tests
	poetry run isort --check-only src tests

security: ## Run security checks
	poetry run bandit -r src -ll

clean: ## Clean up generated files
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build: ## Build Docker image
	docker build -t iotflow:latest .

docker-run: ## Run Docker container
	docker-compose up

docker-stop: ## Stop Docker containers
	docker-compose down

docker-ci: ## Run CI environment with Docker
	docker-compose -f docker-compose.ci.yml up --build

ci-test: ## Run CI tests locally (without Docker)
	@echo "Running CI tests locally..."
	@echo "1. Running tests..."
	poetry run pytest tests/ -v
	@echo "\n2. Running linting..."
	poetry run flake8 src tests --max-line-length=120 --extend-ignore=E203,W503 || true
	@echo "\n3. Checking code format..."
	poetry run black --check src tests || true
	@echo "\n4. Checking import sorting..."
	poetry run isort --check-only src tests || true
	@echo "\n5. Running security checks..."
	poetry run bandit -r src -ll || true
	@echo "\n✅ CI checks complete!"

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

init-db: ## Initialize database
	poetry run python init_db.py

run: ## Run application
	poetry run python app.py

run-prod: ## Run application with gunicorn
	poetry run gunicorn --bind 0.0.0.0:5000 --workers 4 "app:create_app()"

migrate: ## Run database migrations
	poetry run flask db upgrade

migrate-create: ## Create new migration
	poetry run flask db migrate -m "$(message)"

logs: ## Show application logs
	tail -f logs/iotflow.log

all: clean install test lint ## Run all checks
