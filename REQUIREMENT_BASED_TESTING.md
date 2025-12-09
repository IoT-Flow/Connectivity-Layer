# Requirement-Based Testing Guide

## Philosophy

Tests should validate **business requirements** and **expected behavior**, not just mirror the implementation. This ensures tests catch bugs and remain valuable even when implementation changes.

## ❌ Bad: Implementation-Based Tests

```python
# BAD: Test just mirrors what the code does
def test_calculate_total():
    """Test that calculate_total returns price * quantity"""
    result = calculate_total(10, 5)
    assert result == 50  # Just checking it doesn't crash
```

**Problems:**
- Doesn't validate business logic
- If implementation has a bug, test validates the bug
- Doesn't test edge cases
- Changes when implementation changes

## ✅ Good: Requirement-Based Tests

```python
# GOOD: Test validates business requirements
def test_calculate_total_applies_correct_pricing():
    """
    REQUIREMENT: Total cost = unit price × quantity
    BUSINESS RULE: Must handle decimal prices correctly
    """
    # Test standard case
    assert calculate_total(price=10.00, quantity=5) == 50.00
    
    # Test decimal precision (requirement: 2 decimal places)
    assert calculate_total(price=10.99, quantity=3) == 32.97
    
    # Test edge case: zero quantity
    assert calculate_total(price=10.00, quantity=0) == 0.00
    
    # Test edge case: fractional quantity (if allowed)
    assert calculate_total(price=10.00, quantity=0.5) == 5.00
```

**Benefits:**
- Tests actual business requirements
- Catches bugs in implementation
- Tests edge cases
- Survives refactoring

## Real Example from IoTFlow

### ❌ Bad: Testing Implementation

```python
def test_device_authorization():
    """Test that is_device_authorized returns True"""
    service = MQTTAuthService()
    result = service.is_device_authorized(123, "any/topic")
    assert result == True  # Just checking return type
```

### ✅ Good: Testing Requirements

```python
def test_device_authorization_enforces_security():
    """
    REQUIREMENT: Devices can only access their own data
    SECURITY RULE: Device 123 cannot access device 456's topics
    BUSINESS LOGIC: Telemetry and status topics are device-specific
    """
    service = MQTTAuthService()
    device_id = 123
    
    # REQUIREMENT: Device CAN access its own telemetry
    assert service.is_device_authorized(
        device_id, 
        f"iotflow/devices/{device_id}/telemetry"
    ) is True, "Device should access own telemetry"
    
    # REQUIREMENT: Device CAN access its own status
    assert service.is_device_authorized(
        device_id,
        f"iotflow/devices/{device_id}/status"
    ) is True, "Device should access own status"
    
    # SECURITY: Device CANNOT access other device's data
    assert service.is_device_authorized(
        device_id,
        "iotflow/devices/456/telemetry"
    ) is False, "Device must not access other device's data"
    
    # SECURITY: Device CANNOT access admin topics
    assert service.is_device_authorized(
        device_id,
        "iotflow/admin/commands"
    ) is False, "Device must not access admin functions"
    
    # EDGE CASE: Subtopics should follow same rules
    assert service.is_device_authorized(
        device_id,
        f"iotflow/devices/{device_id}/telemetry/sensors"
    ) is True, "Device should access own telemetry subtopics"
```

## How to Write Requirement-Based Tests

### Step 1: Identify Requirements

Before writing tests, document:
1. **Business requirement**: What should the feature do?
2. **Security requirements**: What should it prevent?
3. **Edge cases**: What unusual inputs might occur?
4. **Error handling**: How should errors be handled?

### Step 2: Write Test Cases

For each requirement, write a test that:
1. **States the requirement** in the docstring
2. **Tests the happy path** (normal usage)
3. **Tests edge cases** (boundaries, empty, null)
4. **Tests error cases** (invalid input, unauthorized)
5. **Tests security** (can't bypass restrictions)

### Step 3: Example Template

```python
def test_feature_name():
    """
    REQUIREMENT: [State the business requirement]
    GIVEN: [Initial state/preconditions]
    WHEN: [Action taken]
    THEN: [Expected outcome]
    """
    # Setup
    # ... prepare test data
    
    # Execute
    result = function_under_test(input)
    
    # Assert - verify requirement is met
    assert result == expected, "Requirement: [explain why]"
    
    # Test edge cases
    # Test error cases
    # Test security
```

## IoTFlow Requirements to Test

### 1. Device Authentication

**Requirements:**
- Devices must authenticate with API key
- Invalid API keys must be rejected
- Inactive devices should not authenticate
- Authentication must update last_seen timestamp

**Test Example:**
```python
def test_device_authentication_requirements(self, app, db_session):
    """
    REQUIREMENT: Only devices with valid API keys can authenticate
    SECURITY: Invalid or missing API keys must be rejected
    BUSINESS LOGIC: Authentication updates device last_seen
    """
    # Create test device
    device = Device(name="Test", api_key="valid_key", status="active")
    db_session.add(device)
    db_session.commit()
    
    service = MQTTAuthService(app=app)
    
    # REQUIREMENT: Valid API key authenticates
    result = service.authenticate_device_by_api_key("valid_key")
    assert result is not None, "Valid API key must authenticate"
    assert result.id == device.id, "Must return correct device"
    
    # SECURITY: Invalid API key rejected
    result = service.authenticate_device_by_api_key("invalid_key")
    assert result is None, "Invalid API key must be rejected"
    
    # SECURITY: Empty API key rejected
    result = service.authenticate_device_by_api_key("")
    assert result is None, "Empty API key must be rejected"
    
    # BUSINESS LOGIC: Authentication updates last_seen
    old_last_seen = device.last_seen
    time.sleep(0.1)
    service.authenticate_device_by_api_key("valid_key")
    db_session.refresh(device)
    assert device.last_seen > old_last_seen, "Authentication must update last_seen"
```

### 2. Telemetry Storage

**Requirements:**
- Telemetry must include measurements
- Timestamp is optional (defaults to current time)
- Data must be stored in IoTDB
- Invalid data must be rejected
- Must handle various timestamp formats

**Test Example:**
```python
def test_telemetry_storage_requirements(self, client, test_device):
    """
    REQUIREMENT: Telemetry data must be stored with measurements
    BUSINESS RULE: Timestamp defaults to current time if not provided
    DATA VALIDATION: Measurements must be present
    """
    headers = {"X-API-Key": test_device.api_key}
    
    # REQUIREMENT: Store telemetry with measurements
    payload = {"data": {"temperature": 25.5, "humidity": 60}}
    response = client.post("/api/v1/telemetry", json=payload, headers=headers)
    assert response.status_code in [200, 201], "Valid telemetry must be stored"
    
    # BUSINESS RULE: Timestamp defaults if not provided
    # (verified by successful storage above)
    
    # DATA VALIDATION: Missing measurements rejected
    payload = {"timestamp": "2024-01-01T12:00:00Z"}  # No data
    response = client.post("/api/v1/telemetry", json=payload, headers=headers)
    assert response.status_code == 400, "Missing measurements must be rejected"
    
    # DATA VALIDATION: Empty measurements rejected
    payload = {"data": {}}
    response = client.post("/api/v1/telemetry", json=payload, headers=headers)
    assert response.status_code == 400, "Empty measurements must be rejected"
    
    # SECURITY: Unauthenticated requests rejected
    response = client.post("/api/v1/telemetry", json={"data": {"temp": 25}})
    assert response.status_code == 401, "Unauthenticated requests must be rejected"
```

### 3. Timestamp Parsing

**Requirements:**
- Support ISO 8601 format
- Support epoch timestamps (seconds and milliseconds)
- Support various date formats
- Handle timezone correctly
- Return None for invalid timestamps

**Test Example:**
```python
def test_timestamp_parsing_requirements(self):
    """
    REQUIREMENT: Parse timestamps from various IoT device formats
    BUSINESS RULE: All timestamps converted to UTC
    ERROR HANDLING: Invalid timestamps return None
    """
    # REQUIREMENT: Parse ISO 8601
    result = parse_device_timestamp("2024-01-15T10:30:45Z")
    assert result is not None, "Must parse ISO 8601"
    assert result.year == 2024, "Must extract correct year"
    assert result.tzinfo == timezone.utc, "Must be in UTC"
    
    # REQUIREMENT: Parse epoch seconds
    epoch = 1705318245  # 2024-01-15 10:30:45 UTC
    result = parse_device_timestamp(epoch)
    assert result is not None, "Must parse epoch seconds"
    assert result.year == 2024, "Must convert epoch correctly"
    
    # REQUIREMENT: Parse epoch milliseconds
    epoch_ms = 1705318245000
    result = parse_device_timestamp(epoch_ms)
    assert result is not None, "Must parse epoch milliseconds"
    assert result.year == 2024, "Must handle milliseconds"
    
    # ERROR HANDLING: Invalid timestamp returns None
    result = parse_device_timestamp("invalid")
    assert result is None, "Invalid timestamp must return None"
    
    # ERROR HANDLING: None input returns None
    result = parse_device_timestamp(None)
    assert result is None, "None input must return None"
    
    # EDGE CASE: Empty string returns None
    result = parse_device_timestamp("")
    assert result is None, "Empty string must return None"
```

## Checklist for Good Tests

- [ ] Test states the requirement in docstring
- [ ] Test validates business logic, not implementation
- [ ] Test includes happy path
- [ ] Test includes edge cases
- [ ] Test includes error cases
- [ ] Test includes security checks
- [ ] Test would catch bugs in implementation
- [ ] Test would survive refactoring
- [ ] Test has clear assertion messages
- [ ] Test is independent (no shared state)

## Converting Existing Tests

### Before (Implementation-Based)
```python
def test_set_device_status(self):
    cache = DeviceStatusCache(redis_client)
    result = cache.set_device_status(123, "online")
    assert result is True
```

### After (Requirement-Based)
```python
def test_device_status_caching_requirements(self):
    """
    REQUIREMENT: Device status must be cached for fast access
    BUSINESS RULE: Status changes must be retrievable
    PERFORMANCE: Cache must reduce database queries
    """
    cache = DeviceStatusCache(redis_client)
    device_id = 123
    
    # REQUIREMENT: Can set device status
    result = cache.set_device_status(device_id, "online")
    assert result is True, "Must successfully cache status"
    
    # REQUIREMENT: Can retrieve cached status
    status = cache.get_device_status(device_id)
    assert status == "online", "Must retrieve correct cached status"
    
    # BUSINESS RULE: Status changes are reflected
    cache.set_device_status(device_id, "offline")
    status = cache.get_device_status(device_id)
    assert status == "offline", "Status changes must be reflected"
    
    # ERROR HANDLING: Graceful failure without Redis
    cache_no_redis = DeviceStatusCache(None)
    result = cache_no_redis.set_device_status(device_id, "online")
    assert result is False, "Must handle missing Redis gracefully"
```

## Summary

**Key Principles:**
1. **Test requirements, not implementation**
2. **State the requirement in the test**
3. **Test happy path, edge cases, and errors**
4. **Tests should catch bugs, not validate them**
5. **Tests should survive refactoring**

**Remember:**
- If you change implementation and tests break, that's good (tests caught a change)
- If you change implementation and tests still pass, that's better (tests validate behavior)
- If you have a bug and tests pass, your tests are wrong (they're testing implementation, not requirements)
