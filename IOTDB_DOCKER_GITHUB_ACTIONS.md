# IoTDB Docker Setup for GitHub Actions

This guide explains how to set up Apache IoTDB in Docker containers for GitHub Actions to enable real integration testing instead of mocking.

## Overview

Currently, our CI pipeline disables IoTDB (`IOTDB_ENABLED=false`) and uses mocks for testing. This document provides steps to run actual IoTDB instances in GitHub Actions using Docker services.

## Current State

```yaml
# Current CI setup (mocked)
env:
  IOTDB_ENABLED: false  # IoTDB is disabled
  # Tests use mocks instead of real IoTDB
```

## Target State

```yaml
# Target CI setup (real IoTDB)
services:
  iotdb:
    image: apache/iotdb:1.2.2-standalone
    ports:
      - 6667:6667
env:
  IOTDB_ENABLED: true
  IOTDB_HOST: localhost
  IOTDB_PORT: 6667
```

## Implementation Options

### Option 1: Official Apache IoTDB Docker Image

#### 1.1 Basic Setup

```yaml
name: Connectivity Layer CI with IoTDB

on:
  push:
    branches: [ master, main, develop ]
  pull_request:
    branches: [ master, main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      mosquitto:
        image: eclipse-mosquitto:2.0
        ports:
          - 1883:1883
        options: >-
          --health-cmd "mosquitto_pub -h localhost -t test -m test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      iotdb:
        image: apache/iotdb:1.2.2-standalone
        ports:
          - 6667:6667
        env:
          # IoTDB configuration
          IOTDB_JMX_PORT: 31999
          IOTDB_ENABLE_AUDIT_LOG: false
        options: >-
          --health-cmd "nc -z localhost 6667"
          --health-interval 30s
          --health-timeout 10s
          --health-retries 5
          --health-start-period 60s

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    # ... other setup steps ...
    
    - name: Wait for IoTDB to be ready
      run: |
        echo "Waiting for IoTDB to be ready..."
        timeout 120 bash -c 'until nc -z localhost 6667; do sleep 2; done'
        echo "IoTDB is ready!"
    
    - name: Test IoTDB connection
      run: |
        # Test basic connectivity
        python -c "
        from iotdb.Session import Session
        session = Session('localhost', 6667, 'root', 'root')
        session.open(False)
        print('IoTDB connection successful')
        session.close()
        "
    
    - name: Run tests with real IoTDB
      env:
        FLASK_ENV: testing
        TESTING: true
        CI: true
        # Use real IoTDB
        IOTDB_ENABLED: true
        IOTDB_HOST: localhost
        IOTDB_PORT: 6667
        IOTDB_USERNAME: root
        IOTDB_PASSWORD: root
        # Other services
        REDIS_HOST: localhost
        REDIS_PORT: 6379
        MQTT_BROKER: localhost
        MQTT_PORT: 1883
      run: |
        poetry run pytest tests/ --cov=src --cov-report=term-missing -v
```

#### 1.2 IoTDB Configuration Options

```yaml
iotdb:
  image: apache/iotdb:1.2.2-standalone
  ports:
    - 6667:6667
  env:
    # Memory settings for CI
    IOTDB_HEAP_OPTS: "-Xmx512m -Xms512m"
    # Disable unnecessary features for testing
    IOTDB_JMX_PORT: 31999
    IOTDB_ENABLE_AUDIT_LOG: false
    IOTDB_ENABLE_PERFORMANCE_STAT: false
    # Faster startup for CI
    IOTDB_WAL_BUFFER_SIZE: 16777216
  volumes:
    - /tmp/iotdb-data:/iotdb/data
  options: >-
    --health-cmd "nc -z localhost 6667 || exit 1"
    --health-interval 15s
    --health-timeout 10s
    --health-retries 8
    --health-start-period 90s
```

### Option 2: Custom IoTDB Docker Image for CI

#### 2.1 Create Custom Dockerfile

```dockerfile
# Dockerfile.iotdb-ci
FROM apache/iotdb:1.2.2-standalone

# Optimize for CI environment
ENV IOTDB_HEAP_OPTS="-Xmx256m -Xms256m"
ENV IOTDB_ENABLE_AUDIT_LOG=false
ENV IOTDB_ENABLE_PERFORMANCE_STAT=false

# Copy optimized configuration
COPY iotdb-ci.properties /iotdb/conf/iotdb-engine.properties

# Expose port
EXPOSE 6667

# Health check
HEALTHCHECK --interval=15s --timeout=10s --retries=8 --start-period=60s \
  CMD nc -z localhost 6667 || exit 1
```

#### 2.2 CI Configuration File

```properties
# iotdb-ci.properties - Optimized for CI
####################
# Memory Configuration
####################
storage_group_size_threshold=134217728
memtable_size_threshold=134217728
avg_series_point_number_threshold=10000

####################
# Performance Configuration
####################
enable_performance_stat=false
enable_audit_log=false
wal_buffer_size=16777216

####################
# Concurrent Configuration
####################
concurrent_writing_time_partition=1
max_concurrent_client_num=65535
rpc_thrift_compression_enable=false

####################
# Storage Configuration
####################
timestamp_precision=ms
default_ttl=2147483647
max_degree_of_index_node=256
```

#### 2.3 GitHub Actions with Custom Image

```yaml
services:
  iotdb:
    image: ghcr.io/your-org/iotdb-ci:latest
    ports:
      - 6667:6667
    options: >-
      --health-cmd "nc -z localhost 6667"
      --health-interval 15s
      --health-timeout 10s
      --health-retries 8
      --health-start-period 60s
```

### Option 3: Matrix Testing with Multiple IoTDB Versions

```yaml
strategy:
  matrix:
    python-version: ['3.11']
    iotdb-version: ['1.2.2', '1.3.0']
    
services:
  iotdb:
    image: apache/iotdb:${{ matrix.iotdb-version }}-standalone
    ports:
      - 6667:6667
```

## Implementation Steps

### Step 1: Update CI Configuration

1. **Add IoTDB service to `.github/workflows/ci.yml`**:

```yaml
services:
  # ... existing services ...
  
  iotdb:
    image: apache/iotdb:1.2.2-standalone
    ports:
      - 6667:6667
    env:
      IOTDB_HEAP_OPTS: "-Xmx512m -Xms512m"
    options: >-
      --health-cmd "nc -z localhost 6667"
      --health-interval 30s
      --health-timeout 10s
      --health-retries 5
      --health-start-period 90s
```

2. **Update environment variables**:

```yaml
env:
  # Enable IoTDB for real testing
  IOTDB_ENABLED: true
  IOTDB_HOST: localhost
  IOTDB_PORT: 6667
  IOTDB_USERNAME: root
  IOTDB_PASSWORD: root
```

### Step 2: Add IoTDB Readiness Check

```yaml
- name: Wait for services to be ready
  run: |
    echo "Waiting for Redis..."
    timeout 30 bash -c 'until redis-cli -h localhost -p 6379 ping; do sleep 1; done'
    
    echo "Waiting for MQTT..."
    timeout 30 bash -c 'until nc -z localhost 1883; do sleep 1; done'
    
    echo "Waiting for IoTDB..."
    timeout 120 bash -c 'until nc -z localhost 6667; do sleep 2; done'
    
    echo "All services are ready!"
```

### Step 3: Test IoTDB Connection

```yaml
- name: Verify IoTDB connection
  run: |
    poetry run python -c "
    from iotdb.Session import Session
    import sys
    try:
        session = Session('localhost', 6667, 'root', 'root')
        session.open(False)
        print('✓ IoTDB connection successful')
        session.close()
    except Exception as e:
        print(f'✗ IoTDB connection failed: {e}')
        sys.exit(1)
    "
```

### Step 4: Update Test Configuration

Remove IoTDB mocking and enable real testing:

```python
# tests/conftest.py - Remove or modify IoTDB mocking
@pytest.fixture
def real_iotdb_service():
    """Use real IoTDB service in CI"""
    if os.environ.get("CI") == "true":
        # Use real IoTDB service
        from src.services.iotdb import IoTDBService
        return IoTDBService()
    else:
        # Use mock for local development
        return MockIoTDBService()
```

## Performance Considerations

### Memory Optimization

```yaml
iotdb:
  image: apache/iotdb:1.2.2-standalone
  env:
    # Reduce memory usage for CI
    IOTDB_HEAP_OPTS: "-Xmx256m -Xms256m"
    # Disable heavy features
    IOTDB_ENABLE_PERFORMANCE_STAT: false
    IOTDB_ENABLE_AUDIT_LOG: false
```

### Startup Time Optimization

```yaml
options: >-
  --health-start-period 60s  # Allow more time for startup
  --health-interval 15s      # Check more frequently
  --health-retries 8         # More retries for reliability
```

### Parallel Testing

```yaml
strategy:
  matrix:
    test-group: [unit, integration, e2e]
  
# Run different test groups in parallel
- name: Run ${{ matrix.test-group }} tests
  run: poetry run pytest tests/${{ matrix.test-group }}/ -v
```

## Troubleshooting

### Common Issues

1. **IoTDB startup timeout**:
   ```yaml
   # Increase startup time
   --health-start-period 120s
   ```

2. **Memory issues**:
   ```yaml
   env:
     IOTDB_HEAP_OPTS: "-Xmx256m -Xms256m"
   ```

3. **Connection refused**:
   ```bash
   # Add connection retry logic
   timeout 180 bash -c 'until nc -z localhost 6667; do sleep 3; done'
   ```

### Debug Steps

```yaml
- name: Debug IoTDB
  if: failure()
  run: |
    echo "Checking IoTDB container logs..."
    docker logs $(docker ps -q --filter "ancestor=apache/iotdb:1.2.2-standalone")
    
    echo "Checking port availability..."
    netstat -tlnp | grep 6667
    
    echo "Testing direct connection..."
    nc -zv localhost 6667
```

## Migration Strategy

### Phase 1: Parallel Testing
- Keep existing mocked tests
- Add new real IoTDB tests
- Compare results

### Phase 2: Gradual Migration
- Migrate test by test
- Ensure compatibility
- Monitor CI performance

### Phase 3: Full Migration
- Remove mocks
- Use only real IoTDB
- Optimize performance

## Benefits of Real IoTDB Testing

1. **Authentic Integration Testing**: Tests actual IoTDB behavior
2. **Version Compatibility**: Catch IoTDB version-specific issues
3. **Performance Testing**: Real performance characteristics
4. **Data Integrity**: Test actual data storage and retrieval
5. **Schema Evolution**: Test time series schema changes

## Considerations

### Pros
- ✅ Real integration testing
- ✅ Catches IoTDB-specific issues
- ✅ Tests actual performance
- ✅ Validates data integrity

### Cons
- ❌ Slower CI execution
- ❌ More resource usage
- ❌ Potential flakiness
- ❌ Complex debugging

## Recommended Approach

1. **Start with Option 1** (official image) for simplicity
2. **Monitor CI performance** and adjust timeouts
3. **Consider Option 2** (custom image) if startup time is an issue
4. **Implement gradual migration** to minimize risk
5. **Keep fallback to mocks** for local development

This setup will provide comprehensive testing with real IoTDB while maintaining CI reliability and performance.