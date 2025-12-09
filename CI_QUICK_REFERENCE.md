# CI Quick Reference Guide

## 🚀 Running CI Locally

```bash
# Full CI pipeline (recommended before pushing)
./run-ci-locally.sh

# Individual commands
make format        # Auto-format code
make format-check  # Check formatting only
make lint          # Run linting
make test          # Run tests
make test-cov      # Run tests with coverage
make ci            # Run all CI checks
```

## 📊 Current Status

- ✅ **279 tests** passing
- ✅ **55.34% coverage**
- ✅ **All formatting** checks pass
- ✅ **No linting** errors

## 🔧 Services Required

```bash
# Start services
docker compose up -d postgres redis

# Check services
docker compose ps

# Stop services
docker compose down
```

## 📝 Before Pushing

1. Run `./run-ci-locally.sh`
2. Ensure all checks pass
3. Commit and push

## 🐛 Common Issues

### Tests Failing
```bash
# Run specific test
poetry run pytest tests/unit/test_mqtt_client.py -v

# Run with output
poetry run pytest tests/unit/test_mqtt_client.py -v -s
```

### Formatting Issues
```bash
# Auto-fix formatting
make format
```

### Services Not Running
```bash
# Restart services
docker compose restart postgres redis

# Check logs
docker compose logs postgres
docker compose logs redis
```

## 📈 Coverage Goals

| Module | Current | Target |
|--------|---------|--------|
| MQTT Client | 55% | 70% |
| Device Cache | 74% | 85% |
| Time Utils | 96% | 98% |
| IoTDB Service | 37% | 60% |
| Overall | 55% | 70% |

## 🎯 CI Pipeline Steps

1. **Setup** - Install Python, Poetry, dependencies
2. **Format Check** - Verify code formatting with Black
3. **Lint** - Check code quality with flake8
4. **Test** - Run 279 tests with coverage
5. **Report** - Upload coverage to Codecov

## 📦 Key Dependencies

- Python 3.11
- PostgreSQL 15
- Redis 7
- Poetry 1.7.1
- Flask 2.3+
- pytest 7.4+
- apache-iotdb-client-py 1.3+
- paho-mqtt 1.6+

## 🔗 Useful Commands

```bash
# View coverage report
poetry run coverage report

# Open HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Run specific test class
poetry run pytest tests/unit/test_mqtt_client.py::TestMQTTConfig -v

# Run tests matching pattern
poetry run pytest -k "mqtt" -v

# Run with coverage for specific module
poetry run pytest --cov=src/mqtt --cov-report=term-missing
```

## 🎨 Code Style

- **Line length**: 120 characters
- **Formatter**: Black
- **Linter**: flake8
- **Import sorting**: isort (profile: black)

## 📚 Documentation

- Full details: `CI_IMPROVEMENTS.md`
- Test coverage: `TDD_COVERAGE_IMPROVEMENT.md`
- Architecture: `ARCHITECTURE_DECISION.md`
