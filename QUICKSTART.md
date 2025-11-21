# 🚀 IoTFlow Quick Start Guide

Complete guide to get IoTFlow up and running in minutes.

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

| Software | Version | Purpose | Installation |
|----------|---------|---------|--------------|
| **Docker** | 20.10+ | Container runtime | [Install Docker](https://docs.docker.com/get-docker/) |
| **Docker Compose** | 2.0+ | Multi-container orchestration | Included with Docker Desktop |
| **Python** | 3.10+ | Application runtime | [Install Python](https://www.python.org/downloads/) |
| **Poetry** | 1.5+ | Python dependency management | [Install Poetry](https://python-poetry.org/docs/#installation) |
| **Git** | 2.0+ | Version control | [Install Git](https://git-scm.com/downloads) |

### Optional Tools

- **curl** - For testing API endpoints
- **mosquitto-clients** - For MQTT testing (`mosquitto_pub`, `mosquitto_sub`)
- **PostgreSQL client** - For database inspection (`psql`)

---

## 🎯 Quick Start (5 Minutes)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd IoTFlow_ConnectivityLayer
```

### Step 2: Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env if needed (optional for development)
nano .env
```

### Step 3: Start All Services

```bash
# Make the management script executable
chmod +x docker-manage.sh

# Start all Docker services (Redis, PostgreSQL, MQTT, Prometheus, Grafana)
./docker-manage.sh start-all
```

**This will start:**
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ MQTT Broker - Mosquitto (ports 1883, 9001, 8883)
- ✅ Prometheus (port 9090)
- ✅ Grafana (port 3333)
- ✅ Node Exporter (port 9100)
- ✅ Flask Application (port 5000)

### Step 4: Initialize the Application

```bash
# Install Python dependencies and initialize database
./docker-manage.sh init-app
```

**This will:**
- Install all Python dependencies via Poetry
- Create PostgreSQL database tables
- Create default admin user
- Set up initial configuration

### Step 5: Verify Installation

```bash
# Check service status
./docker-manage.sh status

# Test the API
curl http://localhost:5000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "message": "IoT Connectivity Layer is running",
  "version": "1.0.0"
}
```

---

## 🎮 Running the Application

### Option 1: Using Docker (Recommended for Production)

The Flask application is already running in Docker from Step 3.

```bash
# View application logs
docker logs -f iotflow_connectivity

# Restart application
docker restart iotflow_connectivity
```

### Option 2: Using Poetry (Development)

```bash
# Run Flask application locally
poetry run python app.py

# Or use the management script
./docker-manage.sh run
```

### Option 3: Using Gunicorn (Production)

```bash
# Run with Gunicorn (4 workers)
poetry run gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 🧪 Testing the Installation

### 1. Health Check

```bash
curl http://localhost:5000/health
```

### 2. Register a Test Device

```bash
curl -X POST http://localhost:5000/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TestDevice001",
    "device_type": "sensor",
    "user_id": "dcf1a",
    "description": "Test temperature sensor",
    "location": "Lab"
  }'
```

**Save the `api_key` from the response!**

### 3. Submit Telemetry Data

```bash
# Replace YOUR_API_KEY with the key from step 2
curl -X POST http://localhost:5000/api/v1/devices/telemetry \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "temperature": 23.5,
      "humidity": 65.2,
      "pressure": 1013.25
    }
  }'
```

### 4. Query Telemetry Data

```bash
# Get latest telemetry
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:5000/api/v1/devices/telemetry?limit=10
```

### 5. Run Device Simulator

```bash
# Run advanced MQTT device simulator
poetry run python simulators/new_mqtt_device_simulator.py \
  --name SimulatedDevice \
  --duration 300
```

---

## 📊 Access Web Interfaces

Once everything is running, you can access:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Flask API** | http://localhost:5000 | API Key authentication |
| **Prometheus** | http://localhost:9090 | No auth |
| **Grafana** | http://localhost:3333 | admin/admin (default) |
| **PostgreSQL** | localhost:5432 | iotflow/iotflowpass |

---

## 🔧 Common Management Commands

### Service Management

```bash
# Start all services
./docker-manage.sh start-all

# Stop all services
./docker-manage.sh stop

# Restart services
./docker-manage.sh restart

# Check service status
./docker-manage.sh status

# View logs (all services)
./docker-manage.sh logs

# View logs (specific service)
./docker-manage.sh logs postgres
./docker-manage.sh logs mosquitto
```

### Database Management

```bash
# Connect to PostgreSQL
docker exec -it iotflow_postgres psql -U iotflow -d iotflow

# Backup database
./docker-manage.sh backup

# Restore database
./docker-manage.sh restore backup_20250101_120000.db

# Connect to Redis CLI
./docker-manage.sh redis
```

### Application Management

```bash
# Initialize/reinitialize database
poetry run python init_db.py

# Create a test device
poetry run python manage.py create-device "MyDevice"

# Run tests
poetry run pytest tests/

# Run end-to-end tests
./docker-manage.sh test
```

---

## 🐛 Troubleshooting

### Issue: Docker services won't start

```bash
# Check Docker is running
docker info

# Check for port conflicts
sudo lsof -i :5432  # PostgreSQL
sudo lsof -i :6379  # Redis
sudo lsof -i :1883  # MQTT
sudo lsof -i :5000  # Flask

# Remove old containers and volumes
docker compose down -v
./docker-manage.sh start-all
```

### Issue: Poetry not found

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (Linux/Mac)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
poetry --version
```

### Issue: Database connection errors

```bash
# Check PostgreSQL is running
docker logs iotflow_postgres

# Verify connection
docker exec -it iotflow_postgres psql -U iotflow -d iotflow -c "SELECT 1;"

# Reinitialize database
poetry run python init_db.py
```

### Issue: MQTT connection failures

```bash
# Check MQTT broker logs
docker logs iotflow_mosquitto

# Test MQTT connection
mosquitto_pub -h localhost -p 1883 -t "test/topic" -m "test message"

# Restart MQTT broker
docker restart iotflow_mosquitto
```

### Issue: Port already in use

```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill the process
kill -9 <PID>

# Or change the port in .env
PORT=5001
```

---

## 📁 Project Structure

```
IoTFlow_ConnectivityLayer/
├── app.py                      # Flask application entry point
├── docker-compose.yml          # Docker services configuration
├── docker-manage.sh            # Management script
├── pyproject.toml              # Poetry dependencies
├── .env                        # Environment configuration
│
├── src/                        # Application source code
│   ├── config/                 # Configuration files
│   ├── models/                 # Database models
│   ├── routes/                 # API endpoints
│   ├── services/               # Business logic
│   ├── middleware/             # Auth, security, monitoring
│   ├── mqtt/                   # MQTT client
│   └── utils/                  # Utilities
│
├── simulators/                 # Device simulators
│   └── new_mqtt_device_simulator.py
│
├── tests/                      # Test suites
├── docs/                       # Documentation
├── mqtt/                       # MQTT broker config
├── instance/                   # Database files
└── logs/                       # Application logs
```

---

## 🔐 Default Credentials

### Admin User (Database)

- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@iotflow.local`

### PostgreSQL Database

- **Host**: `localhost` (or `postgres` in Docker)
- **Port**: `5432`
- **Database**: `iotflow`
- **Username**: `iotflow`
- **Password**: `iotflowpass`

### Admin API Token

- **Token**: `test` (set in `.env` as `IOTFLOW_ADMIN_TOKEN`)
- **Usage**: `Authorization: admin test`

### MQTT Broker

- **Host**: `localhost`
- **Port**: `1883` (MQTT), `9001` (WebSocket), `8883` (TLS)
- **Authentication**: Anonymous (API key validated server-side)

---

## 📚 Next Steps

### 1. Explore the API

- Read the [API Documentation](README.md#-api-endpoints)
- Test endpoints with Postman or curl
- Check out example requests in the README

### 2. Run Device Simulators

```bash
# Basic simulator
poetry run python simulators/new_mqtt_device_simulator.py --name Device1

# High-frequency sensor
poetry run python simulators/new_mqtt_device_simulator.py \
  --name HighFreqSensor \
  --profile high_frequency \
  --duration 600

# Industrial sensor
poetry run python simulators/new_mqtt_device_simulator.py \
  --name IndustrialSensor \
  --type industrial_sensor \
  --profile industrial
```

### 3. Set Up Monitoring

- Access Grafana at http://localhost:3333
- Import IoTFlow dashboards
- Configure alerts and notifications

### 4. Develop Custom Integrations

- Create custom device types
- Add new telemetry measurements
- Build custom dashboards
- Integrate with external systems

### 5. Deploy to Production

- Review [Production Deployment](README.md#-production-deployment)
- Configure TLS/SSL for MQTT
- Set up proper authentication
- Configure backup strategies
- Set up monitoring and alerting

---

## 🆘 Getting Help

### Documentation

- **README.md** - Comprehensive project documentation
- **docs/** - Detailed technical documentation
- **API Reference** - Complete API endpoint documentation

### Logs

```bash
# Application logs
tail -f logs/iotflow.log

# Docker service logs
docker logs -f iotflow_connectivity
docker logs -f iotflow_postgres
docker logs -f iotflow_mosquitto
```

### Health Checks

```bash
# Detailed health check
curl http://localhost:5000/health?detailed=true

# System status
curl http://localhost:5000/status

# Telemetry system status
curl http://localhost:5000/api/v1/telemetry/status

# MQTT status
curl http://localhost:5000/api/v1/mqtt/status
```

### Community

- **GitHub Issues** - Report bugs and request features
- **Documentation** - Check docs/ directory
- **Examples** - See simulators/ and tests/ directories

---

## 🎉 Success!

You now have a fully functional IoT platform running! 

**What you can do:**
- ✅ Register IoT devices
- ✅ Collect telemetry data via HTTP and MQTT
- ✅ Query historical data
- ✅ Monitor device status in real-time
- ✅ Visualize metrics in Grafana
- ✅ Simulate device fleets
- ✅ Manage devices via admin API

**Happy IoT building! 🚀**

---

## 📝 Quick Reference Card

```bash
# Essential Commands
./docker-manage.sh start-all    # Start everything
./docker-manage.sh init-app     # Initialize app
./docker-manage.sh run          # Run Flask app
./docker-manage.sh status       # Check status
./docker-manage.sh logs         # View logs
./docker-manage.sh stop         # Stop everything

# Testing
curl http://localhost:5000/health
poetry run python simulators/new_mqtt_device_simulator.py --name Test

# Database
docker exec -it iotflow_postgres psql -U iotflow -d iotflow
./docker-manage.sh redis

# Monitoring
http://localhost:9090  # Prometheus
http://localhost:3333  # Grafana
```

---

**Version**: 0.2  
**Last Updated**: 2025-01-21  
**License**: MIT
