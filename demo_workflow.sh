#!/bin/bash

# IoT Dashboard Complete Workflow Demo Script
# ============================================
# This script demonstrates the complete workflow using curl commands

set -e  # Exit on error

# Configuration
BASE_URL="http://localhost:5000"
API_BASE="${BASE_URL}/api/v1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_section() {
    echo ""
    echo "============================================================"
    echo "  $1"
    echo "============================================================"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Generate unique identifiers
TIMESTAMP=$(date +%s)
USERNAME="demo_user_${TIMESTAMP}"
EMAIL="demo_${TIMESTAMP}@example.com"
PASSWORD="SecurePassword123!"

# Variables to store data
USER_ID=""
AUTH_TOKEN=""
DEVICE1_ID=""
DEVICE1_API_KEY=""
DEVICE2_ID=""
DEVICE2_API_KEY=""
CHART1_ID=""
CHART2_ID=""

# Step 1: Register User
print_section "STEP 1: User Registration"
print_info "Registering user: ${USERNAME}"

REGISTER_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"${USERNAME}\",
    \"email\": \"${EMAIL}\",
    \"password\": \"${PASSWORD}\"
  }")

USER_ID=$(echo $REGISTER_RESPONSE | grep -o '"user_id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$USER_ID" ]; then
    print_success "User registered successfully!"
    print_info "User ID: ${USER_ID}"
else
    print_error "User registration failed!"
    echo $REGISTER_RESPONSE
    exit 1
fi

sleep 1

# Step 2: Login User
print_section "STEP 2: User Login"
print_info "Logging in as: ${USERNAME}"

LOGIN_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"${USERNAME}\",
    \"password\": \"${PASSWORD}\"
  }")

AUTH_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$AUTH_TOKEN" ]; then
    print_success "Login successful!"
    print_info "Auth token: ${AUTH_TOKEN:0:20}..."
else
    print_error "Login failed!"
    echo $LOGIN_RESPONSE
    exit 1
fi

sleep 1

# Step 3: Register Devices
print_section "STEP 3: Device Registration"

# Device 1: Living Room Sensor
print_info "Registering Device 1: Living Room Sensor"

DEVICE1_RESPONSE=$(curl -s -X POST "${API_BASE}/devices/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Living Room Sensor",
    "description": "Temperature and humidity sensor in living room",
    "device_type": "sensor",
    "location": "Living Room",
    "firmware_version": "1.0.0",
    "hardware_version": "v2.1"
  }')

DEVICE1_ID=$(echo $DEVICE1_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
DEVICE1_API_KEY=$(echo $DEVICE1_RESPONSE | grep -o '"api_key":"[^"]*"' | cut -d'"' -f4)

if [ -n "$DEVICE1_ID" ]; then
    print_success "Device 1 registered successfully!"
    print_info "  Device ID: ${DEVICE1_ID}"
    print_info "  API Key: ${DEVICE1_API_KEY:0:20}..."
else
    print_error "Device 1 registration failed!"
    exit 1
fi

# Device 2: Bedroom Sensor
print_info "Registering Device 2: Bedroom Sensor"

DEVICE2_RESPONSE=$(curl -s -X POST "${API_BASE}/devices/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bedroom Sensor",
    "description": "Environmental sensor in bedroom",
    "device_type": "sensor",
    "location": "Bedroom",
    "firmware_version": "1.0.0",
    "hardware_version": "v2.1"
  }')

DEVICE2_ID=$(echo $DEVICE2_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
DEVICE2_API_KEY=$(echo $DEVICE2_RESPONSE | grep -o '"api_key":"[^"]*"' | cut -d'"' -f4)

if [ -n "$DEVICE2_ID" ]; then
    print_success "Device 2 registered successfully!"
    print_info "  Device ID: ${DEVICE2_ID}"
    print_info "  API Key: ${DEVICE2_API_KEY:0:20}..."
else
    print_error "Device 2 registration failed!"
    exit 1
fi

sleep 1

# Step 4: Submit Telemetry Data
print_section "STEP 4: Submit Telemetry Data"

print_info "Submitting 10 telemetry readings for Device 1 (Living Room)..."
for i in {1..10}; do
    TEMP=$(awk -v min=18 -v max=23 'BEGIN{srand(); print min+rand()*(max-min)}')
    HUMIDITY=$(awk -v min=40 -v max=50 'BEGIN{srand(); print min+rand()*(max-min)}')
    PRESSURE=$(awk -v min=1003 -v max=1023 'BEGIN{srand(); print min+rand()*(max-min)}')
    BATTERY=$(awk -v i=$i 'BEGIN{print 100-(i*2)}')
    
    curl -s -X POST "${API_BASE}/telemetry" \
      -H "Content-Type: application/json" \
      -H "X-API-Key: ${DEVICE1_API_KEY}" \
      -d "{
        \"data\": {
          \"temperature\": ${TEMP},
          \"humidity\": ${HUMIDITY},
          \"pressure\": ${PRESSURE},
          \"battery\": ${BATTERY}
        }
      }" > /dev/null
    
    sleep 0.1
done
print_success "10 readings submitted for Device 1"

print_info "Submitting 10 telemetry readings for Device 2 (Bedroom)..."
for i in {1..10}; do
    TEMP=$(awk -v min=16 -v max=21 'BEGIN{srand(); print min+rand()*(max-min)}')
    HUMIDITY=$(awk -v min=45 -v max=55 'BEGIN{srand(); print min+rand()*(max-min)}')
    PRESSURE=$(awk -v min=1003 -v max=1023 'BEGIN{srand(); print min+rand()*(max-min)}')
    BATTERY=$(awk -v i=$i 'BEGIN{print 100-(i*2)}')
    
    curl -s -X POST "${API_BASE}/telemetry" \
      -H "Content-Type: application/json" \
      -H "X-API-Key: ${DEVICE2_API_KEY}" \
      -d "{
        \"data\": {
          \"temperature\": ${TEMP},
          \"humidity\": ${HUMIDITY},
          \"pressure\": ${PRESSURE},
          \"battery\": ${BATTERY}
        }
      }" > /dev/null
    
    sleep 0.1
done
print_success "10 readings submitted for Device 2"

sleep 1

# Step 5: Create Charts
print_section "STEP 5: Create Custom Charts"

# Chart 1: Temperature Comparison
print_info "Creating Chart 1: Temperature Comparison"

CHART1_RESPONSE=$(curl -s -X POST "${API_BASE}/charts" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Temperature Comparison\",
    \"title\": \"Living Room vs Bedroom Temperature\",
    \"description\": \"Compare temperature readings from both sensors\",
    \"type\": \"line\",
    \"user_id\": \"${USER_ID}\",
    \"time_range\": \"1h\",
    \"refresh_interval\": 30
  }")

CHART1_ID=$(echo $CHART1_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -n "$CHART1_ID" ]; then
    print_success "Chart 1 created successfully!"
    print_info "  Chart ID: ${CHART1_ID}"
    
    # Add devices to chart 1
    curl -s -X POST "${API_BASE}/charts/${CHART1_ID}/devices" \
      -H "Content-Type: application/json" \
      -d "{\"device_id\": ${DEVICE1_ID}}" > /dev/null
    print_success "  Added Device 1 to Chart 1"
    
    curl -s -X POST "${API_BASE}/charts/${CHART1_ID}/devices" \
      -H "Content-Type: application/json" \
      -d "{\"device_id\": ${DEVICE2_ID}}" > /dev/null
    print_success "  Added Device 2 to Chart 1"
    
    # Add temperature measurement with red color
    curl -s -X POST "${API_BASE}/charts/${CHART1_ID}/measurements" \
      -H "Content-Type: application/json" \
      -d '{
        "measurement_name": "temperature",
        "display_name": "Temperature (°C)",
        "color": "#FF6384"
      }' > /dev/null
    print_success "  Added Temperature measurement (Red: #FF6384)"
else
    print_error "Chart 1 creation failed!"
fi

# Chart 2: Multi-Sensor Dashboard
print_info "Creating Chart 2: Living Room Multi-Sensor Dashboard"

CHART2_RESPONSE=$(curl -s -X POST "${API_BASE}/charts" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Living Room Dashboard\",
    \"title\": \"Living Room Environmental Monitoring\",
    \"description\": \"Temperature, Humidity, and Pressure in Living Room\",
    \"type\": \"line\",
    \"user_id\": \"${USER_ID}\",
    \"time_range\": \"1h\",
    \"refresh_interval\": 30
  }")

CHART2_ID=$(echo $CHART2_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -n "$CHART2_ID" ]; then
    print_success "Chart 2 created successfully!"
    print_info "  Chart ID: ${CHART2_ID}"
    
    # Add only Device 1 (Living Room)
    curl -s -X POST "${API_BASE}/charts/${CHART2_ID}/devices" \
      -H "Content-Type: application/json" \
      -d "{\"device_id\": ${DEVICE1_ID}}" > /dev/null
    print_success "  Added Device 1 to Chart 2"
    
    # Add multiple measurements with different colors
    curl -s -X POST "${API_BASE}/charts/${CHART2_ID}/measurements" \
      -H "Content-Type: application/json" \
      -d '{
        "measurement_name": "temperature",
        "display_name": "Temperature (°C)",
        "color": "#FF6384"
      }' > /dev/null
    print_success "  Added Temperature (Red: #FF6384)"
    
    curl -s -X POST "${API_BASE}/charts/${CHART2_ID}/measurements" \
      -H "Content-Type: application/json" \
      -d '{
        "measurement_name": "humidity",
        "display_name": "Humidity (%)",
        "color": "#36A2EB"
      }' > /dev/null
    print_success "  Added Humidity (Blue: #36A2EB)"
    
    curl -s -X POST "${API_BASE}/charts/${CHART2_ID}/measurements" \
      -H "Content-Type: application/json" \
      -d '{
        "measurement_name": "pressure",
        "display_name": "Pressure (hPa)",
        "color": "#FFCE56"
      }' > /dev/null
    print_success "  Added Pressure (Yellow: #FFCE56)"
else
    print_error "Chart 2 creation failed!"
fi

sleep 1

# Step 6: Retrieve Chart Data
print_section "STEP 6: Retrieve Chart Data"

print_info "Retrieving data for Chart 1: Temperature Comparison"
CHART1_DATA=$(curl -s "${API_BASE}/charts/${CHART1_ID}/data")
CHART1_COUNT=$(echo $CHART1_DATA | grep -o '"count":[0-9]*' | cut -d':' -f2)
print_success "Chart 1 data retrieved: ${CHART1_COUNT} data points"

print_info "Retrieving data for Chart 2: Living Room Dashboard"
CHART2_DATA=$(curl -s "${API_BASE}/charts/${CHART2_ID}/data")
CHART2_COUNT=$(echo $CHART2_DATA | grep -o '"count":[0-9]*' | cut -d':' -f2)
print_success "Chart 2 data retrieved: ${CHART2_COUNT} data points"

# Step 7: Display Summary
print_section "DEMO SUMMARY"

echo ""
echo "📊 Demo Completed Successfully!"
echo ""
echo "User Information:"
echo "  Username: ${USERNAME}"
echo "  Email: ${EMAIL}"
echo "  User ID: ${USER_ID}"
echo ""
echo "Devices Registered: 2"
echo "  - Living Room Sensor (ID: ${DEVICE1_ID})"
echo "  - Bedroom Sensor (ID: ${DEVICE2_ID})"
echo ""
echo "Telemetry Data:"
echo "  Total Readings: 20 (10 per device)"
echo ""
echo "Charts Created: 2"
echo "  - Temperature Comparison (ID: ${CHART1_ID})"
echo "  - Living Room Dashboard (ID: ${CHART2_ID})"
echo ""
echo "🌐 Access Points:"
echo "  API Base: ${API_BASE}"
echo "  Swagger UI: ${BASE_URL}/docs"
echo "  Health Check: ${BASE_URL}/health"
echo ""
echo "📝 Test the APIs:"
echo "  # Get Chart 1 data"
echo "  curl ${API_BASE}/charts/${CHART1_ID}/data | python -m json.tool"
echo ""
echo "  # Get Chart 2 data"
echo "  curl ${API_BASE}/charts/${CHART2_ID}/data | python -m json.tool"
echo ""
echo "  # List all user's charts"
echo "  curl \"${API_BASE}/charts?user_id=${USER_ID}\" | python -m json.tool"
echo ""
echo "============================================================"
