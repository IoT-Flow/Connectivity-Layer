# IoT Dashboard Demo Guide

## Overview

This guide provides demo scripts that showcase the complete IoT Dashboard workflow from user registration to chart visualization.

## Demo Scripts

### 1. Python Demo Script (Recommended)
**File:** `demo_complete_workflow.py`

A comprehensive Python script with detailed output and error handling.

**Features:**
- ✅ Interactive step-by-step execution
- ✅ Colored output for better readability
- ✅ Detailed progress information
- ✅ Error handling and validation
- ✅ Summary report at the end

**Usage:**
```bash
# Make sure the Flask app is running first
python app.py

# In another terminal, run the demo
python demo_complete_workflow.py
```

### 2. Bash Demo Script
**File:** `demo_workflow.sh`

A shell script version using curl commands.

**Features:**
- ✅ Fast execution
- ✅ Pure bash/curl implementation
- ✅ Easy to modify and customize
- ✅ Works on any Unix-like system

**Usage:**
```bash
# Make sure the Flask app is running first
python app.py

# In another terminal, run the demo
./demo_workflow.sh
```

## What the Demo Does

### Step 1: User Registration
- Creates a new user account
- Generates unique username and email
- Returns user ID for subsequent operations

### Step 2: User Login
- Authenticates the user
- Receives authentication token
- Token used for authorized requests

### Step 3: Device Registration
- Registers 2 IoT devices:
  - **Living Room Sensor** - Temperature, humidity, pressure monitoring
  - **Bedroom Sensor** - Environmental monitoring
- Each device receives a unique API key

### Step 4: Submit Telemetry Data
- Submits **10 telemetry readings** per device (20 total)
- Each reading includes:
  - Temperature (°C)
  - Humidity (%)
  - Pressure (hPa)
  - Battery level (%)
- Realistic sensor data with variations

### Step 5: Create Custom Charts

#### Chart 1: Temperature Comparison
- **Type:** Line chart
- **Devices:** Both Living Room and Bedroom sensors
- **Measurements:** Temperature only
- **Color:** Red (#FF6384)
- **Purpose:** Compare temperature between rooms

#### Chart 2: Living Room Multi-Sensor Dashboard
- **Type:** Line chart
- **Devices:** Living Room sensor only
- **Measurements:** 
  - Temperature - Red (#FF6384)
  - Humidity - Blue (#36A2EB)
  - Pressure - Yellow (#FFCE56)
- **Purpose:** Monitor all environmental factors in one room

### Step 6: Retrieve Chart Data
- Fetches data for both charts
- Displays data point counts
- Shows series information with colors

### Step 7: Summary Report
- Complete overview of created resources
- API endpoints for testing
- Next steps and suggestions

## Prerequisites

### 1. Start the Flask Application
```bash
# Option 1: Direct Python
python app.py

# Option 2: Using Poetry
poetry run python app.py

# Option 3: Using Docker
docker-compose up
```

### 2. Verify Server is Running
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-22T02:00:00Z"
}
```

## Running the Demo

### Python Demo (Detailed)

```bash
# Install dependencies if needed
pip install requests

# Run the demo
python demo_complete_workflow.py
```

**Expected Output:**
```
============================================================
  IoT Dashboard Complete Workflow Demo
============================================================

This demo will:
  1. Register a new user
  2. Login the user
  3. Register 2 IoT devices
  4. Submit 10 telemetry readings per device
  5. Create 2 custom charts with different colors
  6. Retrieve and display chart data

============================================================

Press Enter to start the demo...

============================================================
  STEP 1: User Registration
============================================================
ℹ️  Registering user: demo_user_1732244400
✅ User registered successfully!
ℹ️  User ID: fd596e05a9374eeabbaf2779686b9f1b

...
```

### Bash Demo (Fast)

```bash
# Make executable (already done)
chmod +x demo_workflow.sh

# Run the demo
./demo_workflow.sh
```

## Verifying the Demo Results

### 1. Check Swagger UI
Open http://localhost:5000/docs and explore:
- User endpoints
- Device endpoints
- Telemetry endpoints
- Chart endpoints

### 2. Query the APIs

**List all charts:**
```bash
curl "http://localhost:5000/api/v1/charts" | python -m json.tool
```

**Get chart data:**
```bash
# Replace {chart_id} with actual ID from demo output
curl "http://localhost:5000/api/v1/charts/{chart_id}/data" | python -m json.tool
```

**List user's devices:**
```bash
# Replace {user_id} with actual ID from demo output
curl "http://localhost:5000/api/v1/devices/user/{user_id}" | python -m json.tool
```

**Get telemetry data:**
```bash
# Replace {device_id} with actual ID from demo output
curl "http://localhost:5000/api/v1/telemetry/{device_id}" | python -m json.tool
```

### 3. Check Database

**SQLite:**
```bash
sqlite3 instance/iotflow.db

-- Check users
SELECT * FROM users ORDER BY created_at DESC LIMIT 1;

-- Check devices
SELECT * FROM devices ORDER BY created_at DESC LIMIT 2;

-- Check charts
SELECT * FROM charts ORDER BY created_at DESC LIMIT 2;

-- Check telemetry count
SELECT COUNT(*) FROM telemetry_data;
```

**PostgreSQL:**
```bash
psql -h localhost -U iotflow_user iotflow

-- Check users
SELECT * FROM users ORDER BY created_at DESC LIMIT 1;

-- Check devices
SELECT * FROM devices ORDER BY created_at DESC LIMIT 2;

-- Check charts
SELECT * FROM charts ORDER BY created_at DESC LIMIT 2;

-- Check telemetry count
SELECT COUNT(*) FROM telemetry_data;
```

## Demo Data Structure

### Created Resources

```
User
├── Username: demo_user_{timestamp}
├── Email: demo_{timestamp}@example.com
└── User ID: {uuid}

Devices (2)
├── Living Room Sensor
│   ├── Device ID: {id}
│   ├── API Key: {key}
│   └── Telemetry: 10 readings
│       ├── Temperature: 18-23°C
│       ├── Humidity: 40-50%
│       ├── Pressure: 1003-1023 hPa
│       └── Battery: 100-82%
│
└── Bedroom Sensor
    ├── Device ID: {id}
    ├── API Key: {key}
    └── Telemetry: 10 readings
        ├── Temperature: 16-21°C
        ├── Humidity: 45-55%
        ├── Pressure: 1003-1023 hPa
        └── Battery: 100-82%

Charts (2)
├── Temperature Comparison
│   ├── Chart ID: {uuid}
│   ├── Type: Line
│   ├── Devices: Both sensors
│   └── Measurements:
│       └── Temperature (Red: #FF6384)
│
└── Living Room Dashboard
    ├── Chart ID: {uuid}
    ├── Type: Line
    ├── Devices: Living Room sensor only
    └── Measurements:
        ├── Temperature (Red: #FF6384)
        ├── Humidity (Blue: #36A2EB)
        └── Pressure (Yellow: #FFCE56)
```

## Customizing the Demo

### Modify Number of Telemetry Readings

**Python:**
```python
# In demo_complete_workflow.py, line ~180
for i in range(10):  # Change 10 to desired number
```

**Bash:**
```bash
# In demo_workflow.sh, line ~150
for i in {1..10}; do  # Change 10 to desired number
```

### Add More Devices

**Python:**
```python
# In demo_complete_workflow.py, add to devices_to_register list
{
    "name": "Kitchen Sensor",
    "description": "Kitchen environmental sensor",
    "device_type": "sensor",
    "location": "Kitchen",
    "firmware_version": "1.0.0",
    "hardware_version": "v2.1"
}
```

### Change Chart Colors

**Python:**
```python
# In demo_complete_workflow.py, modify COLORS dictionary
COLORS = {
    'temperature': '#FF0000',  # Pure Red
    'humidity': '#0000FF',     # Pure Blue
    'pressure': '#00FF00',     # Pure Green
    'battery': '#FFA500',      # Orange
}
```

## Troubleshooting

### Error: Connection Refused
```
❌ Cannot connect to the API server!
```

**Solution:** Make sure Flask app is running:
```bash
python app.py
```

### Error: User Already Exists
The demo creates unique usernames using timestamps, but if you run it multiple times per second:

**Solution:** Wait a second and run again, or modify the username generation.

### Error: No Telemetry Data
If chart data shows 0 points:

**Solution:** 
1. Check if telemetry was submitted successfully
2. Verify device IDs match
3. Check time range in chart configuration

### Error: Chart Not Found
**Solution:** Verify chart was created successfully and use correct chart ID.

## Next Steps After Demo

### 1. Explore the APIs
- Open Swagger UI: http://localhost:5000/docs
- Try different endpoints
- Experiment with parameters

### 2. Build the Frontend
- Use the chart IDs from demo
- Fetch data using `/api/v1/charts/{chart_id}/data`
- Render charts with a library (Chart.js, Recharts, etc.)

### 3. Add More Features
- Create more chart types (bar, area, pie)
- Add more devices
- Experiment with different time ranges
- Try multi-device comparisons

### 4. Test Real Devices
- Use the device API keys
- Send real telemetry data
- Monitor in real-time

## Demo Script Comparison

| Feature | Python Script | Bash Script |
|---------|--------------|-------------|
| **Readability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Error Handling** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Speed** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Customization** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Dependencies** | Python + requests | bash + curl |
| **Best For** | Development, Learning | CI/CD, Quick Tests |

## Support

For issues or questions:
1. Check the main README.md
2. Review API_DOCUMENTATION_SUMMARY.md
3. Open Swagger UI for API reference
4. Check logs in `logs/` directory

---

**Demo Version:** 1.0.0
**Last Updated:** November 22, 2025
**Status:** Production Ready ✅
