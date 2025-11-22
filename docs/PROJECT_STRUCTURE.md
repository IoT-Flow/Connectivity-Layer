# IoTFlow Project Structure

## 📁 Root Directory

```
IoTFlow_ConnectivityLayer/
├── 📁 .github/              # GitHub workflows and CI/CD
├── 📁 .kiro/                # Kiro IDE specs and configuration
│   └── specs/
│       └── iot-dashboard-frontend/  # Frontend spec
├── 📁 docs/                 # Project documentation
├── 📁 instance/             # SQLite database files (development)
├── 📁 locust/               # Load testing scripts
├── 📁 logs/                 # Application logs
├── 📁 simulators/           # IoT device simulators
├── 📁 src/                  # Source code
├── 📁 tests/                # Test suites
├── .env                     # Environment variables (not in git)
├── .env.example             # Environment template
├── app.py                   # Flask application entry point
├── docker-compose.yml       # Docker services configuration
├── init_db.py               # Database initialization script
├── poetry.lock              # Poetry lock file
├── pyproject.toml           # Poetry dependencies
├── requirements.txt         # Pip dependencies
├── README.md                # Main project documentation
├── API_DOCUMENTATION_SUMMARY.md  # API overview
└── QUICK_REFERENCE.md       # Quick reference guide
```

## 📁 Source Code (`src/`)

```
src/
├── 📁 config/               # Configuration management
│   ├── config.py           # Flask & database config
│   └── iotdb_config.py     # IoTDB configuration
├── 📁 middleware/           # Request/response middleware
│   ├── auth.py             # Authentication & authorization
│   ├── security.py         # Security utilities
│   └── monitoring.py       # Performance monitoring
├── 📁 models/               # Database models
│   └── __init__.py         # User, Device, Chart, etc.
├── 📁 routes/               # API route handlers
│   ├── admin.py            # Admin endpoints
│   ├── auth.py             # Authentication endpoints
│   ├── charts.py           # Charts API ✨ NEW
│   ├── devices.py          # Device management
│   ├── telemetry_postgres.py  # Telemetry endpoints
│   └── users.py            # User management
├── 📁 services/             # Business logic services
│   ├── device_status_cache.py  # Device status cache
│   ├── iotdb.py            # IoTDB service layer
│   ├── mqtt_auth.py        # MQTT authentication
│   ├── postgres_telemetry.py  # PostgreSQL telemetry
│   └── status_sync_service.py  # Status sync logic
└── 📁 utils/                # Utility functions
    ├── logging.py          # Logging configuration
    ├── redis_util.py       # Redis utilities
    └── time_util.py        # Timestamp utilities
```

## 📁 Tests (`tests/`)

```
tests/
├── test_admin.py           # Admin API tests
├── test_admin_user_deletion.py  # User deletion tests
├── test_charts_api.py      # Charts API tests ✨ NEW
├── test_devices.py         # Device API tests
├── test_health.py          # Health check tests
├── test_telemetry.py       # Telemetry API tests
├── test_user.py            # User API tests
└── test_user_devices.py    # User-device relationship tests
```

## 📁 Documentation (`docs/`)

### Active Documentation
```
docs/
├── API_DOCUMENTATION.md    # Complete API reference
├── CHARTS_API_COMPLETE.md  # Charts API documentation ✨ NEW
├── MISSING_APIS.md         # Future API roadmap
├── openapi.yaml            # OpenAPI specification
├── postgres-telemetry-architecture.md  # Telemetry architecture
├── postgres-telemetry-schema.sql  # Database schema
├── README.md               # Documentation index
├── SETUP_GUIDE.md          # Setup instructions
├── SWAGGER_UI_GUIDE.md     # Swagger UI guide
├── USER_DEVICES_API.md     # User devices API
└── 📁 archive/             # Historical documentation
    ├── ADMIN_TDD_SUMMARY.md
    ├── ADMIN_USER_DELETION.md
    ├── DEVICE_MANAGEMENT_TDD_SUMMARY.md
    ├── FINAL_CLEANUP_SUMMARY.md
    ├── HEALTH_MONITORING_TDD_SUMMARY.md
    ├── REDIS_REMOVAL_SUMMARY.md
    ├── SWAGGER_COMPLETE.md
    ├── SWAGGER_QUICK_FIX.md
    ├── SWAGGER_STATUS.md
    ├── SYSTEM_TEST_REPORT.md
    ├── TDD_IMPLEMENTATION_COMPLETE.md
    ├── TDD_ROADMAP.md
    ├── TELEMETRY_TDD_SUMMARY.md
    └── USER_TDD_SUMMARY.md
```

## 📁 Simulators (`simulators/`)

```
simulators/
├── mqtt_device_simulator.py  # Advanced MQTT simulator
├── example_usage.py          # Usage examples
├── simulator_config.py       # Simulator configuration
└── README.md                 # Simulator documentation
```

## 🗄️ Database Tables

### Core Tables
- **users** - User accounts
- **devices** - IoT devices
- **telemetry_data** - Time-series sensor data

### Chart Tables ✨ NEW
- **charts** - Chart configurations
- **chart_devices** - Chart-device associations (many-to-many)
- **chart_measurements** - Measurement configurations with colors

## 🔌 API Endpoints

### Authentication
- POST `/api/v1/auth/register` - Register user
- POST `/api/v1/auth/login` - User login
- POST `/api/v1/auth/logout` - User logout

### Users
- GET `/api/v1/users` - List users
- GET `/api/v1/users/{user_id}` - Get user details
- PUT `/api/v1/users/{user_id}` - Update user
- DELETE `/api/v1/users/{user_id}` - Delete user

### Devices
- POST `/api/v1/devices/register` - Register device
- GET `/api/v1/devices/user/{user_id}` - Get user's devices
- GET `/api/v1/devices/status` - Get device status
- POST `/api/v1/devices/heartbeat` - Device heartbeat
- PUT `/api/v1/devices/config` - Update device config

### Telemetry
- POST `/api/v1/telemetry` - Submit telemetry data
- GET `/api/v1/telemetry/{device_id}` - Get device telemetry
- GET `/api/v1/telemetry/{device_id}/latest` - Get latest telemetry
- GET `/api/v1/telemetry/{device_id}/aggregated` - Get aggregated data

### Charts ✨ NEW
- POST `/api/v1/charts` - Create chart
- GET `/api/v1/charts` - List charts
- GET `/api/v1/charts/{chart_id}` - Get chart details
- PUT `/api/v1/charts/{chart_id}` - Update chart
- DELETE `/api/v1/charts/{chart_id}` - Delete chart
- GET `/api/v1/charts/{chart_id}/data` - Get chart data
- POST `/api/v1/charts/{chart_id}/devices` - Add device to chart
- DELETE `/api/v1/charts/{chart_id}/devices/{device_id}` - Remove device
- POST `/api/v1/charts/{chart_id}/measurements` - Add measurement
- DELETE `/api/v1/charts/{chart_id}/measurements/{measurement_id}` - Remove measurement

### Admin
- GET `/api/v1/admin/devices` - List all devices
- GET `/api/v1/admin/devices/{device_id}` - Get device details
- PUT `/api/v1/admin/devices/{device_id}/status` - Update device status
- DELETE `/api/v1/admin/devices/{device_id}` - Delete device
- GET `/api/v1/admin/stats` - Get system statistics

## 🧪 Testing

### Run All Tests
```bash
poetry run pytest tests/ -v
```

### Run Specific Test Suite
```bash
poetry run pytest tests/test_charts_api.py -v
```

### Test Coverage
- **148 tests** total
- **21 chart tests** ✨ NEW
- All tests passing ✅

## 🚀 Quick Start

### 1. Install Dependencies
```bash
poetry install
```

### 2. Setup Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Initialize Database
```bash
poetry run python init_db.py
```

### 5. Run Application
```bash
poetry run python app.py
```

### 6. Access API
- **API**: http://localhost:5000
- **Swagger UI**: http://localhost:5000/docs
- **Health Check**: http://localhost:5000/health

## 📊 Next Steps: Frontend Dashboard

The backend is complete! Next steps:

1. **Review Requirements**: `.kiro/specs/iot-dashboard-frontend/requirements.md`
2. **Create Design Document**: Define frontend architecture
3. **Build Frontend**: React/Vue/HTML dashboard
4. **Integrate APIs**: Connect to Charts API and Device API

## 🔧 Development Tools

- **Poetry**: Dependency management
- **Flask**: Web framework
- **SQLAlchemy**: ORM
- **PostgreSQL**: Production database
- **SQLite**: Development database
- **Pytest**: Testing framework
- **Docker**: Containerization
- **Swagger/OpenAPI**: API documentation

## 📝 Key Files

- **app.py** - Flask application entry point
- **init_db.py** - Database initialization
- **docker-compose.yml** - Service orchestration
- **.env** - Environment configuration
- **pyproject.toml** - Python dependencies
- **README.md** - Main documentation

## 🗂️ Archived Files

Historical documentation and TDD summaries have been moved to `docs/archive/` for reference but are not needed for active development.

---

**Last Updated**: November 22, 2025
**Status**: Backend Complete ✅ | Frontend Ready to Build 🚀
