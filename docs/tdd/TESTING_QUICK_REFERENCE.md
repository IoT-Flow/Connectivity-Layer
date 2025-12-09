# Testing Quick Reference Guide

## 🚀 Quick Start

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## 📝 Common Commands

### Running Tests

```bash
# All tests
pytest

# Verbose output
pytest -v

# Quiet output
pytest -q

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run failed tests first
pytest --ff
```

### Test Selection

```bash
# Run specific file
pytest tests/unit/test_models.py

# Run specific class
pytest tests/unit/test_models.py::TestUserModel

# Run specific test
pytest tests/unit/test_models.py::TestUserModel::test_user_creation

# Run by pattern
pytest -k "user"  # Runs all tests with "user" in name
pytest -k "not slow"  # Exclude slow tests
```

### Test Categories (Markers)

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# E2E tests only
pytest -m e2e

# Exclude slow tests
pytest -m "not slow"

# Multiple markers
pytest -m "unit or integration"
```

### Coverage

```bash
# Basic coverage
pytest --cov=src

# HTML report
pytest --cov=src --cov-report=html

# Terminal report with missing lines
pytest --cov=src --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=src --cov-report=xml

# Minimum coverage threshold
pytest --cov=src --cov-fail-under=80
```

### Output Control

```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Detailed traceback
pytest --tb=long

# Short traceback
pytest --tb=short

# Line-only traceback
pytest --tb=line

# No traceback
pytest --tb=no
```

---

## 🎯 Test Organization

### Current Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests (16 tests)
│   └── test_models.py
├── integration/             # Integration tests (18 tests)
│   └── test_device_api.py
└── e2e/                     # End-to-end tests (future)
```

### Test Markers

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - API integration tests
- `@pytest.mark.e2e` - End-to-end workflow tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.mqtt` - Tests requiring MQTT broker
- `@pytest.mark.iotdb` - Tests requiring IoTDB
- `@pytest.mark.redis` - Tests requiring Redis

---

## 🔧 Fixtures Available

### Application Fixtures
- `app` - Flask application with test config
- `client` - HTTP test client
- `runner` - CLI test runner

### Database Fixtures
- `db_session` - Database session with rollback

### User Fixtures
- `test_user` - Regular test user
- `test_admin_user` - Admin test user

### Device Fixtures
- `test_device` - Single test device
- `multiple_devices` - Multiple test devices (3)

### Authentication Fixtures
- `auth_headers` - Device API key headers
- `admin_headers` - Admin authentication headers

### Mock Fixtures
- `mock_redis` - Mocked Redis client
- `mock_iotdb` - Mocked IoTDB client

---

## 📊 Coverage Goals

| Component | Current | Target | Priority |
|-----------|---------|--------|----------|
| Models | 81.38% | 95% | ✅ Good |
| Routes | 51.79% | 85% | ⚠️ Medium |
| Services | 8-12% | 90% | 🔴 High |
| Middleware | 30-58% | 90% | 🔴 High |
| Overall | 24.93% | 85% | 🔴 High |

---

## 🐛 Debugging Tests

### Show More Information

```bash
# Show print statements and logs
pytest -s -v

# Show local variables on failure
pytest -l

# Show full diff on assertion errors
pytest -vv

# Capture mode: no (show all output)
pytest --capture=no
```

### Debug Specific Test

```bash
# Run single test with full output
pytest tests/unit/test_models.py::TestUserModel::test_user_creation -vv -s

# Add breakpoint in test
# In test file: import pdb; pdb.set_trace()
pytest tests/unit/test_models.py -s
```

### Check Test Collection

```bash
# List all tests without running
pytest --collect-only

# List tests in specific file
pytest tests/unit/test_models.py --collect-only

# Count tests
pytest --collect-only -q
```

---

## 📈 Performance

### Timing

```bash
# Show slowest 10 tests
pytest --durations=10

# Show all test durations
pytest --durations=0

# Show only tests slower than 1s
pytest --durations-min=1.0
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (auto-detect CPUs)
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

---

## 🔍 Test Writing Tips

### Test Naming

```python
# Good test names
def test_user_creation_with_valid_data_succeeds():
def test_device_registration_with_duplicate_name_returns_409():
def test_api_key_generation_creates_unique_keys():

# Bad test names
def test_user():
def test_1():
def test_device_stuff():
```

### AAA Pattern

```python
def test_example():
    # Arrange - Set up test data
    user = User(username="test", email="test@example.com")
    
    # Act - Perform the action
    result = user.save()
    
    # Assert - Verify the result
    assert result is True
    assert user.id is not None
```

### Using Fixtures

```python
def test_with_fixture(test_user, client):
    """Use fixtures for common setup"""
    response = client.get(f'/users/{test_user.id}')
    assert response.status_code == 200
```

### Parametrize Tests

```python
@pytest.mark.parametrize("status", ["active", "inactive", "maintenance"])
def test_device_status_values(status):
    """Test multiple values with one test"""
    device = Device(name="Test", status=status)
    assert device.status == status
```

---

## 🚨 Common Issues

### Import Errors

```bash
# Problem: ModuleNotFoundError
# Solution: Install dependencies
pip install -r requirements.txt

# Or install specific package
pip install pytest pytest-flask pytest-cov
```

### Database Errors

```bash
# Problem: Database locked or constraint errors
# Solution: Use db_session fixture
def test_example(db_session):
    # db_session handles transactions and rollback
    pass
```

### Fixture Errors

```bash
# Problem: Fixture not found
# Solution: Check conftest.py is in tests/ directory
# and fixture is properly defined
```

### Coverage Not Working

```bash
# Problem: Coverage shows 0%
# Solution: Ensure source path is correct
pytest --cov=src  # Not --cov=.
```

---

## 📚 Resources

### Documentation
- pytest: https://docs.pytest.org/
- pytest-flask: https://pytest-flask.readthedocs.io/
- pytest-cov: https://pytest-cov.readthedocs.io/

### Project Docs
- `TDD_APPROACH.md` - Complete TDD guide
- `TDD_SUCCESS_REPORT.md` - Implementation results
- `API_ENDPOINTS_SUMMARY.md` - API documentation

### Configuration Files
- `pytest.ini` - Pytest configuration
- `.coveragerc` - Coverage settings
- `conftest.py` - Shared fixtures

---

## 🎓 Best Practices

### DO ✅
- Write tests before code (TDD)
- Use descriptive test names
- Follow AAA pattern
- Keep tests independent
- Use fixtures for common setup
- Test edge cases
- Aim for high coverage

### DON'T ❌
- Share state between tests
- Test implementation details
- Write tests that depend on order
- Ignore failing tests
- Skip writing tests for "simple" code
- Test external services directly (use mocks)

---

## 🏃 Quick Test Workflow

### 1. Before Starting Work
```bash
# Ensure all tests pass
pytest
```

### 2. While Developing (TDD)
```bash
# Write failing test
# Run specific test
pytest tests/unit/test_models.py::TestNewFeature -v

# Write code to make it pass
# Run test again
pytest tests/unit/test_models.py::TestNewFeature -v

# Refactor and verify
pytest tests/unit/test_models.py::TestNewFeature -v
```

### 3. Before Committing
```bash
# Run all tests
pytest

# Check coverage
pytest --cov=src --cov-report=term-missing

# Ensure no warnings
pytest --strict-markers
```

### 4. After Committing
```bash
# CI/CD will run:
pytest --cov=src --cov-report=xml --cov-fail-under=80
```

---

## 📊 Current Status

**Last Updated:** December 8, 2025

```
Total Tests: 34
Passing: 34 (100%)
Failing: 0 (0%)
Coverage: 24.93% overall, 81.38% models
Execution Time: ~3 seconds
```

### Test Breakdown
- Unit Tests: 16/16 ✅
- Integration Tests: 18/18 ✅
- E2E Tests: 0 (planned)

---

## 🎯 Next Steps

1. Add service layer tests (IoTDB, Redis, Cache)
2. Add middleware tests (Auth, Security, Monitoring)
3. Expand integration tests (Admin, MQTT, Telemetry)
4. Create E2E test suite
5. Increase coverage to 85%+

---

**Quick Help:**
```bash
pytest --help          # Show all options
pytest --markers       # Show available markers
pytest --fixtures      # Show available fixtures
pytest --version       # Show pytest version
```
