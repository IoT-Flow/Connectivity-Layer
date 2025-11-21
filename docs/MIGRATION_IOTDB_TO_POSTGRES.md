# IoTDB to PostgreSQL Migration Guide

## Overview

This guide documents the Test-Driven Development (TDD) approach to migrating from Apache IoTDB to PostgreSQL for telemetry storage in the IoT Connectivity Layer.

## Why Migrate?

1. **Unified Database**: Single database for both metadata and telemetry
2. **Simplified Operations**: No need to manage separate IoTDB instance
3. **Better Tooling**: Rich PostgreSQL ecosystem
4. **ACID Compliance**: Strong consistency guarantees
5. **Flexible Queries**: Full SQL support with CTEs, window functions
6. **Native JSON Support**: JSONB for flexible telemetry formats

## Migration Phases

### Phase 1: Preparation ✅

**Goal**: Create PostgreSQL schema and verify it works

**Steps**:
1. Create telemetry_data table with proper schema
2. Add indexes for performance
3. Create test suite
4. Run migration preparation script

**Commands**:
```bash
# Run migration preparation
python migrate_iotdb_to_postgres.py

# Run tests
pytest tests/test_postgres_telemetry_service.py -v
```

**Files Created**:
- `src/services/postgres_telemetry.py` - PostgreSQL telemetry service
- `src/routes/telemetry_postgres.py` - Updated API routes
- `tests/test_postgres_telemetry_service.py` - Test suite
- `migrate_iotdb_to_postgres.py` - Migration script

### Phase 2: Dual Write (Current Phase)

**Goal**: Write to both IoTDB and PostgreSQL, validate consistency

**Implementation Options**:

#### Option A: Gradual Migration (Recommended)
Keep IoTDB routes active, add PostgreSQL routes alongside:

```python
# In app.py
from src.routes.telemetry import telemetry_bp as telemetry_iotdb_bp
from src.routes.telemetry_postgres import telemetry_bp as telemetry_postgres_bp

# Register both blueprints
app.register_blueprint(telemetry_iotdb_bp)  # /api/v1/telemetry (IoTDB)
app.register_blueprint(telemetry_postgres_bp, url_prefix="/api/v1/telemetry-pg")  # New endpoint
```

Test PostgreSQL endpoint separately before switching.

#### Option B: Dual Write in Same Endpoint
Modify existing telemetry routes to write to both:

```python
# In src/routes/telemetry.py
from src.services.iotdb import IoTDBService
from src.services.postgres_telemetry import PostgresTelemetryService

iotdb_service = IoTDBService()
postgres_service = PostgresTelemetryService()

# In store_telemetry():
iotdb_success = iotdb_service.write_telemetry_data(...)
postgres_success = postgres_service.write_telemetry_data(...)

# Log any discrepancies
if iotdb_success != postgres_success:
    logger.warning(f"Write mismatch: IoTDB={iotdb_success}, Postgres={postgres_success}")
```

**Validation**:
```bash
# Send test telemetry
curl -X POST http://localhost:5000/api/v1/telemetry \
  -H "X-API-Key: YOUR_DEVICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "temperature": 22.5,
      "humidity": 65.0
    },
    "metadata": {
      "test": "dual_write"
    }
  }'

# Verify in PostgreSQL
psql -U iotflow -d iotflow -c "SELECT * FROM telemetry_data ORDER BY created_at DESC LIMIT 5;"
```

### Phase 3: Switch Reads to PostgreSQL

**Goal**: Read from PostgreSQL while still writing to both

**Steps**:
1. Update all GET endpoints to use PostgreSQL service
2. Monitor query performance
3. Validate data accuracy

**Code Changes**:
```python
# Replace in telemetry routes
# OLD:
telemetry_data = iotdb_service.get_device_telemetry(...)

# NEW:
telemetry_data = postgres_service.get_device_telemetry(...)
```

**Performance Monitoring**:
```sql
-- Check query performance
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
WHERE query LIKE '%telemetry_data%'
ORDER BY mean_time DESC
LIMIT 10;
```

### Phase 4: Stop IoTDB Writes

**Goal**: Write only to PostgreSQL

**Steps**:
1. Remove IoTDB write calls
2. Update response to indicate PostgreSQL storage
3. Monitor for errors

**Code Changes**:
```python
# In app.py - Replace blueprint
from src.routes.telemetry_postgres import telemetry_bp
app.register_blueprint(telemetry_bp)
```

### Phase 5: Decommission IoTDB

**Goal**: Remove IoTDB completely

**Steps**:
1. Backup any historical IoTDB data if needed
2. Remove IoTDB dependencies
3. Remove IoTDB configuration
4. Clean up code

**Cleanup**:
```bash
# Remove from requirements.txt
# apache-iotdb>=1.3.0,<2.0.0

# Remove from .env
# IOTDB_HOST=localhost
# IOTDB_PORT=6667
# IOTDB_USERNAME=root
# IOTDB_PASSWORD=root
# IOTDB_DATABASE=root.iotflow

# Remove files
rm src/config/iotdb_config.py
rm src/services/iotdb.py
rm src/routes/telemetry.py  # If using new file
```

## Testing Strategy (TDD)

### Unit Tests
```bash
# Run all telemetry tests
pytest tests/test_postgres_telemetry_service.py -v

# Run specific test
pytest tests/test_postgres_telemetry_service.py::TestPostgresTelemetryService::test_write_numeric_telemetry -v
```

### Integration Tests
```bash
# Test full API flow
pytest tests/test_telemetry_api.py -v
```

### Load Testing
```bash
# Use locust for load testing
locust -f tests/load_test_telemetry.py --host=http://localhost:5000
```

## Database Schema

### Telemetry Data Table
```sql
CREATE TABLE telemetry_data (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    measurement_name VARCHAR(100) NOT NULL,
    numeric_value DOUBLE PRECISION,
    text_value TEXT,
    boolean_value BOOLEAN,
    json_value JSONB,
    metadata JSONB,
    quality_flag SMALLINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### Key Indexes
```sql
-- Primary query pattern: device + time range
CREATE INDEX idx_telemetry_device_time ON telemetry_data (device_id, timestamp DESC);

-- User queries
CREATE INDEX idx_telemetry_user_time ON telemetry_data (user_id, timestamp DESC);

-- Measurement queries
CREATE INDEX idx_telemetry_device_measurement_time 
ON telemetry_data (device_id, measurement_name, timestamp DESC);
```

## Performance Considerations

### Query Optimization
1. Use time-based partitioning for large datasets
2. Implement materialized views for common aggregations
3. Use connection pooling
4. Enable query result caching in Redis

### Write Optimization
1. Batch inserts when possible
2. Use async processing for high-volume writes
3. Configure appropriate PostgreSQL settings

### Recommended PostgreSQL Settings
```ini
# postgresql.conf
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 64MB
maintenance_work_mem = 1GB
max_connections = 200
```

## Monitoring

### Key Metrics to Track
1. Write latency (IoTDB vs PostgreSQL)
2. Query response times
3. Database size growth
4. Index usage
5. Connection pool utilization

### Grafana Dashboards
- Telemetry write rate
- Query performance
- Database size
- Error rates

## Rollback Plan

If issues arise, you can rollback to IoTDB:

1. **Phase 2**: Simply stop using PostgreSQL endpoint
2. **Phase 3**: Switch reads back to IoTDB
3. **Phase 4**: Re-enable IoTDB writes

Keep IoTDB running until Phase 5 is complete and stable.

## Troubleshooting

### Common Issues

**Issue**: Slow writes to PostgreSQL
**Solution**: 
- Check index overhead
- Use batch inserts
- Verify PostgreSQL configuration

**Issue**: Query timeouts
**Solution**:
- Add missing indexes
- Implement query result caching
- Use materialized views for aggregations

**Issue**: Data type mismatches
**Solution**:
- Review telemetry data types
- Update schema if needed
- Use JSONB for complex types

## Success Criteria

- [ ] All tests passing
- [ ] Write latency < 50ms (p95)
- [ ] Query latency < 100ms (p95)
- [ ] Zero data loss
- [ ] No increase in error rates
- [ ] Successful 24-hour production run

## Timeline

- **Week 1**: Phase 1 - Preparation (Complete)
- **Week 2**: Phase 2 - Dual Write & Validation
- **Week 3**: Phase 3 - Switch Reads
- **Week 4**: Phase 4 - Stop IoTDB Writes
- **Week 5**: Phase 5 - Decommission IoTDB

## Resources

- [PostgreSQL Time-Series Best Practices](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [TimescaleDB Extension](https://docs.timescale.com/) (Optional for advanced time-series features)
- [Architecture Documentation](./postgres-telemetry-architecture.md)
- [Schema Documentation](./postgres-telemetry-schema.sql)

## Support

For questions or issues during migration:
1. Check test output: `pytest tests/test_postgres_telemetry_service.py -v`
2. Review logs: `tail -f logs/iot_connectivity.log`
3. Check database: `psql -U iotflow -d iotflow`
