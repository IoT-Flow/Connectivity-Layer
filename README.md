# IoTFlow - IoT Device Connectivity Layer

A modern, production-ready IoT platform built with Python Flask for comprehensive device connectivity, telemetry data collection, and real-time analytics. Clean architecture with PostgreSQL storage and comprehensive REST API.

![IoT Platform](https://img.shields.io/badge/Platform-IoT-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey)

## 🚀 Features

### Core Capabilities
- **🔌 Device Management**: Complete device lifecycle with secure API key authentication
- **💾 PostgreSQL Storage**: Unified PostgreSQL database for devices, users, and telemetry data
- **📡 REST API**: Comprehensive HTTP REST API with Swagger documentation
- **⚡ Real-time Analytics**: Time-series queries, aggregations, and data visualization
- **🛡️ Enterprise Security**: API key authentication, JWT tokens, rate limiting, and secure endpoints
- **📈 Scalable Architecture**: Containerized services with Docker Compose
- **🧪 Comprehensive Testing**: Full test suite for all API endpoints

### Production Features
- **🔍 Time-Series Analytics**: PostgreSQL-based telemetry queries with filtering and aggregation
- **📋 User Management**: Multi-user support with device ownership and access control
- **📊 Chart Configuration**: Customizable charts with device and measurement associations
- **📚 Modern Development**: Poetry dependency management and development workflow
- **🐳 Containerized Deployment**: Docker Compose for PostgreSQL and application services
- **📊 Comprehensive Monitoring**: Structured logging, health checks, and system metrics

## 🏗️ Architecture

```
    IoT Devices (HTTP)
           ↓
    ┌─────────────────────────┐
    │   Load Balancer/Proxy   │
    └─────────────┬───────────┘
                  ↓
    ┌─────────────────────────┐
    │    Flask Application    │
    │      (REST API)         │
    └─────────────┬───────────┘
                  ↓
    ┌─────────────────────────┐
    │      PostgreSQL         │
    │  (Users, Devices,       │
    │   Telemetry, Charts)    │
    └─────────────────────────┘
```

## � PostgreSQL Migration

### Overview

This project supports both SQLite (development) and PostgreSQL (production) databases. PostgreSQL provides better performance, concurrency, and reliability for production deployments.

### Migration Steps

#### 1. PostgreSQL Setup

**Using Docker Compose (Recommended):**
```bash
# PostgreSQL is already configured in docker-compose.yml
docker compose up -d
```

**Manual PostgreSQL Installation:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE iotflow;
CREATE USER iotflow_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE iotflow TO iotflow_user;
\q
```

#### 2. Environment Configuration

Update your `.env` file with PostgreSQL connection:

```bash
# Replace SQLite DATABASE_URL with PostgreSQL
DATABASE_URL=postgresql://iotflow_user:your_secure_password@localhost:5432/iotflow

# For Docker Compose setup (already configured)
DATABASE_URL=postgresql://iotflow_user:iotflow_password@postgres:5432/iotflow
```

#### 3. Database Migration

```bash
# Initialize PostgreSQL database (drops all existing tables)
poetry run python init_db.py
```

#### 4. Data Migration (Optional)

If you have existing SQLite data to migrate:

```bash
# Export data from SQLite
poetry run python scripts/export_sqlite_data.py --output backup.json

# Import to PostgreSQL (after updating DATABASE_URL)
poetry run python scripts/import_data.py --input backup.json
```

#### 5. Verification

```bash
# Test database connection
poetry run python -c "from src.config.config import db; print('PostgreSQL connected:', db.engine.url)"

# Run health check
curl http://localhost:5000/health

# Verify Redis-database sync
tail -f logs/iotflow.log | grep "Database sync"
```

### Configuration Differences

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| **Concurrent Connections** | Limited | High |
| **Data Types** | Basic | Rich (JSON, Arrays, etc.) |
| **Performance** | Good for small datasets | Optimized for large datasets |
| **Backup** | File copy | pg_dump/pg_restore |
| **Scaling** | Single file | Horizontal scaling |

### Production Considerations

#### Connection Pooling
PostgreSQL automatically uses connection pooling through SQLAlchemy:

```python
# Configured in src/config/config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True,
    'pool_recycle': 300
}
```

#### Backup Strategy
```bash
# Database backup
pg_dump -h localhost -U iotflow_user iotflow > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql -h localhost -U iotflow_user iotflow < backup_20241201_143000.sql
```

#### Performance Optimization
```sql
-- Recommended indexes for production
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_last_seen ON devices(last_seen);
CREATE INDEX idx_devices_api_key ON devices(api_key);
```

#### Monitoring
```bash
# Connection monitoring
psql -h localhost -U iotflow_user iotflow -c "SELECT count(*) FROM pg_stat_activity WHERE datname='iotflow';"

# Database size monitoring
psql -h localhost -U iotflow_user iotflow -c "SELECT pg_size_pretty(pg_database_size('iotflow'));"
```

### Troubleshooting

#### Common Issues

**Connection refused:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql
sudo systemctl start postgresql
```

**Authentication failed:**
```bash
# Verify credentials
psql -h localhost -U iotflow_user iotflow
```

**Redis sync issues:**
```bash
# Check Redis-database sync logs
tail -f logs/iotflow.log | grep "redis_util\|Database sync"

# Verify Redis connection
redis-cli ping
```

**Permission issues:**
```sql
-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO iotflow_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO iotflow_user;
```

#### Performance Issues

**Slow queries:**
```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_reload_conf();

-- Monitor slow queries
SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
```

**High connection count:**
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname='iotflow';

-- Adjust connection limits if needed
ALTER SYSTEM SET max_connections = 200;
```

## �🚀 Quick Start

### Prerequisites

- **Python 3.10+** 
- **Poetry** (recommended) or pip
- **Docker & Docker Compose**
- **PostgreSQL 15+**
- **Git**

### 1. Clone and Setup

```bash
git clone <repository-url>
cd IoTFlow_ConnectivityLayer

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies with Poetry
poetry install

# Or with pip
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional - defaults work for development)
nano .env
```

### 3. Start Services & Initialize

```bash
# Start PostgreSQL with Docker Compose
docker compose up -d

# Initialize database and create default users
poetry run python init_db.py

# Start Flask application
poetry run python app.py
```

### 4. Verify Installation

```bash
# Check service health
curl http://localhost:5000/health

# View API documentation
open http://localhost:5000/docs

# Run comprehensive tests
poetry run pytest tests/
```

## 🧪 Testing & Validation

### Running Tests

```bash
# Run all tests
poetry run pytest tests/ -v

# Run specific test files
poetry run pytest tests/test_devices.py -v
poetry run pytest tests/test_telemetry.py -v
poetry run pytest tests/test_user.py -v

# Run with coverage
poetry run pytest tests/ --cov=src --cov-report=html
```

### Available Test Suites

- `test_devices.py` - Device registration, status, and management
- `test_telemetry.py` - Telemetry data submission and retrieval
- `test_user.py` - User creation and management
- `test_admin.py` - Admin operations
- `test_charts_api.py` - Chart configuration
- `test_health.py` - Health check endpoints
## 📡 API Endpoints

The IoTFlow platform provides a comprehensive API for device management, telemetry data handling, administration, and system monitoring. The APIs follow RESTful principles and use the following authentication mechanisms:

- **No Authentication**: Public endpoints like health checks and device registration
- **API Key**: Device-specific endpoints requiring the `X-API-Key` header
- **Admin Token**: Administrative endpoints requiring `Authorization: admin <TOKEN>` header

### 🔌 Device Management

| Method | Endpoint                    | Description                    | Auth Required |
|--------|----------------------------|--------------------------------|---------------|
| POST   | `/api/v1/devices/register` | Register new device            | X-User-ID     |
| GET    | `/api/v1/devices/status`   | Get device status & health     | API Key       |
| POST   | `/api/v1/devices/heartbeat`| Send device heartbeat          | API Key       |
| PUT    | `/api/v1/devices/config`   | Update device configuration    | API Key       |
| GET    | `/api/v1/devices/credentials` | Get device credentials      | API Key       |
| GET    | `/api/v1/devices/user/{user_id}` | Get user's devices       | None          |
| GET    | `/api/v1/devices/{device_id}/status` | Get device status by ID | X-User-ID |

### 📊 Telemetry & Data

| Method | Endpoint                           | Description                    | Auth Required |
|--------|------------------------------------|--------------------------------|---------------|
| POST   | `/api/v1/telemetry`               | Submit telemetry data          | API Key       |
| GET    | `/api/v1/telemetry/{device_id}`   | Get device telemetry history   | API Key       |
| GET    | `/api/v1/telemetry/{device_id}/latest` | Get latest telemetry      | API Key       |
| GET    | `/api/v1/telemetry/{device_id}/aggregated` | Get aggregated data   | API Key       |
| DELETE | `/api/v1/telemetry/{device_id}`   | Delete device telemetry        | API Key       |
| GET    | `/api/v1/telemetry/status`        | Get telemetry system status    | None          |
| GET    | `/api/v1/telemetry/user/{user_id}` | Get user's telemetry data     | X-User-ID     |

### 👥 User Management

| Method | Endpoint                      | Description                 | Auth Required |
|--------|-------------------------------|-----------------------------|--------------| 
| POST   | `/api/v1/auth/register`       | Register new user           | None          |
| GET    | `/api/v1/users/{user_id}`     | Get user details            | User ID or Admin |
| GET    | `/api/v1/users`               | List all users              | Admin Token   |
| PUT    | `/api/v1/users/{user_id}`     | Update user                 | User ID or Admin |
| DELETE | `/api/v1/users/{user_id}`     | Delete/deactivate user      | Admin Token   |

### 🔐 Authentication

| Method | Endpoint                      | Description                 | Auth Required |
|--------|-------------------------------|-----------------------------|--------------| 
| POST   | `/api/v1/auth/login`          | User login (JWT)            | None          |
| POST   | `/api/v1/auth/refresh`        | Refresh JWT token           | JWT           |

### 📊 Charts

| Method | Endpoint                      | Description                 | Auth Required |
|--------|-------------------------------|-----------------------------|--------------| 
| POST   | `/api/v1/charts`              | Create chart                | X-User-ID     |
| GET    | `/api/v1/charts/{chart_id}`   | Get chart details           | None          |
| PUT    | `/api/v1/charts/{chart_id}`   | Update chart                | X-User-ID     |
| DELETE | `/api/v1/charts/{chart_id}`   | Delete chart                | X-User-ID     |
| GET    | `/api/v1/charts/user/{user_id}` | Get user's charts         | None          |

### 🛠️ Administration

| Method | Endpoint                      | Description                 | Auth Required |
|--------|-------------------------------|-----------------------------|--------------| 
| GET    | `/api/v1/admin/devices`       | List all devices            | Admin         |
| GET    | `/api/v1/admin/devices/statuses` | Get all device statuses  | Admin         |
| GET    | `/api/v1/admin/devices/{id}`  | Get device details          | Admin         |
| PUT    | `/api/v1/admin/devices/{id}`  | Update device               | Admin         |
| DELETE | `/api/v1/admin/devices/{id}`  | Delete device               | Admin         |
| PUT    | `/api/v1/admin/devices/{id}/status` | Update device status  | Admin         |
| GET    | `/api/v1/admin/stats`         | Get system statistics       | Admin         |
| GET    | `/api/v1/admin/cache/device-status` | Get device cache stats | Admin        |
| DELETE | `/api/v1/admin/cache/device-status` | Clear all device cache | Admin        |
| DELETE | `/api/v1/admin/cache/devices/{id}` | Clear specific device cache | Admin     |

### 🔍 System Health

| Method | Endpoint              | Description              | Auth Required |
|--------|-----------------------|--------------------------|---------------|
| GET    | `/health`             | API health check         | None          |
| GET    | `/api/v1/telemetry/status` | Telemetry system status | None      |

\* API Key required if accessing own device data; Admin token required for other devices

## 💡 Usage Examples

### Create a User

```bash
curl -X POST http://localhost:5000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "User created successfully",
  "user": {
    "id": 1,
    "user_id": "adc513e4ab554b3f84900affe582beb8",
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true,
    "is_admin": false,
    "created_at": "2025-11-23T14:30:00Z"
  }
}
```

### Register a Device

```bash
curl -X POST http://localhost:5000/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -H "X-User-ID: adc513e4ab554b3f84900affe582beb8" \
  -d '{
    "name": "Smart Temperature Sensor 001",
    "description": "Living room environmental sensor",
    "device_type": "sensor",
    "location": "Living Room",
    "firmware_version": "1.2.3",
    "hardware_version": "v2.1"
  }'
```

**Response:**
```json
{
  "message": "Device registered successfully",
  "device": {
    "id": 1,
    "name": "Smart Temperature Sensor 001",
    "api_key": "rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB",
    "status": "inactive",
    "device_type": "sensor",
    "user_id": 1,
    "created_at": "2025-11-23T14:30:00Z",
    "owner": {
      "username": "john_doe",
      "email": "john@example.com"
    }
  }
}
```

### Submit Telemetry Data

```bash
# Submit telemetry data
curl -X POST http://localhost:5000/api/v1/telemetry \
  -H "X-API-Key: rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "temperature": 23.5,
      "humidity": 65.2
    },
    "metadata": {
      "location": "Living Room"
    },
    "timestamp": "2025-11-23T14:30:00Z"
  }'
```

### Query Telemetry Data

```bash
# Get latest telemetry
curl "http://localhost:5000/api/v1/telemetry/1/latest" \
  -H "X-API-Key: rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB"

# Get historical data with filters
curl "http://localhost:5000/api/v1/telemetry/1?start_time=-1h&limit=100" \
  -H "X-API-Key: rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB"

# Get aggregated data (hourly averages)
curl "http://localhost:5000/api/v1/telemetry/1/aggregated?window=1h&start_time=-24h&field=temperature&aggregation=mean" \
  -H "X-API-Key: rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB"

# Get telemetry system status
curl "http://localhost:5000/api/v1/telemetry/status"
```

### Device Heartbeat

```bash
curl -X POST http://localhost:5000/api/v1/devices/heartbeat \
  -H "X-API-Key: rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB"
```

### User Login

```bash
# Login to get JWT token
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password"
  }'

# Response includes JWT token
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "user_id": "adc513e4ab554b3f84900affe582beb8",
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

### Administration APIs

```bash
# Get admin token from environment (for example purposes)
ADMIN_TOKEN="test"

# List all devices
curl "http://localhost:5000/api/v1/admin/devices" \
  -H "Authorization: admin ${ADMIN_TOKEN}"

# Get detailed device information
curl "http://localhost:5000/api/v1/admin/devices/1" \
  -H "Authorization: admin ${ADMIN_TOKEN}"

# Update device status
curl -X PUT "http://localhost:5000/api/v1/admin/devices/1/status" \
  -H "Authorization: admin ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "maintenance"
  }'

# Get system statistics
curl "http://localhost:5000/api/v1/admin/stats" \
  -H "Authorization: admin ${ADMIN_TOKEN}"

# Clear device cache
curl -X DELETE "http://localhost:5000/api/v1/admin/cache/devices/1" \
  -H "Authorization: admin ${ADMIN_TOKEN}"
```
## 🗃️ Data Architecture

### PostgreSQL Database

The platform uses PostgreSQL as the primary database for all data storage through SQLAlchemy ORM.

**Users Table:**
- `id` - Primary key (SERIAL)
- `user_id` - Unique UUID (VARCHAR(32))
- `username` - Unique username (VARCHAR(80))
- `email` - Unique email (VARCHAR(120))
- `password_hash` - Hashed password (VARCHAR(128))
- `is_active` - Account status (BOOLEAN)
- `is_admin` - Admin privileges (BOOLEAN)
- `created_at` - Registration timestamp (TIMESTAMP)
- `updated_at` - Last modification (TIMESTAMP)
- `last_login` - Last login timestamp (TIMESTAMP)

**Devices Table:**
- `id` - Primary key (SERIAL)
- `name` - Device name (VARCHAR(100))
- `description` - Device description (TEXT)
- `device_type` - Category (VARCHAR(50): sensor, actuator, etc.)
- `api_key` - Unique authentication key (VARCHAR(64))
- `status` - Device status (VARCHAR(20): active, inactive, maintenance)
- `location` - Physical location (VARCHAR(200))
- `firmware_version` - Current firmware version (VARCHAR(20))
- `hardware_version` - Hardware revision (VARCHAR(20))
- `user_id` - Foreign key to users table (INTEGER)
- `created_at` - Registration timestamp (TIMESTAMP)
- `updated_at` - Last modification (TIMESTAMP)
- `last_seen` - Last heartbeat/activity (TIMESTAMP)

**Telemetry Data Table:**
- `id` - Primary key (SERIAL)
- `device_id` - Device identifier (VARCHAR)
- `timestamp` - Measurement timestamp (TIMESTAMP)
- `measurement_name` - Measurement type (VARCHAR)
- `value` - Measurement value (FLOAT)
- `unit` - Unit of measurement (VARCHAR)
- `device_type` - Device category (VARCHAR)
- `user_id` - Owner user ID (INTEGER)
- `metadata` - Additional data (JSONB)

**Charts Tables:**
- `charts` - Chart configurations with user associations
- `chart_devices` - Many-to-many relationship between charts and devices
- `chart_measurements` - Measurement configurations for charts

## 🛠️ Development & Management

### Project Structure

```
IoTFlow_ConnectivityLayer/
├── 📁 src/                          # Core application code
│   ├── config/                      # Configuration management
│   │   └── config.py               # Flask & database config
│   ├── models/                      # SQLAlchemy database models
│   │   └── __init__.py             # User, Device, Chart models
│   ├── routes/                      # API route handlers
│   │   ├── devices.py              # Device management endpoints
│   │   ├── telemetry_postgres.py   # Telemetry data endpoints
│   │   ├── admin.py                # Administrative endpoints
│   │   ├── users.py                # User management endpoints
│   │   ├── auth.py                 # Authentication endpoints
│   │   └── charts.py               # Chart configuration endpoints
│   ├── services/                    # Business logic services
│   │   └── postgres_telemetry.py   # PostgreSQL telemetry service
│   ├── middleware/                  # Request/response middleware
│   │   ├── auth.py                 # Authentication & authorization
│   │   ├── security.py             # Security utilities
│   │   └── monitoring.py           # Performance monitoring
│   └── utils/                       # Utility functions
│       ├── logging.py              # Logging configuration
│       └── time_util.py            # Timestamp utilities
├── 📁 simulators/                   # Device simulation examples
│   ├── example_usage.py            # Simulator usage example
│   ├── simulator_config.py         # Simulator configuration
│   └── README.md                   # Simulator usage guide
├── 📁 tests/                        # Test suites
│   ├── test_devices.py             # Device tests
│   ├── test_telemetry.py           # Telemetry tests
│   ├── test_user.py                # User tests
│   ├── test_admin.py               # Admin tests
│   ├── test_charts_api.py          # Chart tests
│   └── test_health.py              # Health check tests
├── 📁 docs/                         # Documentation
│   ├── API_DOCUMENTATION.md
│   ├── SETUP_GUIDE.md
│   └── openapi.yaml                # OpenAPI specification
├── 📁 logs/                         # Application logs
├── 🐳 docker-compose.yml            # Container orchestration
├── 📦 pyproject.toml                # Poetry dependencies
├── 📄 requirements.txt              # Pip dependencies
├── 📄 app.py                        # Flask application entrypoint
├── 📄 init_db.py                    # Database initialization script
├── 📄 README.md                     # Project documentation
├── 📄 .env.example                  # Example environment config
└── 📄 instance/                     # PostgreSQL data directory
```

### Management Commands

#### Database Management

```bash
# Initialize database and create default users
poetry run python init_db.py

# Connect to PostgreSQL
docker compose exec postgres psql -U iotflow -d iotflow

# Backup database
docker compose exec postgres pg_dump -U iotflow iotflow > backup.sql

# Restore database
docker compose exec -T postgres psql -U iotflow iotflow < backup.sql
```

#### Application Management

```bash
# Start Flask application
poetry run python app.py

# Run with Gunicorn (production)
poetry run gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Run tests
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/test_devices.py -v
```

### Default Users

After running `init_db.py`, the following users are created:

| Username | Password | Role | User ID |
|----------|----------|------|---------|
| admin | admin123 | Admin | (generated UUID) |
| testuser | test123 | Regular User | (generated UUID) |

Use these credentials for testing and development. Change passwords in production!

### Configuration Management

#### Environment Variables (.env)

| Category | Variable | Description | Default |
|----------|----------|-------------|---------|
| **Flask** | `FLASK_ENV` | Environment mode | `development` |
| | `FLASK_DEBUG` | Debug mode | `True` |
| | `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| | `HOST` | Server host | `0.0.0.0` |
| | `PORT` | Server port | `5000` |
| **Database** | `DATABASE_URL` | PostgreSQL connection URL | `postgresql://iotflow:iotflowpass@postgres:5432/iotflow` |
| **Security** | `JWT_SECRET_KEY` | JWT token secret | `jwt-secret-key` |
| | `API_KEY_LENGTH` | Generated API key length | `32` |
| | `RATE_LIMIT_PER_MINUTE` | API rate limiting | `60` |
| | `IOTFLOW_ADMIN_TOKEN` | Admin API token | `test` |
| **Logging** | `LOG_LEVEL` | Logging level | `INFO` |
| | `LOG_FILE` | Log file path | `logs/iotflow.log` |
| **API** | `API_VERSION` | API version | `v1` |
| | `MAX_DEVICES_PER_USER` | Max devices per user | `100` |

#### PostgreSQL Configuration

**Connection Settings:**
- Host: `postgres` (Docker) or `localhost` (local)
- Port: `5432`
- Database: `iotflow`
- User: `iotflow`
- Password: `iotflowpass`

**Performance:**
- Connection pooling via SQLAlchemy
- Indexed columns for fast queries
- JSONB support for flexible metadata storage

## 🚀 Production Deployment

### Container Deployment

```bash
# Production-ready deployment
docker compose -f docker-compose.prod.yml up -d

# Scale application instances
docker compose up --scale app=3

# Health checks and monitoring
docker compose ps
docker compose logs -f app
```

### Performance Tuning

#### Flask Application
```bash
# Use Gunicorn for production
poetry run gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - app:app

# With performance monitoring
poetry run gunicorn -w 4 -b 0.0.0.0:5000 --statsd-host=localhost:8125 app:app
```

#### Database Optimization
- **PostgreSQL**: Connection pooling, prepared statements, and query optimization
- **Indexes**: Strategic indexes on frequently queried columns
- **JSONB**: Efficient storage and querying of flexible telemetry data

### Security Hardening

#### API Security
- Rate limiting per device and IP
- API key rotation capabilities
- Request payload validation
- CORS configuration for web clients

#### Infrastructure Security
- TLS termination at load balancer
- Network isolation between services
- Secrets management (avoid plain text)
- Regular security updates

### Monitoring & Observability

#### Built-in Monitoring
```bash
# Application health
curl http://localhost:5000/health

# Service metrics
curl http://localhost:5000/api/v1/telemetry/status

# Admin dashboard
curl http://localhost:5000/api/v1/admin/dashboard
```

#### External Monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards  
- **ELK Stack**: Log aggregation and analysis
- **Alerting**: PagerDuty, Slack integration

### System Health

```bash
# Basic health check
curl "http://localhost:5000/health"

# Detailed health check with all components
curl "http://localhost:5000/health?detailed=true"

# Check specific components
curl "http://localhost:5000/health?include=iotdb,redis,mqtt"

# Check telemetry system status
curl "http://localhost:5000/api/v1/telemetry/status"
```

## 📊 Performance Benchmarks

### Test Results (Local Development)

#### HTTP API Performance
- **Device Registration**: ~40ms average response time
- **Telemetry Storage**: ~70ms average (SQLite + IoTDB)
- **Data Retrieval**: ~50ms average
- **Concurrent Requests**: 100+ requests/second

#### Fleet Simulation Results
- **9 Device Fleet**: 20+ telemetry points/minute
- **30 Device Fleet**: 100+ telemetry points/minute  
- **Network Failure Simulation**: 5% realistic failure rate
- **Data Integrity**: 100% for successful transmissions

#### Database Performance
- **SQLite**: 1000+ device registrations/second
- **IoTDB**: 10,000+ telemetry points/second
- **Redis**: Sub-millisecond caching responses
- **Storage**: ~1KB per telemetry record

## 🔧 Troubleshooting Guide

### Common Issues and Solutions

#### 🚨 HTTP 500 Error on Telemetry Submission

**Symptoms:** `{"error":"Failed to store telemetry data","message":"IoTDB may not be available. Check logs for details."}`

**Diagnosis:**
```bash
# Check PostgreSQL service status
docker compose ps

# Check Flask application logs
tail -50 logs/iotflow.log
```

**Solutions:**
1. **IoTDB Service Issues:**
   ```bash
   # Restart IoTDB service
   docker restart iotflow-iotdb
   
   # Check IoTDB initialization
   docker logs iotflow-iotdb | grep -i "error\|exception"
   ```

2. **Connection Issues:**
   ```bash
   # Verify IoTDB port accessibility
   telnet localhost 6667
   
   # Check network configuration
   docker network inspect iotflow_default
   ```

3. **Data Format Issues:**
   ```bash
   # Test with simple telemetry data
   curl -X POST http://localhost:5000/api/v1/telemetry \
     -H "X-API-Key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"data": {"temperature": 25.0}}'
   ```

#### 🔌 Device Registration Issues

**Symptoms:** Device already exists errors, API key conflicts

**Solutions:**
```bash
# Check existing devices
curl http://localhost:5000/api/v1/admin/devices

# Use auto-suffix for testing
poetry run python simulators/new_mqtt_device_simulator.py \
    --name TestDevice --auto-suffix

# Force registration (development only)
poetry run python simulators/new_mqtt_device_simulator.py \
    --name TestDevice --force-register
```

#### 📡 MQTT Connection Problems

**Symptoms:** MQTT connection failures, authentication errors

**Diagnosis:**
```bash
# Check MQTT broker status
docker logs iotflow-mqtt

# Test MQTT connectivity
mosquitto_pub -h localhost -p 1883 -t "test/topic" -m "test message"
```

**Solutions:**
```bash
# Restart MQTT broker
docker restart iotflow-mqtt

# Check authentication
cat mqtt/config/passwd

# Verify MQTT configuration
cat mqtt/config/mosquitto.conf
```

#### 💾 Database Issues

**Symptoms:** SQLite database corruption, IoTDB storage errors

**Solutions:**
```bash
# Backup current database
docker compose exec postgres pg_dump -U iotflow iotflow > backup.sql

# Initialize fresh database
poetry run python manage.py init-db
```

### Performance Issues

#### Slow API Responses
1. **Check resource usage:**
   ```bash
   docker stats
   ```

2. **Database optimization:**
   ```bash
   # PostgreSQL maintenance
   docker compose exec postgres psql -U iotflow -d iotflow -c "VACUUM ANALYZE;"
   
   # Check database size
   docker compose exec postgres psql -U iotflow -d iotflow -c "SELECT pg_size_pretty(pg_database_size('iotflow'));"
   ```

### Data Verification Tools

#### Check Data Flow
```bash
# Check telemetry data via API
curl "http://localhost:5000/api/v1/telemetry/1/latest" \
  -H "X-API-Key: YOUR_API_KEY"

# Check device status
curl "http://localhost:5000/api/v1/devices/status" \
  -H "X-API-Key: YOUR_API_KEY"
```

## 📚 Advanced Features

### 🔍 Data Analytics and Querying

#### PostgreSQL Telemetry Queries
```bash
# Get aggregated telemetry data
curl "http://localhost:5000/api/v1/telemetry/1/aggregated?field=temperature&aggregation=mean&window=1h&start_time=-24h" \
  -H "X-API-Key: YOUR_API_KEY"

# Get historical data with time range
curl "http://localhost:5000/api/v1/telemetry/1?start_time=-24h&limit=1000" \
  -H "X-API-Key: YOUR_API_KEY"
```

#### Data Export
```bash
# Export device data via API
curl "http://localhost:5000/api/v1/telemetry/1?start_time=-24h&limit=10000" \
  -H "X-API-Key: YOUR_API_KEY" > device_data.json

# Direct PostgreSQL export
docker compose exec postgres psql -U iotflow -d iotflow \
  -c "COPY (SELECT * FROM telemetry_data WHERE device_id='1') TO STDOUT CSV HEADER" > device_1_data.csv
```

### 🤖 Device Simulation

#### Simulating Devices
```bash
# Create test devices via API
curl -X POST http://localhost:5000/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -H "X-User-ID: YOUR_USER_ID" \
  -d '{
    "name": "TestDevice1",
    "device_type": "sensor",
    "location": "Lab"
  }'

# Submit test telemetry
curl -X POST http://localhost:5000/api/v1/telemetry \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "temperature": 25.5,
      "humidity": 60.0
    }
  }'
```

### 🔐 Security and Authentication

#### API Key Management
```bash
# API keys are automatically generated during device registration
# To get device credentials including API key:
curl "http://localhost:5000/api/v1/devices/credentials" \
  -H "X-API-Key: YOUR_API_KEY"
```

#### Advanced Rate Limiting
Configure per-device and per-endpoint rate limiting in `src/middleware/auth.py`:
- Device-specific limits
- Time-window based limiting
- Redis-backed rate limiting
- Automatic scaling based on device tier

### 📊 Monitoring and Alerting

#### System Health Monitoring
```bash
# Basic health check
curl http://localhost:5000/health

# Detailed health check
curl "http://localhost:5000/health?detailed=true"

# Telemetry system status
curl http://localhost:5000/api/v1/telemetry/status
```

## 🔮 Future Roadmap

### Planned Features
- **🌐 Web Dashboard**: React-based admin interface
- **📱 Mobile API**: RESTful API optimizations for mobile apps
- **🔄 Device Firmware OTA**: Over-the-air firmware updates
- **🧠 ML Analytics**: Machine learning for predictive maintenance
- **📡 LoRaWAN Support**: Long-range, low-power device connectivity
- **🔐 OAuth2**: Enterprise authentication integration

### Architecture Evolution
- **Microservices**: Service decomposition for scalability
- **Message Queues**: Apache Kafka integration for high-throughput
- **Edge Computing**: Edge device data processing capabilities

## 🤝 Contributing

### Development Guidelines

#### Code Style
```bash
# Install development dependencies
poetry install --with dev

# Set up pre-commit hooks
poetry run pre-commit install

# Run code formatting
poetry run black .
poetry run isort .

# Run linting
poetry run flake8 .
poetry run mypy .
```

#### Testing Requirements
- Unit tests for all new features
- Integration tests for API endpoints
- End-to-end tests for device simulation
- Performance benchmarks for data operations

#### Pull Request Process
1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Write tests for new functionality
4. Ensure all tests pass (`poetry run pytest`)
5. Update documentation
6. Submit pull request with detailed description

### Development Environment

```bash
# Complete development setup
git clone <repository-url>
cd IoTFlow_ConnectivityLayer

# Install dependencies
poetry install --with dev

# Set up environment
cp .env.example .env

# Start services
docker compose up -d
poetry run python init_db.py

# Run in development mode
FLASK_ENV=development poetry run python app.py

# Run tests continuously
poetry run pytest --watch
```

### Code Quality

```bash
# Code formatting
poetry run black src/ simulators/
poetry run isort src/ simulators/

# Linting
poetry run flake8 src/ simulators/
poetry run mypy src/

# Testing
poetry run pytest tests/ --cov=src/
```

## 📚 Documentation

- **[Management Guide](MANAGEMENT_GUIDE.md)** - Comprehensive setup and management
- **[API Documentation](docs/api.md)** - Complete API reference
- **[Architecture Guide](docs/architecture.md)** - System design and components
- **[Testing Results](HTTP_SIMULATION_TEST_RESULTS.md)** - Performance and reliability tests
- **[IoTDB Integration](docs/iotdb_integration.md)** - Time-series database setup
- **[Device Status Cache](docs/device_status_cache.md)** - Redis-based device status caching

## ❓ Frequently Asked Questions (FAQ)

### General Questions

**Q: What's the difference between the legacy simulators and the new advanced simulator?**
A: The new advanced MQTT simulator (v2.1.0) replaces all legacy simulators with a single, production-ready tool that includes:
- Multiple simulation profiles (default, high_frequency, energy_efficient, industrial)
- Smart device registration handling (existing device detection, auto-suffix)
- Realistic device behavior with battery simulation and network jitter
- Comprehensive telemetry types and MQTT command handling
- Better error handling and logging

**Q: How do I handle the "device already exists" error during testing?**
A: Use one of these approaches:
```bash
# Option 1: Auto-suffix (recommended for testing)
--auto-suffix

# Option 2: Use a different device name
--name TestDevice_$(date +%s)

# Option 3: Force registration (development only)
--force-register
```

**Q: Why am I getting HTTP 500 errors when submitting telemetry?**
A: This usually indicates PostgreSQL connection issues. Check:
1. PostgreSQL service status: `docker compose ps`
2. Database connectivity: `docker compose exec postgres psql -U iotflow -d iotflow -c "SELECT 1;"`
3. Application logs: `tail -f logs/iotflow.log`

**Q: How can I monitor device activity in real-time?**
A: Use the API endpoints:
```bash
# Get latest telemetry
curl "http://localhost:5000/api/v1/telemetry/1/latest" -H "X-API-Key: YOUR_API_KEY"

# Get device status
curl "http://localhost:5000/api/v1/devices/status" -H "X-API-Key: YOUR_API_KEY"

# Check application logs
tail -f logs/iotflow.log
```

### Technical Questions

**Q: What data types are supported for telemetry?**
A: PostgreSQL supports:
- **Numeric**: INTEGER, FLOAT, DOUBLE (for sensor readings)
- **Text**: VARCHAR, TEXT (for status messages)
- **Boolean**: BOOLEAN (for device states)
- **Complex**: JSONB (for flexible metadata and nested objects)

**Q: How is data stored and organized?**
A: 
- **All data**: PostgreSQL database (users, devices, telemetry, charts)
- **Telemetry data**: `telemetry_data` table with JSONB metadata support
- **Device metadata**: `devices` table with user relationships
- **User data**: `users` table with authentication

**Q: Can I use this in production?**
A: Yes, with proper configuration:
- Use production database settings (PostgreSQL instead of SQLite)
- Enable TLS for MQTT and HTTP
- Set up proper monitoring and alerting
- Configure rate limiting and security headers
- Use load balancing for Flask application

**Q: How do I scale the platform for more devices?**
A: Scaling strategies:
1. **Horizontal scaling**: Multiple Flask instances behind load balancer
2. **Database scaling**: PostgreSQL with read replicas and connection pooling
3. **Caching**: Add Redis for frequently accessed data
4. **Message queuing**: Add Apache Kafka for high-throughput scenarios
5. **Microservices**: Split into device management, telemetry, and analytics services

### Development Questions

**Q: How do I add a new device type?**
A: 
1. Add device type to the allowed types in `src/routes/devices.py`
2. Update device simulator profiles if needed
3. Consider any specific telemetry requirements
4. Update documentation and tests

**Q: How do I add custom telemetry fields?**
A: Telemetry fields are flexible:
```python
# In API call
"data": {
    "temperature": 25.0,
    "custom_field": "any_value"
},
"metadata": {
    "complex_data": {"nested": "object"}
}
```
PostgreSQL stores each measurement as a separate row with JSONB metadata support.

**Q: How do I backup and restore data?**
A: 
```bash
# Backup PostgreSQL database
docker compose exec postgres pg_dump -U iotflow iotflow > backup.sql

# Restore database
docker compose exec -T postgres psql -U iotflow iotflow < backup.sql
```

## 📋 Quick Reference

### Essential Commands
```bash
# Complete setup
docker compose up -d && poetry run python init_db.py && poetry run python app.py

# Check system health
curl http://localhost:5000/health

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

### API Endpoints Summary
| Purpose | Method | Endpoint | Authentication |
|---------|--------|----------|----------------|
| Register device | POST | `/api/v1/devices/register` | None |
| Submit telemetry | POST | `/api/v1/telemetry` | API Key |
| Submit telemetry (MQTT) | POST | `/api/v1/mqtt/telemetry/{device_id}` | API Key |
| Get latest telemetry | GET | `/api/v1/telemetry/{device_id}/latest` | API Key* |
| Get device history | GET | `/api/v1/telemetry/{device_id}?start_time=-24h&limit=100` | API Key* |
| Send heartbeat | POST | `/api/v1/devices/heartbeat` | API Key |
| Get device status | GET | `/api/v1/devices/status` | API Key |
| Update device config | PUT | `/api/v1/devices/config` | API Key |
| List all devices | GET | `/api/v1/admin/devices` | Admin |
| System statistics | GET | `/api/v1/admin/stats` | Admin |
| Health check | GET | `/health` | None |
| MQTT status | GET | `/api/v1/mqtt/status` | None |

\* API Key required if accessing own device data; Admin token required for other devices

### Common Data Formats
```bash
# Device registration
{
  "name": "MyDevice",
  "device_type": "smart_sensor",
  "location": "Office",
  "description": "Temperature and humidity sensor"
}

# Telemetry submission
{
  "data": {
    "temperature": 23.5,
    "humidity": 65.2,
    "battery_level": 87
  },
  "metadata": {
    "location": "Office",
    "sensor_status": "active"
  },
  "timestamp": "2025-07-04T10:30:00Z"
}
```

## 📞 Support and Community

### Getting Help
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Comprehensive docs in `/docs` directory
- **Examples**: Working examples in `/simulators` and `/scripts`
- **Logs**: Detailed logging for troubleshooting

### Reporting Issues
When reporting issues, please include:
1. **Environment details**: OS, Python version, Docker version
2. **Steps to reproduce**: Exact commands and configuration
3. **Error messages**: Complete error output and logs
4. **Expected behavior**: What should have happened
5. **Actual behavior**: What actually happened

### Feature Requests
- Use GitHub issues with the "enhancement" label
- Provide detailed use case and requirements
- Include examples of expected API behavior
- Consider backward compatibility implications

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **IoTDB Community** for the excellent time-series database
- **Flask Community** for the robust web framework
- **Docker Community** for containerization best practices
- **MQTT.org** for the messaging protocol specifications
- **Contributors** who have helped improve this platform

---

**IoTFlow v0.2** - A modern, production-ready IoT connectivity platform.

Built with ❤️ for the IoT community.
