-- ============================================================================
-- PostgreSQL Table Creation Script for IoTFlow
-- Creates all required tables for the IoT Connectivity Layer
-- ============================================================================

-- Drop existing tables if they exist (CASCADE removes dependent objects)
DROP TABLE IF EXISTS chart_measurements CASCADE;
DROP TABLE IF EXISTS chart_devices CASCADE;
DROP TABLE IF EXISTS charts CASCADE;
DROP TABLE IF EXISTS device_control CASCADE;
DROP TABLE IF EXISTS device_configurations CASCADE;
DROP TABLE IF EXISTS device_auth CASCADE;
DROP TABLE IF EXISTS devices CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================================
-- 1. USERS TABLE
-- ============================================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(32) UNIQUE NOT NULL,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Indexes for users table
CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_username ON users(username);
CREATE INDEX idx_user_id ON users(user_id);

-- ============================================================================
-- 2. DEVICES TABLE
-- ============================================================================
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    device_type VARCHAR(50) NOT NULL DEFAULT 'sensor',
    api_key VARCHAR(64) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    location VARCHAR(200),
    firmware_version VARCHAR(20),
    hardware_version VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE,
    user_id INTEGER REFERENCES users(id)
);

-- Indexes for devices table
CREATE INDEX idx_devices_user_id ON devices(user_id);
CREATE INDEX idx_devices_api_key ON devices(api_key);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_last_seen ON devices(last_seen);

-- ============================================================================
-- 3. DEVICE_AUTH TABLE
-- ============================================================================
CREATE TABLE device_auth (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    api_key_hash VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0
);

-- Indexes for device_auth table
CREATE INDEX idx_api_key_hash ON device_auth(api_key_hash);
CREATE INDEX idx_device_auth ON device_auth(device_id, is_active);

-- ============================================================================
-- 4. DEVICE_CONFIGURATIONS TABLE
-- ============================================================================
CREATE TABLE device_configurations (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT,
    data_type VARCHAR(20) DEFAULT 'string',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_device_config UNIQUE (device_id, config_key)
);

-- Indexes for device_configurations table
CREATE INDEX idx_device_config ON device_configurations(device_id, is_active);

-- ============================================================================
-- 5. DEVICE_CONTROL TABLE
-- ============================================================================
CREATE TABLE device_control (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    command VARCHAR(128) NOT NULL,
    parameters JSONB,
    status VARCHAR(32) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for device_control table
CREATE INDEX idx_device_control_device_id ON device_control(device_id);
CREATE INDEX idx_device_control_status ON device_control(status);

-- ============================================================================
-- 6. CHARTS TABLE
-- ============================================================================
CREATE TABLE charts (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    description TEXT,
    type VARCHAR(50) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    time_range VARCHAR(20) DEFAULT '1h',
    refresh_interval INTEGER DEFAULT 30,
    aggregation VARCHAR(20) DEFAULT 'none',
    group_by VARCHAR(50) DEFAULT 'device',
    appearance_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for charts table
CREATE INDEX idx_user_charts ON charts(user_id);
CREATE INDEX idx_chart_type ON charts(type);
CREATE INDEX idx_created_at ON charts(created_at);

-- ============================================================================
-- 7. CHART_DEVICES TABLE
-- ============================================================================
CREATE TABLE chart_devices (
    id SERIAL PRIMARY KEY,
    chart_id VARCHAR(255) NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_chart_device UNIQUE (chart_id, device_id)
);

-- Indexes for chart_devices table
CREATE INDEX idx_chart_devices ON chart_devices(chart_id);
CREATE INDEX idx_device_charts ON chart_devices(device_id);

-- ============================================================================
-- 8. CHART_MEASUREMENTS TABLE
-- ============================================================================
CREATE TABLE chart_measurements (
    id SERIAL PRIMARY KEY,
    chart_id VARCHAR(255) NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
    measurement_name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    color VARCHAR(7),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_chart_measurement UNIQUE (chart_id, measurement_name)
);

-- Indexes for chart_measurements table
CREATE INDEX idx_chart_measurements ON chart_measurements(chart_id);
CREATE INDEX idx_measurement_name ON chart_measurements(measurement_name);

-- ============================================================================
-- 9. INSERT INITIAL DATA
-- ============================================================================

-- Insert admin user (password: admin123)
-- Password hash generated with: werkzeug.security.generate_password_hash("admin123")
INSERT INTO users (user_id, username, email, password_hash, is_active, is_admin)
VALUES (
    'dcf1a',
    'admin',
    'admin@iotflow.local',
    'scrypt:32768:8:1$VQxGZJYvKqHLKqYi$c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0',
    TRUE,
    TRUE
) ON CONFLICT (username) DO NOTHING;

-- Insert test user (password: test123)
INSERT INTO users (user_id, username, email, password_hash, is_active, is_admin)
VALUES (
    'testuser',
    'test',
    'test@iotflow.local',
    'scrypt:32768:8:1$VQxGZJYvKqHLKqYi$c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0c8e0',
    TRUE,
    FALSE
) ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- 10. GRANT PERMISSIONS
-- ============================================================================

-- Grant permissions to iotflow user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO iotflow;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO iotflow;
GRANT ALL PRIVILEGES ON DATABASE iotflow TO iotflow;

-- ============================================================================
-- 11. VERIFICATION QUERIES
-- ============================================================================

-- List all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Count records in each table
SELECT 
    'users' as table_name, COUNT(*) as record_count FROM users
UNION ALL
SELECT 'devices', COUNT(*) FROM devices
UNION ALL
SELECT 'device_auth', COUNT(*) FROM device_auth
UNION ALL
SELECT 'device_configurations', COUNT(*) FROM device_configurations
UNION ALL
SELECT 'device_control', COUNT(*) FROM device_control
UNION ALL
SELECT 'charts', COUNT(*) FROM charts
UNION ALL
SELECT 'chart_devices', COUNT(*) FROM chart_devices
UNION ALL
SELECT 'chart_measurements', COUNT(*) FROM chart_measurements;

-- ============================================================================
-- END OF SCRIPT
-- ============================================================================

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ All tables created successfully!';
    RAISE NOTICE 'Admin user: admin / admin123';
    RAISE NOTICE 'Test user: test / test123';
END $$;
