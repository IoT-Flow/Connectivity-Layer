# IoTFlow Quick Reference Guide

## Test Commands

```bash
# Run all tests
poetry run pytest tests/ -v

# Run user tests only
poetry run pytest tests/test_user.py -v

# Run specific test class
poetry run pytest tests/test_user.py::TestUserModel -v

# Run with coverage
poetry run pytest tests/ --cov=src --cov-report=html
```

## Application Commands

```bash
# Start application
poetry run python app.py

# Initialize database
poetry run python init_db.py

# Run migrations
poetry run flask db upgrade
```

## API Endpoints

### Health Check
```bash
GET /health
```

### User Management
```bash
POST   /api/v1/users              # Create user
GET    /api/v1/users              # List users
GET    /api/v1/users/:id          # Get user
PUT    /api/v1/users/:id          # Update user
DELETE /api/v1/users/:id          # Delete user
```

### Authentication
```bash
POST /api/v1/auth/login           # Login
POST /api/v1/auth/register        # Register
POST /api/v1/auth/logout          # Logout
```

### Devices
```bash
POST   /api/v1/devices/register   # Register device
GET    /api/v1/devices/:id        # Get device
POST   /api/v1/devices/heartbeat  # Device heartbeat
GET    /api/v1/devices/statuses   # List device statuses
```

### Telemetry
```bash
POST /api/v1/devices/telemetry    # Submit telemetry
GET  /api/v1/devices/telemetry    # Get telemetry
```

## Quick API Tests

### Create and Login User
```bash
# Create user
curl -X POST http://localhost:5000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","email":"demo@example.com","password":"demo123"}'

# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'
```

### Device Operations
```bash
# Register device
curl -X POST http://localhost:5000/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Device1","device_type":"sensor","user_id":"USER_ID"}'

# Send heartbeat
curl -X POST http://localhost:5000/api/v1/devices/heartbeat \
  -H "X-API-Key: DEVICE_API_KEY"

# Submit telemetry
curl -X POST http://localhost:5000/api/v1/devices/telemetry \
  -H "X-API-Key: DEVICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"data":{"temperature":25.5,"humidity":60}}'
```

## Test Status

| Feature | Tests | Status |
|---------|-------|--------|
| User Model | 8 | ✅ Passing |
| Password Management | 4 | ✅ Passing |
| User Routes | 10 | ✅ Passing |
| Authentication | 3 | ✅ Passing |
| **Total** | **25** | **✅ 100%** |

## Architecture

```
IoT Device/User → Flask API → PostgreSQL
```

**No Redis, No MQTT, No IoTDB** - Ultra-minimal architecture!

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main application |
| `src/models/__init__.py` | Database models |
| `src/routes/users.py` | User management routes |
| `src/routes/auth.py` | Authentication routes |
| `src/routes/devices.py` | Device routes |
| `tests/test_user.py` | User tests |

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/iotflow

# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Admin
IOTFLOW_ADMIN_TOKEN=your-admin-token
```

## Common Issues

### Port Already in Use
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

### Database Connection Error
```bash
# Check PostgreSQL is running
docker-compose up postgres -d

# Or use SQLite for testing
export DATABASE_URL=sqlite:///instance/iotflow.db
```

### Import Errors
```bash
# Reinstall dependencies
poetry install
```

## Documentation

- `REDIS_REMOVAL_SUMMARY.md` - Redis removal details
- `USER_TDD_SUMMARY.md` - User management details
- `TDD_IMPLEMENTATION_COMPLETE.md` - Overall summary
- `QUICK_REFERENCE.md` - This file

## Support

For issues or questions:
1. Check test files for examples
2. Review documentation files
3. Check application logs
4. Run tests to verify setup

---

**Quick Start:**
```bash
poetry install
poetry run pytest tests/ -v
poetry run python app.py
curl http://localhost:5000/health
```
