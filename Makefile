.PHONY: help install format format-check lint test test-cov clean

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make format        - Format code with Black"
	@echo "  make format-check  - Check code formatting"
	@echo "  make lint          - Lint code with flake8"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make clean         - Clean cache and build files"

install:
	pip install -r requirements.txt
	pip install black flake8 pytest pytest-cov

format:
	black src/ tests/

format-check:
	black --check src/ tests/

lint:
	flake8 src/ tests/

test:
	pytest

test-cov:
	pytest --cov=src --cov-report=term-missing --cov-report=html

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage coverage.xml
