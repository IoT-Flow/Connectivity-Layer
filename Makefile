.PHONY: help install format format-check lint test test-unit test-integration test-e2e test-cov test-cov-unit test-cov-integration test-cov-e2e ci ci-fast clean

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make format           - Format code with Black"
	@echo "  make format-check     - Check code formatting"
	@echo "  make lint             - Lint code with flake8"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-e2e         - Run e2e tests only"
	@echo "  make test-cov         - Run all tests with coverage"
	@echo "  make test-cov-unit    - Run unit tests with coverage"
	@echo "  make test-cov-integration - Run integration tests with coverage"
	@echo "  make test-cov-e2e     - Run e2e tests with coverage"
	@echo "  make ci               - Run all CI checks (format, lint, unit+integration tests)"
	@echo "  make ci-fast          - Run fast CI checks (format, lint, unit tests only)"
	@echo "  make clean            - Clean cache and build files"

install:
	poetry install

format:
	poetry run black src/ tests/

format-check:
	poetry run black --check src/ tests/

lint:
	poetry run flake8 src/ tests/

test:
	poetry run pytest

test-unit:
	poetry run pytest tests/unit/

test-integration:
	poetry run pytest tests/integration/

test-e2e:
	poetry run pytest tests/e2e/

test-cov:
	poetry run pytest --cov=src --cov-report=term-missing --cov-report=html:build/coverage/htmlcov --cov-report=xml:build/coverage/coverage.xml

test-cov-unit:
	poetry run pytest tests/unit/ --cov=src --cov-report=term-missing --cov-report=html:build/coverage/htmlcov --cov-report=xml:build/coverage/coverage.xml

test-cov-integration:
	poetry run pytest tests/integration/ --cov=src --cov-report=term-missing --cov-report=html:build/coverage/htmlcov --cov-report=xml:build/coverage/coverage.xml

test-cov-e2e:
	poetry run pytest tests/e2e/ --cov=src --cov-report=term-missing --cov-report=html:build/coverage/htmlcov --cov-report=xml:build/coverage/coverage.xml

ci:
	@echo "🚀 Running full CI checks locally..."
	@echo ""
	@echo "📝 Step 1/4: Checking code formatting..."
	@poetry run black --check src/ tests/ && echo "✅ Formatting check passed" || (echo "❌ Formatting check failed. Run 'make format' to fix." && exit 1)
	@echo ""
	@echo "🔍 Step 2/4: Linting code..."
	@poetry run flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics && echo "✅ Critical lint checks passed" || (echo "❌ Linting failed" && exit 1)
	@echo ""
	@echo "🧪 Step 3/4: Running unit and integration tests..."
	@poetry run pytest tests/unit/ tests/integration/ --cov=src --cov-report=term-missing --cov-report=html:build/coverage/htmlcov --cov-report=xml:build/coverage/coverage.xml && echo "✅ Unit and integration tests passed" || (echo "❌ Unit/integration tests failed" && exit 1)
	@echo ""
	@echo "🌐 Step 4/4: Running e2e tests..."
	@poetry run pytest tests/e2e/ && echo "✅ E2E tests passed" || (echo "❌ E2E tests failed" && exit 1)
	@echo ""
	@echo "✅ All CI checks passed! Ready to push. 🎉"

ci-fast:
	@echo "🚀 Running fast CI checks locally..."
	@echo ""
	@echo "📝 Step 1/3: Checking code formatting..."
	@poetry run black --check src/ tests/ && echo "✅ Formatting check passed" || (echo "❌ Formatting check failed. Run 'make format' to fix." && exit 1)
	@echo ""
	@echo "🔍 Step 2/3: Linting code..."
	@poetry run flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics && echo "✅ Critical lint checks passed" || (echo "❌ Linting failed" && exit 1)
	@echo ""
	@echo "🧪 Step 3/3: Running unit tests only..."
	@poetry run pytest tests/unit/ --cov=src --cov-report=term-missing --cov-report=html:build/coverage/htmlcov --cov-report=xml:build/coverage/coverage.xml && echo "✅ Unit tests passed" || (echo "❌ Unit tests failed" && exit 1)
	@echo ""
	@echo "✅ Fast CI checks passed! 🎉"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf build/coverage/ htmlcov/ .coverage coverage.xml coverage.json
