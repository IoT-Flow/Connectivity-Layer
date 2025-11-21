-- ============================================================================
-- PostgreSQL Telemetry Schema for IoTFlow
-- Replaces Apache IoTDB with PostgreSQL for time-series telemetry storage
-- ============================================================================

-- ============================================================================
-- 1. TELEMETRY DATA TABLE (Main time-series storage)
-- ============================================================================

CREATE TABLE telemetry_data (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Measurement identification
    measurement_name VARCHAR(100) NOT NULL,  -- e.g., 'temperature', 'humidity', 'pressure'
    
    -- Multi-type value storage (only one should be populated per row)
    numeric_value DOUBLE PRECISION,          -- For numeric sensor readings
    text_value TEXT,                         -- For text/string values
    boolean_value BOOLEAN,                   -- For boolean states
    json_value JSONB,                        -- For complex/nested data
    
    -- Additional metadata
    metadata JSONB,                          -- Flexible metadata storage
    quality_flag SMALLINT DEFAULT 0,         -- Data quality indicator (0=good, 1=suspect, 2=bad)
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_value_not_null CHECK (
        numeric_value IS NOT NULL OR 
        text_value IS NOT NULL OR 
        boolean_value IS NOT NULL OR 
        json_value IS NOT NULL
    )
);

-- ============================================================================
-- 2. INDEXES FOR PERFORMANCE
-- ============================================================================

-- Primary query pattern: Get telemetry for device within time range
CREATE INDEX idx_telemetry_device_time ON telemetry_data (device_id, timestamp DESC);

-- Query by user (all devices owned by user)
CREATE INDEX idx_telemetry_user_time ON telemetry_data (user_id, timestamp DESC);

-- Query by measurement type
CREATE INDEX idx_telemetry_measurement ON telemetry_data (measurement_name);

-- Query by device and measurement
CREATE INDEX idx_telemetry_device_measurement_time ON telemetry_data (device_id, measurement_name, timestamp DESC);

-- Latest telemetry queries
CREATE INDEX idx_telemetry_latest ON telemetry_data (device_id, measurement_name, timestamp DESC);

-- JSONB metadata queries (GIN index for JSONB)
CREATE INDEX idx_telemetry_metadata ON telemetry_data USING GIN (metadata);

-- Quality filtering
CREATE INDEX idx_telemetry_quality ON telemetry_data (quality_flag) WHERE quality_flag > 0;

-- ============================================================================
-- 3. TABLE PARTITIONING (Time-based for scalability)
-- ============================================================================

-- Convert to partitioned table (PostgreSQL 10+)
-- This should be done BEFORE inserting data

-- Drop the existing table and recreate as partitioned
-- WARNING: Only do this on a fresh installation or after backing up data

/*
DROP TABLE IF EXISTS telemetry_data CASCADE;

CREATE TABLE telemetry_data (
    id BIGSERIAL,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    measurement_name VARCHAR(100) NOT NULL,
    numeric_value DOUBLE PRECISION,
    text_value TEXT,
    boolean_value BOOLEAN,
    json_value JSONB,
    metadata JSONB,
    quality_flag SMALLINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, timestamp),
    CONSTRAINT chk_value_not_null CHECK (
        numeric_value IS NOT NULL OR 
        text_value IS NOT NULL OR 
        boolean_value IS NOT NULL OR 
        json_value IS NOT NULL
    )
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions (example for 2024-2025)
CREATE TABLE telemetry_data_2024_11 PARTITION OF telemetry_data
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE telemetry_data_2024_12 PARTITION OF telemetry_data
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

CREATE TABLE telemetry_data_2025_01 PARTITION OF telemetry_data
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Add indexes to each partition
CREATE INDEX idx_telemetry_2024_11_device_time ON telemetry_data_2024_11 (device_id, timestamp DESC);
CREATE INDEX idx_telemetry_2024_12_device_time ON telemetry_data_2024_12 (device_id, timestamp DESC);
CREATE INDEX idx_telemetry_2025_01_device_time ON telemetry_data_2025_01 (device_id, timestamp DESC);
*/

-- ============================================================================
-- 4. AGGREGATED TELEMETRY TABLE (Pre-computed aggregations)
-- ============================================================================

CREATE TABLE telemetry_aggregates (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    measurement_name VARCHAR(100) NOT NULL,
    
    -- Time window
    time_bucket TIMESTAMP WITH TIME ZONE NOT NULL,  -- Start of time bucket
    interval_minutes INTEGER NOT NULL,               -- Bucket size (5, 15, 60, etc.)
    
    -- Aggregated values
    count INTEGER NOT NULL,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    avg_value DOUBLE PRECISION,
    sum_value DOUBLE PRECISION,
    stddev_value DOUBLE PRECISION,
    
    -- First and last values in bucket
    first_value DOUBLE PRECISION,
    last_value DOUBLE PRECISION,
    first_timestamp TIMESTAMP WITH TIME ZONE,
    last_timestamp TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate aggregations
    CONSTRAINT uq_telemetry_aggregate UNIQUE (device_id, measurement_name, time_bucket, interval_minutes)
);

-- Indexes for aggregated data
CREATE INDEX idx_telemetry_agg_device_time ON telemetry_aggregates (device_id, time_bucket DESC);
CREATE INDEX idx_telemetry_agg_measurement ON telemetry_aggregates (measurement_name, time_bucket DESC);
CREATE INDEX idx_telemetry_agg_interval ON telemetry_aggregates (interval_minutes, time_bucket DESC);

-- ============================================================================
-- 5. MATERIALIZED VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Latest telemetry per device per measurement
CREATE MATERIALIZED VIEW mv_latest_telemetry AS
SELECT DISTINCT ON (device_id, measurement_name)
    device_id,
    user_id,
    measurement_name,
    timestamp,
    numeric_value,
    text_value,
    boolean_value,
    json_value,
    metadata
FROM telemetry_data
ORDER BY device_id, measurement_name, timestamp DESC;

CREATE UNIQUE INDEX idx_mv_latest_telemetry ON mv_latest_telemetry (device_id, measurement_name);

-- Device activity summary (last 24 hours)
CREATE MATERIALIZED VIEW mv_device_activity_24h AS
SELECT 
    d.id as device_id,
    d.name as device_name,
    d.user_id,
    COUNT(t.id) as telemetry_count,
    COUNT(DISTINCT t.measurement_name) as measurement_types,
    MIN(t.timestamp) as first_reading,
    MAX(t.timestamp) as last_reading
FROM devices d
LEFT JOIN telemetry_data t ON d.id = t.device_id 
    AND t.timestamp > NOW() - INTERVAL '24 hours'
GROUP BY d.id, d.name, d.user_id;

CREATE UNIQUE INDEX idx_mv_device_activity ON mv_device_activity_24h (device_id);

-- ============================================================================
-- 6. FUNCTIONS FOR DATA MANAGEMENT
-- ============================================================================

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_telemetry_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_latest_telemetry;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_device_activity_24h;
END;
$$ LANGUAGE plpgsql;

-- Function to insert telemetry with automatic type detection
CREATE OR REPLACE FUNCTION insert_telemetry(
    p_device_id INTEGER,
    p_user_id INTEGER,
    p_measurement_name VARCHAR,
    p_value ANYELEMENT,
    p_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    p_metadata JSONB DEFAULT NULL
)
RETURNS BIGINT AS $$
DECLARE
    v_telemetry_id BIGINT;
BEGIN
    INSERT INTO telemetry_data (
        device_id, 
        user_id, 
        measurement_name, 
        timestamp,
        numeric_value,
        text_value,
        boolean_value,
        json_value,
        metadata
    ) VALUES (
        p_device_id,
        p_user_id,
        p_measurement_name,
        p_timestamp,
        CASE WHEN pg_typeof(p_value) IN ('double precision'::regtype, 'numeric'::regtype, 'integer'::regtype) 
             THEN p_value::DOUBLE PRECISION ELSE NULL END,
        CASE WHEN pg_typeof(p_value) = 'text'::regtype 
             THEN p_value::TEXT ELSE NULL END,
        CASE WHEN pg_typeof(p_value) = 'boolean'::regtype 
             THEN p_value::BOOLEAN ELSE NULL END,
        CASE WHEN pg_typeof(p_value) = 'jsonb'::regtype 
             THEN p_value::JSONB ELSE NULL END,
        p_metadata
    ) RETURNING id INTO v_telemetry_id;
    
    RETURN v_telemetry_id;
END;
$$ LANGUAGE plpgsql;

-- Function to compute aggregates for a time range
CREATE OR REPLACE FUNCTION compute_telemetry_aggregates(
    p_device_id INTEGER,
    p_measurement_name VARCHAR,
    p_start_time TIMESTAMP WITH TIME ZONE,
    p_end_time TIMESTAMP WITH TIME ZONE,
    p_interval_minutes INTEGER
)
RETURNS TABLE (
    time_bucket TIMESTAMP WITH TIME ZONE,
    count INTEGER,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    avg_value DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        date_trunc('hour', timestamp) + 
            (EXTRACT(MINUTE FROM timestamp)::INTEGER / p_interval_minutes) * 
            (p_interval_minutes || ' minutes')::INTERVAL as bucket,
        COUNT(*)::INTEGER,
        MIN(numeric_value),
        MAX(numeric_value),
        AVG(numeric_value)
    FROM telemetry_data
    WHERE device_id = p_device_id
        AND measurement_name = p_measurement_name
        AND timestamp BETWEEN p_start_time AND p_end_time
        AND numeric_value IS NOT NULL
    GROUP BY bucket
    ORDER BY bucket;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old telemetry data
CREATE OR REPLACE FUNCTION cleanup_old_telemetry(
    p_retention_days INTEGER DEFAULT 90
)
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM telemetry_data
    WHERE timestamp < NOW() - (p_retention_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 7. TRIGGERS FOR AUTOMATIC AGGREGATION
-- ============================================================================

-- Trigger to update device last_seen on telemetry insert
CREATE OR REPLACE FUNCTION update_device_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE devices 
    SET last_seen = NEW.timestamp
    WHERE id = NEW.device_id 
        AND (last_seen IS NULL OR last_seen < NEW.timestamp);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_telemetry_update_last_seen
    AFTER INSERT ON telemetry_data
    FOR EACH ROW
    EXECUTE FUNCTION update_device_last_seen();

-- ============================================================================
-- 8. SCHEDULED JOBS (requires pg_cron extension)
-- ============================================================================

-- Install pg_cron extension (run as superuser)
-- CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule materialized view refresh every 5 minutes
-- SELECT cron.schedule('refresh-telemetry-views', '*/5 * * * *', 'SELECT refresh_telemetry_views()');

-- Schedule old data cleanup daily at 2 AM
-- SELECT cron.schedule('cleanup-old-telemetry', '0 2 * * *', 'SELECT cleanup_old_telemetry(90)');

-- ============================================================================
-- 9. PERFORMANCE TUNING SETTINGS
-- ============================================================================

-- Recommended PostgreSQL configuration for time-series workload
-- Add to postgresql.conf:

/*
# Memory settings
shared_buffers = 4GB                    # 25% of RAM
effective_cache_size = 12GB             # 75% of RAM
work_mem = 64MB                         # For sorting/aggregation
maintenance_work_mem = 1GB              # For VACUUM, CREATE INDEX

# Write performance
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB
min_wal_size = 1GB

# Query performance
random_page_cost = 1.1                  # For SSD storage
effective_io_concurrency = 200          # For SSD storage
default_statistics_target = 100

# Parallel query
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_worker_processes = 8

# Connection pooling
max_connections = 200
*/

-- ============================================================================
-- 10. EXAMPLE QUERIES
-- ============================================================================

-- Get latest telemetry for a device
/*
SELECT 
    measurement_name,
    timestamp,
    COALESCE(
        numeric_value::TEXT,
        text_value,
        boolean_value::TEXT,
        json_value::TEXT
    ) as value
FROM mv_latest_telemetry
WHERE device_id = 1;
*/

-- Get telemetry history with time range
/*
SELECT 
    timestamp,
    measurement_name,
    numeric_value
FROM telemetry_data
WHERE device_id = 1
    AND timestamp > NOW() - INTERVAL '24 hours'
    AND measurement_name = 'temperature'
ORDER BY timestamp DESC
LIMIT 1000;
*/

-- Get aggregated data (hourly averages)
/*
SELECT * FROM compute_telemetry_aggregates(
    1,                              -- device_id
    'temperature',                  -- measurement_name
    NOW() - INTERVAL '7 days',     -- start_time
    NOW(),                          -- end_time
    60                              -- interval_minutes (1 hour)
);
*/

-- Get all measurements for multiple devices
/*
SELECT 
    d.name as device_name,
    t.measurement_name,
    t.timestamp,
    t.numeric_value
FROM telemetry_data t
JOIN devices d ON t.device_id = d.id
WHERE t.user_id = 1
    AND t.timestamp > NOW() - INTERVAL '1 hour'
ORDER BY t.timestamp DESC;
*/

-- ============================================================================
-- 11. GRANTS AND PERMISSIONS
-- ============================================================================

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON telemetry_data TO iotflow_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON telemetry_aggregates TO iotflow_user;
GRANT SELECT ON mv_latest_telemetry TO iotflow_user;
GRANT SELECT ON mv_device_activity_24h TO iotflow_user;
GRANT USAGE, SELECT ON SEQUENCE telemetry_data_id_seq TO iotflow_user;
GRANT USAGE, SELECT ON SEQUENCE telemetry_aggregates_id_seq TO iotflow_user;
GRANT EXECUTE ON FUNCTION refresh_telemetry_views() TO iotflow_user;
GRANT EXECUTE ON FUNCTION compute_telemetry_aggregates(INTEGER, VARCHAR, TIMESTAMP WITH TIME ZONE, TIMESTAMP WITH TIME ZONE, INTEGER) TO iotflow_user;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
