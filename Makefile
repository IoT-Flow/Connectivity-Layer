.PHONY: help install format format-check lint test test-cov ci clean

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make format        - Format code with Black"
	@echo "  make format-check  - Check code formatting"
	@echo "  make lint          - Lint code with flake8"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make ci            - Run all CI checks locally"
	@echo "  make clean         - Clean cache and build files"

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

test-cov:
	poetry run pytest --cov=src --cov-report=term-missing --cov-report=html

ci:
	@echo "🚀 Running CI checks locally..."
	@echo ""
	@echo "📝 Step 1/3: Checking code formatting..."
	@poetry run black --check src/ tests/ && echo "✅ Formatting check passed" || (echo "❌ Formatting check failed. Run 'make format' to fix." && exit 1)
	@echo ""
	@echo "🔍 Step 2/3: Linting code..."
	@poetry run flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics && echo "✅ Critical lint checks passed" || (echo "❌ Linting failed" && exit 1)
	@echo ""
	@echo "🧪 Step 3/3: Running tests..."
	@poetry run pytest --cov=src --cov-report=term-missing && echo "✅ Tests passed" || (echo "❌ Tests failed" && exit 1)
	@echo ""
	@echo "✅ All CI checks passed! Ready to push. 🎉"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage coverage.xml
