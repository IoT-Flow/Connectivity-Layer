# Telemetry Data Retrieval APIs

## Overview
APIs to retrieve telemetry data from devices. All endpoints require device authentication via API key.

---

## 1. Get Device Telemetry (Time Range)

Retrieve telemetry data for a specific device within a time range.

### Endpoint
```
GET /api/v1/telemetry/{device_id}
```

### Headers
- `X-API-Key`: Device API key (required)

### Path Parameters
- `device_id` (integer): The device ID

### Query Parameters
- `start_time` (string, optional): Start time (default: "-1h")
  - Examples: "-1h", "-24h", "-7d", "2024-01-01T00:00:00Z"
- `limit` (integer, optional): Maximum records to return (default: 1000, max: 10000)
- `measurement` (string, optional): Filter by specific measurement name

### Example Request
```bash
# Get last hour of data
curl -X GET "http://localhost:5000/api/v1/telemetry/54" \
  -H "X-API-Key: JVpok9Vp4jCOTyHJ9eHsNteXY3bfkJZv"

# Get last 24 hours
curl -X GET "http://localhost:5000/api/v1/telemetry/54?start_time=-24h" \
  -H "X-API-Key: JVpok9Vp4jCOTyHJ9eHsNteXY3bfkJZv"

# Get last 100 records
curl -X GET "http://localhost:5000/api/v1/telemetry/54?limit=100" \
  -H "X-API-Key: JVpok9Vp4jCOTyHJ9eHsNteXY3bfkJZv"
```

### Response (200 OK)
```json
{
  "device_id": 54,
  "device_name": "Test",
  "device_type": "sensor",
  "start_time": "-1h",
  "data": [
    {
      "timestamp": "2025-11-22T05:25:14.659617Z",
      "temperature": 25.5,
      "humidity": 60.2,
      "pressure": 1013.25
    },
    {
      "timestamp": "2025-11-22T05:26:15.123456Z",
      "temperature": 26.0,
      "humidity": 61.5,
      "pressure": 1013.30
    }
  ],
  "count": 2,
  "postgres_available": true
}
```

---

## 2. Get Latest Telemetry

Get the most recent telemetry data for a device.

### Endpoint
```
GET /api/v1/telemetry/{device_id}/latest
```

### Headers
- `X-API-Key`: Device API key (required)

### Path Parameters
- `device_id` (integer): The device ID

### Query Parameters
- `measurement` (string, optional): Filter by specific measurement

### Example Request
```bash
curl -X GET "http://localhost:5000/api/v1/telemetry/54/latest" \
  -H "X-API-Key: JVpok9Vp4jCOTyHJ9eHsNteXY3bfkJZv"
```

### Response (200 OK)
```json
{
  "device_id": 54,
  "device_name": "Test",
  "device_type": "sensor",
  "latest_data": {
    "timestamp": "2025-11-22T05:25:14.659617Z",
    "temperature": 25.5,
    "humidity": 60.2,
    "pressure": 1013.25
  },
  "postgres_available": true
}
```

### Response (404 Not Found)
```json
{
  "device_id": 54,
  "device_name": "Test",
  "message": "No telemetry data found",
  "postgres_available": true
}
```

---

## 3. Get Aggregated Telemetry

Get aggregated statistics (min, max, avg) for telemetry data.

### Endpoint
```
GET /api/v1/telemetry/{device_id}/aggregated
```

### Headers
- `X-API-Key`: Device API key (required)

### Path Parameters
- `device_id` (integer): The device ID

### Query Parameters
- `field` (string, optional): Field to aggregate (default: "temperature")
- `start_time` (string, optional): Start time (default: "-1h")
- `interval` (string, optional): Aggregation interval (e.g., "1h", "1d")

### Example Request
```bash
# Get temperature statistics for last 24 hours
curl -X GET "http://localhost:5000/api/v1/telemetry/54/aggregated?field=temperature&start_time=-24h" \
  -H "X-API-Key: JVpok9Vp4jCOTyHJ9eHsNteXY3bfkJZv"
```

### Response (200 OK)
```json
{
  "device_id": 54,
  "device_name": "Test",
  "field": "temperature",
  "start_time": "-24h",
  "aggregated_data": {
    "min": 18.5,
    "max": 28.0,
    "avg": 23.5,
    "count": 144
  }
}
```

---

## 4. Get Device Telemetry (Alternative Endpoint)

Alternative endpoint using device authentication.

### Endpoint
```
GET /api/v1/devices/telemetry
```

### Headers
- `X-API-Key`: Device API key (required)

### Query Parameters
- `limit` (integer, optional): Maximum records (default: 100, max: 1000)
- `start_time` (string, optional): Start time (default: "-24h")
- `measurement_name` (string, optional): Filter by measurement name

### Example Request
```bash
curl -X GET "http://localhost:5000/api/v1/devices/telemetry?limit=50" \
  -H "X-API-Key: JVpok9Vp4jCOTyHJ9eHsNteXY3bfkJZv"
```

### Response (200 OK)
```json
{
  "status": "success",
  "telemetry": [
    {
      "timestamp": "2025-11-22T05:25:14.659617Z",
      "temperature": 25.5,
      "humidity": 60.2
    }
  ],
  "count": 1,
  "limit": 50,
  "start_time": "-24h"
}
```

---

## 5. Get Telemetry Status

Get PostgreSQL telemetry service status and statistics.

### Endpoint
```
GET /api/v1/telemetry/status
```

### Headers
None required (public endpoint)

### Example Request
```bash
curl -X GET "http://localhost:5000/api/v1/telemetry/status"
```

### Response (200 OK)
```json
{
  "status": "operational",
  "postgres_available": true,
  "total_records": 1523,
  "total_devices": 12,
  "last_24h_records": 456
}
```

---

## 6. Get User Telemetry

Get telemetry data for all devices belonging to a user.

### Endpoint
```
GET /api/v1/telemetry/user/{user_id}
```

### Headers
- `X-User-ID`: User ID (required) or authentication token

### Path Parameters
- `user_id` (integer): The user's internal database ID

### Query Parameters
- `start_time` (string, optional): Start time (default: "-1h")
- `limit` (integer, optional): Records per device (default: 100)

### Example Request
```bash
curl -X GET "http://localhost:5000/api/v1/telemetry/user/1?start_time=-24h" \
  -H "X-User-ID: adc513e4ab554b3f84900affe582beb8"
```

### Response (200 OK)
```json
{
  "user_id": 1,
  "devices": [
    {
      "device_id": 54,
      "device_name": "Test",
      "telemetry": [
        {
          "timestamp": "2025-11-22T05:25:14.659617Z",
          "temperature": 25.5
        }
      ],
      "count": 1
    }
  ],
  "total_devices": 1,
  "start_time": "-24h"
}
```

---

## Error Responses

### 401 Unauthorized - Missing API Key
```json
{
  "error": "API key required"
}
```

### 401 Unauthorized - Invalid API Key
```json
{
  "error": "Invalid API key"
}
```

### 403 Forbidden - Device Mismatch
```json
{
  "error": "Forbidden: device mismatch"
}
```

### 404 Not Found - No Data
```json
{
  "device_id": 54,
  "device_name": "Test",
  "message": "No telemetry data found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error: <error details>"
}
```

---

## Time Format Examples

### Relative Time
- `-1h` - Last 1 hour
- `-24h` - Last 24 hours
- `-7d` - Last 7 days
- `-30d` - Last 30 days

### Absolute Time (ISO 8601)
- `2024-01-01T00:00:00Z`
- `2024-11-22T05:25:14.659617Z`

---

## Complete Example Workflow

```bash
# 1. Send telemetry data
curl -X POST http://localhost:5000/api/v1/devices/telemetry \
  -H "X-API-Key: JVpok9Vp4jCOTyHJ9eHsNteXY3bfkJZv" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "temperature": 25.5,
      "humidity": 60.2,
      "pressure": 1013.25
    }
  }'

# 2. Get latest telemetry
curl -X GET "http://localhost:5000/api/v1/telemetry/54/latest" \
  -H "X-API-Key: JVpok9Vp4jCOTyHJ9eHsNteXY3bfkJZv"

# 3. Get last 24 hours of data
curl -X GET "http://localhost:5000/api/v1/telemetry/54?start_time=-24h&limit=100" \
  -H "X-API-Key: JVpok9Vp4jCOTyHJ9eHsNteXY3bfkJZv"

# 4. Get aggregated statistics
curl -X GET "http://localhost:5000/api/v1/telemetry/54/aggregated?field=temperature&start_time=-24h" \
  -H "X-API-Key: JVpok9Vp4jCOTyHJ9eHsNteXY3bfkJZv"
```

---

## Quick Reference

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/api/v1/telemetry/{device_id}` | GET | Get time-range data | API Key |
| `/api/v1/telemetry/{device_id}/latest` | GET | Get latest data | API Key |
| `/api/v1/telemetry/{device_id}/aggregated` | GET | Get statistics | API Key |
| `/api/v1/devices/telemetry` | GET | Get device data | API Key |
| `/api/v1/telemetry/status` | GET | Service status | None |
| `/api/v1/telemetry/user/{user_id}` | GET | Get user's devices data | User ID |

---

## Notes

1. **Device ID**: Use the device's internal database ID (integer), not the UUID
2. **API Key**: Must be the device's API key returned during registration
3. **Time Range**: Default is last 1 hour if not specified
4. **Limits**: Maximum 10,000 records per request for performance
5. **Authentication**: Device must be active to retrieve data
