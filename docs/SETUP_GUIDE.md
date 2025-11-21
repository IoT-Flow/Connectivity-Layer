# 📖 IoTFlow Complete Setup Guide

Visual step-by-step guide with diagrams and troubleshooting.

---

## 🎯 Setup Flow Diagram

```mermaid
graph TB
    START[Start Setup] --> CHECK{Prerequisites<br/>Installed?}
    CHECK -->|No| INSTALL[Install Prerequisites]
    CHECK -->|Yes| CLONE[Clone Repository]
    INSTALL --> CLONE
    
    CLONE --> ENV[Configure .env File]
    ENV --> DOCKER[Start Docker Services]
    DOCKER --> WAIT[Wait for Services]
    WAIT --> INIT[Initialize Database]
    INIT --> VERIFY[Verify Installation]
    
    VERIFY --> TEST{All Tests<br/>Pass?}
    TEST -->|Yes| SUCCESS[✅ Setup Complete]
    TEST -->|No| DEBUG[Debug Issues]
    DEBUG --> VERIFY
    
    SUCCESS --> NEXT[Next Steps]
    
    style START fill:#90EE90
    style SUCCESS fill:#32CD32,stroke:#000,stroke-width:3px
    style DEBUG fill:#FFD700
    style TEST fill:#87CEEB
```

---

## 📦 Installation Steps

### Step 1: Install Prerequisites

```mermaid
graph LR
    subgraph "Required Software"
        A[Docker 20.10+]
        B[Python 3.10+]
        C[Poetry 1.5+]
        D[Git 2.0+]
    end
    
    subgraph "Verification"
        V1[docker --version]
        V2[python --version]
        V3[poetry --version]
        V4[git --version]
    end
    
    A --> V1
    B --> V2
    C --> V3
    D --> V4
    
    style A fill:#2496ED,color:#fff
    style B fill:#3776AB,color:#fff
    style C fill:#60A5FA,color:#fff
    style D fill:#F05032,color:#fff
```

#### Installation Commands

**Docker (Ubuntu/Debian):**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

**Python:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3-pip

# macOS (using Homebrew)
brew install python@3.10

# Verify
python3 --version
```

**Poetry:**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Verify
poetry --version
```

---

### Step 2: Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd IoTFlow_ConnectivityLayer

# Make management script executable
chmod +x docker-manage.sh

# Copy environment template
cp .env.example .env

# Edit configuration (optional)
nano .env
```

#### Environment Configuration

```mermaid
graph TB
    subgraph "Environment Variables"
        DB[Database Settings]
        MQTT[MQTT Configuration]
        FLASK[Flask Settings]
        SEC[Security Settings]
    end
    
    subgraph "Default Values"
        DB --> DB1[PostgreSQL: localhost:5432]
        MQTT --> MQTT1[Broker: localhost:1883]
        FLASK --> FLASK1[Port: 5000]
        SEC --> SEC1[Admin Token: test]
    end
    
    style DB fill:#4169E1,color:#fff
    style MQTT fill:#FF6B6B
    style FLASK fill:#90EE90
    style SEC fill:#FFD700
```

**Key Environment Variables:**

```bash
# Database
DATABASE_URL=postgresql://iotflow:iotflowpass@postgres:5432/iotflow

# MQTT
MQTT_HOST=localhost
MQTT_PORT=1883

# Flask
FLASK_ENV=development
PORT=5000

# Security
IOTFLOW_ADMIN_TOKEN=test
```

---

### Step 3: Start Services

```mermaid
sequenceDiagram
    participant User
    participant Script as docker-manage.sh
    participant Docker
    participant Services
    
    User->>Script: ./docker-manage.sh start-all
    Script->>Docker: Check Docker running
    Docker-->>Script: ✓ Docker OK
    
    Script->>Docker: docker compose up -d
    Docker->>Services: Start PostgreSQL
    Docker->>Services: Start Redis
    Docker->>Services: Start MQTT
    Docker->>Services: Start Prometheus
    Docker->>Services: Start Grafana
    Docker->>Services: Start Flask App
    
    Services-->>Docker: All services started
    Docker-->>Script: ✓ Services running
    
    Script->>Services: Health checks
    Services-->>Script: ✓ All healthy
    
    Script-->>User: ✅ Setup complete
```

**Command:**
```bash
./docker-manage.sh start-all
```

**Expected Output:**
```
[INFO] Docker is running
[INFO] Docker Compose is available
[STEP] Starting all services (Redis, PostgreSQL, MQTT)...
[STEP] Waiting for services to be ready...
[INFO] PostgreSQL is ready
[INFO] Redis is ready
[INFO] MQTT broker is running
[INFO] All services are ready!
```

---

### Step 4: Initialize Application

```mermaid
graph TB
    START[Initialize App] --> DEPS[Install Dependencies]
    DEPS --> DB[Create Database Tables]
    DB --> ADMIN[Create Admin User]
    ADMIN --> VERIFY[Verify Setup]
    
    subgraph "Database Tables Created"
        T1[users]
        T2[devices]
        T3[device_auth]
        T4[device_configurations]
        T5[device_control]
        T6[charts]
        T7[chart_devices]
        T8[chart_measurements]
    end
    
    DB --> T1
    DB --> T2
    DB --> T3
    DB --> T4
    DB --> T5
    DB --> T6
    DB --> T7
    DB --> T8
    
    style START fill:#90EE90
    style VERIFY fill:#32CD32,color:#fff
```

**Command:**
```bash
./docker-manage.sh init-app
```

**What happens:**
1. ✅ Poetry installs Python dependencies
2. ✅ Creates PostgreSQL database tables
3. ✅ Creates admin user (username: `admin`, password: `admin123`)
4. ✅ Sets up initial configuration

---

### Step 5: Verify Installation

```mermaid
graph LR
    subgraph "Verification Tests"
        T1[Health Check]
        T2[Service Status]
        T3[Database Connection]
        T4[MQTT Connection]
        T5[API Test]
    end
    
    T1 -->|Pass| SUCCESS[✅ All Tests Pass]
    T2 -->|Pass| SUCCESS
    T3 -->|Pass| SUCCESS
    T4 -->|Pass| SUCCESS
    T5 -->|Pass| SUCCESS
    
    T1 -->|Fail| DEBUG[Debug Issues]
    T2 -->|Fail| DEBUG
    T3 -->|Fail| DEBUG
    T4 -->|Fail| DEBUG
    T5 -->|Fail| DEBUG
    
    style SUCCESS fill:#32CD32,color:#fff
    style DEBUG fill:#FF6B6B,color:#fff
```

**Verification Commands:**

```bash
# 1. Check service status
./docker-manage.sh status

# 2. Health check
curl http://localhost:5000/health

# 3. Detailed health check
curl http://localhost:5000/health?detailed=true

# 4. Test database connection
docker exec -it iotflow_postgres psql -U iotflow -d iotflow -c "SELECT 1;"

# 5. Test Redis connection
docker exec -it iotflow_redis redis-cli ping

# 6. Test MQTT broker
mosquitto_pub -h localhost -p 1883 -t "test/topic" -m "test"
```

---

## 🧪 Testing the Setup

### Test Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant API as Flask API
    participant DB as PostgreSQL
    participant MQTT as MQTT Broker
    participant Device as Simulator
    
    User->>API: Register Device
    API->>DB: Store Device
    DB-->>API: Device + API Key
    API-->>User: API Key
    
    User->>Device: Start Simulator
    Device->>MQTT: Connect
    MQTT-->>Device: Connected
    
    Device->>MQTT: Publish Telemetry
    MQTT->>API: Forward Message
    API->>DB: Store Telemetry
    DB-->>API: Stored
    API-->>Device: ACK
    
    User->>API: Query Telemetry
    API->>DB: Fetch Data
    DB-->>API: Telemetry Data
    API-->>User: JSON Response
```

### 1. Register a Test Device

```bash
curl -X POST http://localhost:5000/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TestSensor001",
    "device_type": "sensor",
    "user_id": "dcf1a",
    "description": "Temperature and humidity sensor",
    "location": "Lab Room 1"
  }'
```

**Expected Response:**
```json
{
  "message": "Device registered successfully",
  "device": {
    "id": 1,
    "name": "TestSensor001",
    "api_key": "abc123xyz789...",
    "status": "active",
    "device_type": "sensor"
  }
}
```

### 2. Submit Telemetry Data

```bash
# Save the API key from previous step
API_KEY="your_api_key_here"

curl -X POST http://localhost:5000/api/v1/devices/telemetry \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "temperature": 23.5,
      "humidity": 65.2,
      "pressure": 1013.25,
      "battery": 87
    },
    "metadata": {
      "location": "Lab Room 1",
      "sensor_status": "active"
    }
  }'
```

### 3. Query Telemetry Data

```bash
# Get latest telemetry
curl -H "X-API-Key: $API_KEY" \
  "http://localhost:5000/api/v1/devices/telemetry?limit=10"

# Get device status
curl -H "X-API-Key: $API_KEY" \
  "http://localhost:5000/api/v1/devices/status"
```

### 4. Run Device Simulator

```bash
# Basic simulator (5 minutes)
poetry run python simulators/new_mqtt_device_simulator.py \
  --name SimulatedDevice \
  --duration 300

# High-frequency sensor
poetry run python simulators/new_mqtt_device_simulator.py \
  --name HighFreqSensor \
  --profile high_frequency \
  --duration 600
```

---

## 🔍 Service Architecture

```mermaid
graph TB
    subgraph "External Access"
        USER[Users/Devices]
        WEB[Web Browser]
    end
    
    subgraph "Application Layer - Port 5000"
        FLASK[Flask Application<br/>Gunicorn Workers]
    end
    
    subgraph "Message Broker - Port 1883"
        MQTT[MQTT Broker<br/>Mosquitto]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Port 5432)]
        REDIS[(Redis<br/>Port 6379)]
    end
    
    subgraph "Monitoring - Ports 9090, 3333"
        PROM[Prometheus]
        GRAF[Grafana]
    end
    
    USER -->|HTTP/REST| FLASK
    USER -->|MQTT| MQTT
    WEB -->|HTTP| GRAF
    
    FLASK --> PG
    FLASK --> REDIS
    FLASK --> MQTT
    FLASK --> PROM
    
    PROM --> GRAF
    
    style FLASK fill:#90EE90
    style MQTT fill:#FF6B6B
    style PG fill:#4169E1,color:#fff
    style REDIS fill:#DC143C,color:#fff
    style GRAF fill:#F46800,color:#fff
```

---

## 🐛 Troubleshooting Guide

### Common Issues and Solutions

```mermaid
graph TB
    ISSUE{Issue Type?}
    
    ISSUE -->|Docker| D1[Docker not running]
    ISSUE -->|Port| P1[Port already in use]
    ISSUE -->|Database| DB1[Connection failed]
    ISSUE -->|MQTT| M1[MQTT connection failed]
    ISSUE -->|Poetry| PO1[Poetry not found]
    
    D1 --> D2[Start Docker Desktop]
    P1 --> P2[Change port in .env]
    DB1 --> DB2[Check PostgreSQL logs]
    M1 --> M2[Restart MQTT broker]
    PO1 --> PO2[Install Poetry]
    
    D2 --> FIX[✅ Fixed]
    P2 --> FIX
    DB2 --> FIX
    M2 --> FIX
    PO2 --> FIX
    
    style ISSUE fill:#FFD700
    style FIX fill:#32CD32,color:#fff
```

### Issue 1: Docker Services Won't Start

**Symptoms:**
- Services fail to start
- Port conflicts
- Container exits immediately

**Solutions:**
```bash
# Check Docker is running
docker info

# Check for port conflicts
sudo lsof -i :5432  # PostgreSQL
sudo lsof -i :6379  # Redis
sudo lsof -i :1883  # MQTT
sudo lsof -i :5000  # Flask

# Clean up and restart
docker compose down -v
./docker-manage.sh start-all

# View logs for specific service
docker logs iotflow_postgres
docker logs iotflow_mosquitto
```

### Issue 2: Database Connection Errors

**Symptoms:**
- "Connection refused"
- "Database does not exist"
- "Authentication failed"

**Solutions:**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# View PostgreSQL logs
docker logs iotflow_postgres

# Test connection
docker exec -it iotflow_postgres psql -U iotflow -d iotflow

# Reinitialize database
poetry run python init_db.py

# Check environment variables
cat .env | grep DATABASE_URL
```

### Issue 3: MQTT Connection Failures

**Symptoms:**
- Devices can't connect
- Messages not received
- Authentication errors

**Solutions:**
```bash
# Check MQTT broker status
docker ps | grep mosquitto

# View MQTT logs
docker logs iotflow_mosquitto

# Test MQTT connection
mosquitto_pub -h localhost -p 1883 -t "test/topic" -m "test"

# Restart MQTT broker
docker restart iotflow_mosquitto

# Check MQTT configuration
cat mqtt/config/mosquitto.conf
```

### Issue 4: Poetry/Python Issues

**Symptoms:**
- "poetry: command not found"
- Dependency installation fails
- Python version mismatch

**Solutions:**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Verify Python version
python3 --version  # Should be 3.10+

# Clear Poetry cache and reinstall
poetry cache clear . --all
poetry install

# Use specific Python version
poetry env use python3.10
```

### Issue 5: Port Already in Use

**Symptoms:**
- "Address already in use"
- Service fails to bind to port

**Solutions:**
```bash
# Find process using port
sudo lsof -i :5000

# Kill the process
kill -9 <PID>

# Or change port in .env
echo "PORT=5001" >> .env

# Restart services
./docker-manage.sh restart
```

---

## 📊 Monitoring and Dashboards

### Access Points

```mermaid
graph LR
    subgraph "Monitoring Stack"
        A[Prometheus<br/>:9090]
        B[Grafana<br/>:3333]
        C[Node Exporter<br/>:9100]
        D[Flask Metrics<br/>:5000/metrics]
    end
    
    D --> A
    C --> A
    A --> B
    
    style A fill:#E6522C,color:#fff
    style B fill:#F46800,color:#fff
    style C fill:#37D100,color:#fff
    style D fill:#90EE90
```

**URLs:**
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3333 (admin/admin)
- **Flask Metrics**: http://localhost:5000/metrics
- **Node Exporter**: http://localhost:9100/metrics

---

## 🎓 Next Steps

### Learning Path

```mermaid
graph TB
    START[Setup Complete] --> BASIC[Basic Operations]
    BASIC --> API[API Exploration]
    API --> SIM[Device Simulation]
    SIM --> MON[Monitoring Setup]
    MON --> ADV[Advanced Features]
    ADV --> PROD[Production Deployment]
    
    style START fill:#32CD32,color:#fff
    style PROD fill:#4169E1,color:#fff
```

### 1. Basic Operations
- Register devices
- Submit telemetry
- Query data
- Monitor device status

### 2. API Exploration
- Test all API endpoints
- Understand authentication
- Learn query parameters
- Handle errors

### 3. Device Simulation
- Run basic simulators
- Test different profiles
- Simulate device fleets
- Test failure scenarios

### 4. Monitoring Setup
- Configure Grafana dashboards
- Set up alerts
- Monitor system health
- Track metrics

### 5. Advanced Features
- Custom device types
- Complex queries
- Data aggregation
- MQTT commands

### 6. Production Deployment
- Security hardening
- TLS/SSL setup
- Backup strategies
- Scaling configuration

---

## 📚 Additional Resources

### Documentation
- **README.md** - Main documentation
- **QUICKSTART.md** - Quick reference
- **docs/** - Technical documentation
- **API Reference** - Complete API docs

### Scripts and Tools
- **docker-manage.sh** - Service management
- **manage.py** - Application management
- **simulators/** - Device simulators
- **tests/** - Test suites

### Configuration Files
- **.env** - Environment variables
- **docker-compose.yml** - Service definitions
- **pyproject.toml** - Python dependencies
- **mqtt/config/** - MQTT configuration

---

## ✅ Setup Checklist

- [ ] Docker installed and running
- [ ] Python 3.10+ installed
- [ ] Poetry installed
- [ ] Repository cloned
- [ ] .env file configured
- [ ] Docker services started
- [ ] Database initialized
- [ ] Health check passed
- [ ] Test device registered
- [ ] Telemetry data submitted
- [ ] Simulator tested
- [ ] Monitoring accessible

**All checked? You're ready to build! 🚀**

---

**Last Updated**: 2025-01-21  
**Version**: 0.2
