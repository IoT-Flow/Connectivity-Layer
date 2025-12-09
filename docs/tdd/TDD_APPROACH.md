# Test-Driven Development (TDD) Approach - Connectivity Layer

## Overview

This document outlines the Test-Driven Development approach for the IoTFlow Connectivity Layer (Python/Flask backend). TDD ensures code quality, maintainability, and reliability through a test-first development methodology.

---

## TDD Philosophy

**Test-Driven Development Cycle:**
```
1. 🔴 RED   → Write a failing test
2. 🟢 GREEN → Write minimal code to pass
3. 🔵 REFACTOR → Improve code quality
4. ♻️  REPEAT → Continue the cycle
```

**Benefits:**
- Ensures code correctness before implementation
- Provides living documentation
- Facilitates refactoring with confidence
- Reduces debugging time
- Improves code design

---

## Testing Stack

### Core Testing Tools

| Tool | Purpose | Version |
|------|---------|---------|
| **pytest** | Test framework | 7.4.2+ |
| **pytest-flask** | Flask testing utilities | 1.2.0+ |
| **pytest-cov** | Code coverage | 4.1.0+ |
| **unittest** | Python standard testing | Built-in |
| **requests** | HTTP testing | 2.32.4+ |
| **paho-mqtt** | MQTT testing | 1.6.1+ |

### Additional Tools

- **pytest-mock** - Mocking and patching
- **faker** - Test data generation
- **freezegun** - Time manipulation for tests
- **responses** - HTTP request mocking
- **pytest-asyncio** - Async testing support

---

## Test Structure

### Directory Organization

```
Connectivity-Layer/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures
│   ├── unit/                          # Unit tests
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   ├── test_utils.py
│   │   └── test_middleware.py
│   ├── integration/                   # Integration tests
│   │   ├── test_device_api.py
│   │   ├── test_telemetry_api.py
│   │   ├── test_mqtt_integration.py
│   │   └── test_iotdb_integration.py
│   ├── e2e/                          # End-to-end tests
│   │   ├── test_device_lifecycle.py
│   │   └── test_end_to_end.py
│   └── performance/                   # Performance tests
│       ├── test_load.py
│       └── test_stress.py
├── pytest.ini                         # Pytest configuration
└── .coveragerc                        # Coverage configuration
```

---

## Test Categories

### 1. Unit Tests

**Purpose:** Test individual functions and methods in isolation

**Characteristics:**
- Fast execution (< 1ms per test)
- No external dependencies
- Use mocks for dependencies
- Test single responsibility

**Example Structure:**

```python
# tests/unit/test_models.py
import pytest
from src.models import Device, User

class TestDeviceModel:
    """Unit tests for Device model"""
    
    def test_device_creation(self):
        """Test device instance creation"""
        device = Device(
            name="Test Device",
            device_type="sensor",
            user_id=1
        )
        assert device.name == "Test Device"
        assert device.device_type == "sensor"
        assert device.status == "offline"  # Default value
    
    def test_api_key_generation(self):
        """Test API key is auto-generated"""
        device = Device(name="Test", device_type="sensor")
        assert device.api_key is not None
        assert len(device.api_key) == 64  # 32 bytes hex
    
    def test_update_last_seen(self, db_session):
        """Test last_seen timestamp update"""
        device = Device(name="Test", device_type="sensor")
        db_session.add(device)
        db_session.commit()
        
        old_last_seen = device.last_seen
        device.update_last_seen()
        
        assert device.last_seen > old_last_seen
```

### 2. Integration Tests

**Purpose:** Test interactions between components

**Characteristics:**
- Test API endpoints
- Use test database
- Test service integrations
- Verify data flow

**Example Structure:**
```python
# tests/integration/test_device_api.py
import pytest
from flask import Flask

class TestDeviceAPI:
    """Integration tests for device API endpoints"""
    
    def test_device_registration_success(self, client, test_user):
        """Test successful device registration"""
        payload = {
            "name": "Integration Test Device",
            "device_type": "sensor",
            "user_id": test_user.user_id
        }
        
        response = client.post(
            '/api/v1/devices/register',
            json=payload
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Device registered successfully'
        assert 'api_key' in data['device']
    
    def test_device_registration_duplicate_name(self, client, test_device):
        """Test registration with duplicate name fails"""
        payload = {
            "name": test_device.name,  # Existing device name
            "device_type": "sensor",
            "user_id": test_device.user_id
        }
        
        response = client.post(
            '/api/v1/devices/register',
            json=payload
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'already exists' in data['error'].lower()
```

### 3. End-to-End Tests

**Purpose:** Test complete user workflows

**Characteristics:**
- Test full scenarios
- Use real services (or close replicas)
- Verify business requirements
- Test user journeys

**Example Structure:**
```python
# tests/e2e/test_device_lifecycle.py
import pytest
import time

class TestDeviceLifecycle:
    """E2E tests for complete device lifecycle"""
    
    def test_complete_device_workflow(self, client, mqtt_client):
        """Test: Register → Configure → Send Data → Query → Delete"""
        
        # 1. Register device
        register_response = client.post('/api/v1/devices/register', json={
            "name": "E2E Test Device",
            "device_type": "sensor",
            "user_id": "test_user_id"
        })
        assert register_response.status_code == 201
        device = register_response.get_json()['device']
        api_key = device['api_key']
        device_id = device['id']
        
        # 2. Configure device
        config_response = client.post(
            '/api/v1/devices/config',
            headers={'X-API-Key': api_key},
            json={
                "config_key": "sampling_rate",
                "config_value": "30",
                "data_type": "integer"
            }
        )
        assert config_response.status_code == 200
        
        # 3. Send telemetry via MQTT
        mqtt_client.publish(
            f'iotflow/devices/{device_id}/telemetry',
            json.dumps({
                "api_key": api_key,
                "data": {"temperature": 25.5}
            })
        )
        time.sleep(2)  # Wait for processing
        
        # 4. Query telemetry
        telemetry_response = client.get(
            '/api/v1/devices/telemetry',
            headers={'X-API-Key': api_key}
        )
        assert telemetry_response.status_code == 200
        assert telemetry_response.get_json()['count'] > 0
        
        # 5. Delete device
        delete_response = client.delete(
            f'/api/v1/admin/devices/{device_id}',
            headers={'Authorization': 'admin test'}
        )
        assert delete_response.status_code == 200
```

---

## Test Fixtures

### Common Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from flask import Flask
from src.models import db, User, Device
from src.config.config import config

@pytest.fixture(scope='session')
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config.from_object(config['testing'])
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def db_session(app):
    """Create database session"""
    with app.app_context():
        yield db.session
        db.session.rollback()

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_device(db_session, test_user):
    """Create test device"""
    device = Device(
        name="Test Device",
        device_type="sensor",
        user_id=test_user.id
    )
    db_session.add(device)
    db_session.commit()
    return device

@pytest.fixture
def auth_headers(test_device):
    """Create authentication headers"""
    return {'X-API-Key': test_device.api_key}

@pytest.fixture
def admin_headers():
    """Create admin authentication headers"""
    return {'Authorization': 'admin test'}
```

---

## TDD Workflow Examples

### Example 1: Adding New Device Status Feature

#### Step 1: Write Failing Test (RED 🔴)

```python
# tests/unit/test_device_status.py
def test_device_can_be_marked_as_maintenance(db_session):
    """Test device can be set to maintenance status"""
    device = Device(name="Test", device_type="sensor")
    db_session.add(device)
    db_session.commit()
    
    device.set_maintenance_mode(reason="Firmware update")
    
    assert device.status == "maintenance"
    assert device.maintenance_reason == "Firmware update"
    assert device.maintenance_started_at is not None
```

**Run test:** `pytest tests/unit/test_device_status.py`
**Result:** ❌ FAIL - Method doesn't exist

#### Step 2: Write Minimal Code (GREEN 🟢)

```python
# src/models/device.py
class Device(db.Model):
    # ... existing code ...
    
    maintenance_reason = db.Column(db.String(200))
    maintenance_started_at = db.Column(db.DateTime)
    
    def set_maintenance_mode(self, reason):
        """Set device to maintenance mode"""
        self.status = "maintenance"
        self.maintenance_reason = reason
        self.maintenance_started_at = datetime.now(timezone.utc)
        db.session.commit()
```

**Run test:** `pytest tests/unit/test_device_status.py`
**Result:** ✅ PASS

#### Step 3: Refactor (REFACTOR 🔵)

```python
# src/models/device.py
from enum import Enum

class DeviceStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"

class Device(db.Model):
    # ... existing code ...
    
    def set_maintenance_mode(self, reason: str) -> None:
        """
        Set device to maintenance mode
        
        Args:
            reason: Reason for maintenance
        
        Raises:
            ValueError: If reason is empty
        """
        if not reason or not reason.strip():
            raise ValueError("Maintenance reason is required")
        
        self.status = DeviceStatus.MAINTENANCE.value
        self.maintenance_reason = reason.strip()
        self.maintenance_started_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()
```

**Add more tests:**
```python
def test_maintenance_mode_requires_reason(db_session):
    """Test maintenance mode requires a reason"""
    device = Device(name="Test", device_type="sensor")
    db_session.add(device)
    db_session.commit()
    
    with pytest.raises(ValueError, match="reason is required"):
        device.set_maintenance_mode("")
```

---

### Example 2: Adding Telemetry Validation

#### Step 1: Write Failing Test (RED 🔴)

```python
# tests/unit/test_telemetry_validation.py
from src.services.telemetry_validator import TelemetryValidator

def test_validate_temperature_range():
    """Test temperature validation"""
    validator = TelemetryValidator()
    
    # Valid temperature
    assert validator.validate_temperature(25.0) == True
    
    # Invalid temperatures
    assert validator.validate_temperature(-100.0) == False
    assert validator.validate_temperature(200.0) == False
```

**Result:** ❌ FAIL - Module doesn't exist

#### Step 2: Write Minimal Code (GREEN 🟢)

```python
# src/services/telemetry_validator.py
class TelemetryValidator:
    """Validate telemetry data"""
    
    def validate_temperature(self, value: float) -> bool:
        """Validate temperature is in reasonable range"""
        return -50.0 <= value <= 100.0
```

**Result:** ✅ PASS

#### Step 3: Refactor (REFACTOR 🔵)

```python
# src/services/telemetry_validator.py
from typing import Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of validation"""
    is_valid: bool
    errors: list[str]
    warnings: list[str]

class TelemetryValidator:
    """Validate telemetry data with configurable ranges"""
    
    RANGES = {
        'temperature': (-50.0, 100.0),
        'humidity': (0.0, 100.0),
        'pressure': (800.0, 1200.0),
        'battery_level': (0.0, 100.0)
    }
    
    def validate_temperature(self, value: float) -> bool:
        """Validate temperature is in reasonable range"""
        return self._validate_range(value, 'temperature')
    
    def _validate_range(self, value: float, field: str) -> bool:
        """Generic range validation"""
        if field not in self.RANGES:
            return True  # Unknown fields pass
        
        min_val, max_val = self.RANGES[field]
        return min_val <= value <= max_val
    
    def validate_telemetry(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate complete telemetry payload"""
        errors = []
        warnings = []
        
        for field, value in data.items():
            if not isinstance(value, (int, float)):
                continue
            
            if not self._validate_range(value, field):
                errors.append(
                    f"{field} value {value} outside valid range "
                    f"{self.RANGES.get(field, 'unknown')}"
                )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

---

## Test Coverage Goals

### Coverage Targets

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| **Models** | 95%+ | Critical |
| **Services** | 90%+ | Critical |
| **Routes/Controllers** | 85%+ | High |
| **Middleware** | 90%+ | High |
| **Utils** | 80%+ | Medium |
| **Overall** | 85%+ | - |

### Running Coverage

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Generate coverage badge
coverage-badge -o coverage.svg
```

---

## Testing Best Practices

### 1. Test Naming Convention

```python
# ✅ GOOD: Descriptive test names
def test_device_registration_with_valid_data_returns_201():
    pass

def test_device_registration_with_duplicate_name_returns_409():
    pass

# ❌ BAD: Vague test names
def test_device():
    pass

def test_registration():
    pass
```

### 2. Arrange-Act-Assert (AAA) Pattern

```python
def test_device_status_update():
    # Arrange - Set up test data
    device = Device(name="Test", device_type="sensor")
    db.session.add(device)
    db.session.commit()
    
    # Act - Perform the action
    device.status = "active"
    db.session.commit()
    
    # Assert - Verify the result
    assert device.status == "active"
    assert device.updated_at is not None
```

### 3. Test Independence

```python
# ✅ GOOD: Each test is independent
def test_create_device(db_session):
    device = Device(name="Test1", device_type="sensor")
    db_session.add(device)
    db_session.commit()
    assert device.id is not None

def test_delete_device(db_session):
    device = Device(name="Test2", device_type="sensor")
    db_session.add(device)
    db_session.commit()
    device_id = device.id
    
    db_session.delete(device)
    db_session.commit()
    assert Device.query.get(device_id) is None

# ❌ BAD: Tests depend on each other
device_id = None

def test_create_device():
    global device_id
    device = Device(name="Test", device_type="sensor")
    db.session.add(device)
    db.session.commit()
    device_id = device.id

def test_delete_device():
    global device_id
    device = Device.query.get(device_id)  # Depends on previous test
    db_session.delete(device)
```

### 4. Use Mocks for External Dependencies

```python
# tests/unit/test_iotdb_service.py
from unittest.mock import Mock, patch

def test_store_telemetry_in_iotdb():
    """Test telemetry storage without real IoTDB"""
    with patch('src.services.iotdb.IoTDBClient') as mock_client:
        # Arrange
        mock_client.return_value.insert_record.return_value = True
        service = IoTDBService()
        
        # Act
        result = service.write_telemetry_data(
            device_id="1",
            data={"temperature": 25.0}
        )
        
        # Assert
        assert result == True
        mock_client.return_value.insert_record.assert_called_once()
```

### 5. Test Edge Cases

```python
def test_device_name_validation():
    """Test various device name edge cases"""
    # Empty name
    with pytest.raises(ValueError):
        Device(name="", device_type="sensor")
    
    # Very long name
    long_name = "A" * 101
    with pytest.raises(ValueError):
        Device(name=long_name, device_type="sensor")
    
    # Special characters
    device = Device(name="Device-123_Test", device_type="sensor")
    assert device.name == "Device-123_Test"
    
    # Unicode characters
    device = Device(name="设备001", device_type="sensor")
    assert device.name == "设备001"
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379
      
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      
      - name: Run tests
        run: |
          poetry run pytest --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test
pytest tests/unit/test_models.py::TestDeviceModel::test_device_creation

# Run tests matching pattern
pytest -k "device_registration"

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src

# Run and stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

### Test Markers

```python
# tests/conftest.py
import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "e2e: end-to-end tests")

# Usage in tests
@pytest.mark.slow
def test_large_data_processing():
    pass

@pytest.mark.integration
def test_api_endpoint():
    pass

# Run only unit tests (exclude marked tests)
pytest -m "not slow and not integration"

# Run only integration tests
pytest -m integration
```

---

## Performance Testing

### Load Testing with Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class DeviceUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Register device and get API key"""
        response = self.client.post("/api/v1/devices/register", json={
            "name": f"LoadTest_{self.environment.runner.user_count}",
            "device_type": "sensor",
            "user_id": "test_user"
        })
        self.api_key = response.json()['device']['api_key']
    
    @task(3)
    def send_telemetry(self):
        """Send telemetry data"""
        self.client.post(
            "/api/v1/devices/telemetry",
            headers={"X-API-Key": self.api_key},
            json={
                "data": {
                    "temperature": 25.0,
                    "humidity": 60.0
                }
            }
        )
    
    @task(1)
    def check_status(self):
        """Check device status"""
        self.client.get(
            "/api/v1/devices/status",
            headers={"X-API-Key": self.api_key}
        )

# Run load test
# locust -f tests/performance/locustfile.py --host=http://localhost:5000
```

---

## Documentation

### Test Documentation

```python
class TestDeviceRegistration:
    """
    Test Suite: Device Registration
    
    Purpose:
        Verify device registration functionality including validation,
        error handling, and database persistence.
    
    Test Coverage:
        - Successful registration with valid data
        - Duplicate device name handling
        - Invalid user ID validation
        - Missing required fields
        - Inactive user handling
        - Multiple devices per user
    
    Dependencies:
        - Database (SQLite/PostgreSQL)
        - User model
        - Device model
    
    Related:
        - API Documentation: /docs/api/devices.md
        - User Story: US-001 Device Registration
    """
    
    def test_successful_registration(self):
        """
        Test: Successful device registration
        
        Given: Valid device data and active user
        When: POST /api/v1/devices/register
        Then: Device is created with 201 status
        And: API key is generated
        And: Device is persisted in database
        """
        pass
```

---

## Troubleshooting Tests

### Common Issues

**1. Database State Issues**
```python
# Problem: Tests fail due to database state
# Solution: Use transactions and rollback

@pytest.fixture(autouse=True)
def reset_db(db_session):
    """Reset database after each test"""
    yield
    db_session.rollback()
    db_session.remove()
```

**2. Async/Threading Issues**
```python
# Problem: MQTT tests are flaky
# Solution: Use proper synchronization

import time
from threading import Event

def test_mqtt_message_received():
    received = Event()
    
    def on_message(client, userdata, msg):
        received.set()
    
    client.on_message = on_message
    client.publish("test/topic", "message")
    
    assert received.wait(timeout=5.0), "Message not received"
```

**3. Time-Dependent Tests**
```python
# Problem: Tests fail due to timing
# Solution: Use freezegun

from freezegun import freeze_time

@freeze_time("2025-01-01 12:00:00")
def test_device_last_seen():
    device = Device(name="Test", device_type="sensor")
    device.update_last_seen()
    
    assert device.last_seen == datetime(2025, 1, 1, 12, 0, 0)
```

---

## Next Steps

### Implementing TDD

1. **Start Small** - Begin with unit tests for new features
2. **Add Integration Tests** - Test API endpoints
3. **Build E2E Suite** - Cover critical user journeys
4. **Measure Coverage** - Aim for 85%+ coverage
5. **Automate** - Set up CI/CD pipeline
6. **Maintain** - Keep tests updated with code changes

### Resources

- **pytest Documentation**: https://docs.pytest.org/
- **Flask Testing**: https://flask.palletsprojects.com/en/latest/testing/
- **TDD Best Practices**: https://testdriven.io/
- **Python Testing Guide**: https://realpython.com/python-testing/

---

**Document Version:** 1.0  
**Last Updated:** December 8, 2025  
**Connectivity Layer Version:** 0.2
