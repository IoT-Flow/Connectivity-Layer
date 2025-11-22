# IoTFlow API Documentation

## Overview

The IoTFlow Connectivity Layer provides a RESTful API for managing IoT devices, collecting telemetry data, and visualizing data through charts.

**Base URL:** `http://localhost:5000` (development)

**API Version:** v1

## Interactive Documentation

Visit the interactive Swagger UI documentation at:
- **Swagger UI:** http://localhost:5000/docs
- **OpenAPI Spec:** http://localhost:5000/apispec.json

## Authentication

The API uses two authentication methods:

### 1. API Key Authentication (Devices)
Used by IoT devices to submit telemetry data.

**Header:** `X-API-Key: <device_api_key>`

```bash
curl -H "X-API-Key: your-device-api-key" \
  http://localhost:5000/api/v1/telemetry
```

### 2. JWT Bearer Token (Users)
Used by users for device management and admin operations.

**Header:** `Authorization: Bearer <jwt_token>`

```bash
curl -H "Authorization: Bearer your-jwt-token" \
  http://localhost:5000/api/v1/devices
```

## Quick Start

### 1. Register a User

```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password123"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "User registered successfully",
  "user": {
    "user_id": "fd596e05-a937-4eea-bbaf-2779686b9f1b",
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true,
    "is_admin": false
  }
}
```

### 2. Login

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password123"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "user_id": "fd596e05-a937-4eea-bbaf-2779686b9f1b",
    "username": "john_doe"
  }
}
```

### 3. Register a Device

```bash
curl -X POST http://localhost:5000/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Temperature Sensor 1",
    "device_type": "sensor",
    "user_id": "fd596e05-a937-4eea-bbaf-2779686b9f1b"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Device registered successfully",
  "device": {
    "id": 1,
    "api_key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "name": "Temperature Sensor 1",
    "device_type": "sensor",
    "status": "active"
  }
}
```

### 4. Submit Telemetry Data

```bash
curl -X POST http://localhost:5000/api/v1/telemetry \
  -H "Content-Type: application/json" \
  -H "X-API-Key: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6" \
  -d '{
    "measurements": [
      {
        "name": "temperature",
        "value": 25.5,
        "unit": "celsius"
      },
      {
        "name": "humidity",
        "value": 60,
        "unit": "percent"
      }
    ]
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Telemetry data stored successfully",
  "count": 2
}
```

### 5. Retrieve Telemetry Data

```bash
curl http://localhost:5000/api/v1/telemetry/device/1?limit=10
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "device_id": 1,
      "measurement_name": "temperature",
      "timestamp": "2025-11-22T00:00:00Z",
      "numeric_value": 25.5,
      "unit": "celsius"
    },
    {
      "device_id": 1,
      "measurement_name": "humidity",
      "timestamp": "2025-11-22T00:00:00Z",
      "numeric_value": 60,
      "unit": "percent"
    }
  ],
  "count": 2
}
```

## API Endpoints

### Health & Status

#### GET /health
Basic health check

**Query Parameters:**
- `detailed` (boolean): Return detailed health information

**Example:**
```bash
curl http://localhost:5000/health?detailed=true
```

#### GET /status
Detailed system status and metrics

---

### Authentication

#### POST /api/v1/auth/register
Register a new user

**Request Body:**
```json
{
  "username": "string (min 3 chars)",
  "email": "string (valid email)",
  "password": "string (min 6 chars)"
}
```

#### POST /api/v1/auth/login
User login

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

---

### Users

#### GET /api/v1/users
List all users (requires authentication)

#### GET /api/v1/users/{user_id}
Get user details

**Path Parameters:**
- `user_id` (string): User UUID

#### PUT /api/v1/users/{user_id}
Update user information

#### DELETE /api/v1/users/{user_id}
Delete user account

---

### Devices

#### POST /api/v1/devices/register
Register a new device

**Request Body:**
```json
{
  "name": "string",
  "device_type": "string",
  "user_id": "string (UUID)"
}
```

#### GET /api/v1/devices
List all devices

**Query Parameters:**
- `user_id` (string): Filter by user
- `status` (string): Filter by status (active, inactive, maintenance)
- `limit` (integer): Max results (default: 100)
- `offset` (integer): Pagination offset

#### GET /api/v1/devices/{device_id}
Get device details

#### PUT /api/v1/devices/{device_id}
Update device information

**Request Body:**
```json
{
  "name": "string",
  "status": "active|inactive|maintenance"
}
```

#### DELETE /api/v1/devices/{device_id}
Delete a device

#### GET /api/v1/devices/status
Get status of all devices

---

### Telemetry

#### POST /api/v1/telemetry
Submit telemetry data (requires API key)

**Headers:**
- `X-API-Key`: Device API key

**Request Body:**
```json
{
  "measurements": [
    {
      "name": "string",
      "value": "number|string",
      "unit": "string (optional)",
      "timestamp": "ISO 8601 datetime (optional)"
    }
  ]
}
```

#### GET /api/v1/telemetry/device/{device_id}
Get telemetry data for a device

**Query Parameters:**
- `start` (datetime): Start time (ISO 8601)
- `end` (datetime): End time (ISO 8601)
- `measurement` (string): Filter by measurement name
- `limit` (integer): Max results (default: 100)

**Example:**
```bash
curl "http://localhost:5000/api/v1/telemetry/device/1?start=2025-11-01T00:00:00Z&end=2025-11-22T23:59:59Z&measurement=temperature&limit=50"
```

#### GET /api/v1/telemetry/latest/{device_id}
Get latest telemetry data for a device

**Query Parameters:**
- `measurement` (string): Filter by measurement name

---

### Charts

#### POST /api/v1/charts
Create a new chart

**Request Body:**
```json
{
  "name": "string",
  "chart_type": "line|bar|pie|scatter|area",
  "user_id": "string (UUID)",
  "description": "string (optional)"
}
```

#### GET /api/v1/charts
List all charts

**Query Parameters:**
- `user_id` (string): Filter by user
- `limit` (integer): Max results (default: 100)
- `offset` (integer): Pagination offset

#### GET /api/v1/charts/{chart_id}
Get chart details including devices and measurements

#### PUT /api/v1/charts/{chart_id}
Update chart configuration

**Request Body:**
```json
{
  "name": "string (optional)",
  "description": "string (optional)",
  "chart_type": "string (optional)"
}
```

#### DELETE /api/v1/charts/{chart_id}
Delete a chart

#### GET /api/v1/charts/{chart_id}/data
Get data for chart visualization

**Query Parameters:**
- `start` (datetime): Start time
- `end` (datetime): End time
- `limit` (integer): Max data points (default: 1000)

---

### Admin

#### GET /api/v1/admin/users
List all users (admin only)

#### GET /api/v1/admin/devices
List all devices (admin only)

#### GET /api/v1/admin/devices/{device_id}
Get detailed device information with stats (admin only)

#### GET /api/v1/admin/stats
Get system statistics (admin only)

---

## Data Models

### User
```json
{
  "id": "integer",
  "user_id": "string (UUID)",
  "username": "string",
  "email": "string",
  "is_active": "boolean",
  "is_admin": "boolean",
  "created_at": "datetime"
}
```

### Device
```json
{
  "id": "integer",
  "api_key": "string",
  "name": "string",
  "device_type": "string",
  "status": "active|inactive|maintenance",
  "last_seen": "datetime",
  "created_at": "datetime"
}
```

### Telemetry Data
```json
{
  "device_id": "integer",
  "measurement_name": "string",
  "timestamp": "datetime",
  "numeric_value": "float",
  "string_value": "string",
  "unit": "string"
}
```

### Chart
```json
{
  "id": "integer",
  "name": "string",
  "chart_type": "line|bar|pie|scatter|area",
  "description": "string",
  "user_id": "integer",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error type",
  "message": "Detailed error message"
}
```

### Common HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required or failed
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

---

## Rate Limiting

Currently, rate limiting is disabled. When enabled, rate limits will be:
- **60 requests per minute** per device/user
- Rate limit headers will be included in responses:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `limit`: Maximum number of results (default: 100)
- `offset`: Number of results to skip (default: 0)

**Example:**
```bash
curl "http://localhost:5000/api/v1/devices?limit=20&offset=40"
```

**Response includes metadata:**
```json
{
  "status": "success",
  "devices": [...],
  "meta": {
    "total": 150,
    "limit": 20,
    "offset": 40
  }
}
```

---

## Time Ranges

Endpoints that support time filtering accept ISO 8601 datetime format:

**Format:** `YYYY-MM-DDTHH:MM:SSZ`

**Examples:**
- `2025-11-22T00:00:00Z`
- `2025-11-22T23:59:59Z`

**Query Parameters:**
- `start`: Start datetime (inclusive)
- `end`: End datetime (inclusive)

---

## Best Practices

### 1. Always Use HTTPS in Production
```bash
# Production
curl https://api.iotflow.example.com/api/v1/devices
```

### 2. Store API Keys Securely
- Never commit API keys to version control
- Use environment variables
- Rotate keys regularly

### 3. Handle Errors Gracefully
```python
import requests

try:
    response = requests.post(
        'http://localhost:5000/api/v1/telemetry',
        headers={'X-API-Key': api_key},
        json={'measurements': data}
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

### 4. Use Batch Operations
Submit multiple measurements in one request:
```json
{
  "measurements": [
    {"name": "temperature", "value": 25.5},
    {"name": "humidity", "value": 60},
    {"name": "pressure", "value": 1013}
  ]
}
```

### 5. Implement Retry Logic
```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
```

---

## Code Examples

### Python

```python
import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
API_KEY = "your-device-api-key"

# Submit telemetry data
def send_telemetry(temperature, humidity):
    url = f"{BASE_URL}/api/v1/telemetry"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    data = {
        "measurements": [
            {"name": "temperature", "value": temperature, "unit": "celsius"},
            {"name": "humidity", "value": humidity, "unit": "percent"}
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# Get device telemetry
def get_telemetry(device_id, limit=10):
    url = f"{BASE_URL}/api/v1/telemetry/device/{device_id}"
    params = {"limit": limit}
    
    response = requests.get(url, params=params)
    return response.json()

# Usage
result = send_telemetry(25.5, 60)
print(result)

data = get_telemetry(1, limit=5)
print(data)
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:5000';
const API_KEY = 'your-device-api-key';

// Submit telemetry data
async function sendTelemetry(temperature, humidity) {
  try {
    const response = await axios.post(
      `${BASE_URL}/api/v1/telemetry`,
      {
        measurements: [
          { name: 'temperature', value: temperature, unit: 'celsius' },
          { name: 'humidity', value: humidity, unit: 'percent' }
        ]
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
    throw error;
  }
}

// Get device telemetry
async function getTelemetry(deviceId, limit = 10) {
  try {
    const response = await axios.get(
      `${BASE_URL}/api/v1/telemetry/device/${deviceId}`,
      { params: { limit } }
    );
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
    throw error;
  }
}

// Usage
(async () => {
  const result = await sendTelemetry(25.5, 60);
  console.log(result);
  
  const data = await getTelemetry(1, 5);
  console.log(data);
})();
```

### cURL

```bash
#!/bin/bash

BASE_URL="http://localhost:5000"
API_KEY="your-device-api-key"

# Submit telemetry data
curl -X POST "${BASE_URL}/api/v1/telemetry" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "measurements": [
      {"name": "temperature", "value": 25.5, "unit": "celsius"},
      {"name": "humidity", "value": 60, "unit": "percent"}
    ]
  }'

# Get device telemetry
curl "${BASE_URL}/api/v1/telemetry/device/1?limit=10"
```

---

## Support

For issues, questions, or contributions:
- **GitHub:** https://github.com/IoT-Flow/Connectivity-Layer
- **Documentation:** http://localhost:5000/docs

---

## Changelog

### Version 1.0.0 (2025-11-22)
- Initial API release
- User authentication and management
- Device registration and management
- Telemetry data ingestion (PostgreSQL)
- Chart configuration and visualization
- Admin functions
- Health monitoring
- Interactive Swagger documentation
