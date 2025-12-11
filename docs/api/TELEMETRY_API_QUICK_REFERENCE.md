# Telemetry API Quick Reference

## New Enhanced Endpoints

### Get Telemetry Data
```bash
GET /api/v1/telemetry/device/{device_id}
```

**Headers**:
```
X-API-Key: <device_api_key>
```

**Query Parameters**:
- `data_type` (optional): Filter by specific measurement type (e.g., "temperature")
- `start_date` (optional): ISO 8601 date (e.g., "2024-12-09T00:00:00Z")
- `end_date` (optional): ISO 8601 date
- `limit` (optional): Records per page (default: 100, max: 1000)
- `page` (optional): Page number (default: 1)

**Example**:
```bash
curl -X GET "http://localhost:5000/api/v1/telemetry/device/1?data_type=temperature&limit=50&page=1" \
  -H "X-API-Key: your_device_api_key"
```

**Response**:
```json
{
  "success": true,
  "device_id": 1,
  "device_name": "Sensor_01",
  "device_type": "temperature_sensor",
  "telemetry": [
    {
      "timestamp": "2024-12-10T03:00:00Z",
      "device_id": 1,
      "measurements": {
        "temperature": 23.5
      }
    }
  ],
  "pagination": {
    "total": 100,
    "currentPage": 1,
    "totalPages": 2,
    "limit": 50
  },
  "filters": {
    "data_type": "temperature"
  },
  "iotdb_available": true
}
```

---

### Get Aggregated Telemetry
```bash
GET /api/v1/telemetry/device/{device_id}/aggregated
```

**Headers**:
```
X-API-Key: <device_api_key>
```

**Query Parameters** (Required):
- `data_type`: Measurement to aggregate (e.g., "temperature")
- `aggregation`: Function to apply (avg, sum, min, max, count)

**Query Parameters** (Optional):
- `start_date`: ISO 8601 date
- `end_date`: ISO 8601 date

**Example**:
```bash
curl -X GET "http://localhost:5000/api/v1/telemetry/device/1/aggregated?data_type=temperature&aggregation=avg" \
  -H "X-API-Key: your_device_api_key"
```

**Response**:
```json
{
  "success": true,
  "device_id": 1,
  "device_name": "Sensor_01",
  "device_type": "temperature_sensor",
  "aggregation": {
    "type": "avg",
    "data_type": "temperature",
    "value": 24.5,
    "count": 100
  },
  "iotdb_available": true
}
```

---

## Legacy Endpoints (Still Supported)

### Get Telemetry Data (Legacy)
```bash
GET /api/v1/telemetry/{device_id}
```

**Query Parameters**:
- `start_time`: Relative time (e.g., "-1h", "-24h")
- `limit`: Max records (default: 1000, max: 10000)

---

### Get Aggregated Telemetry (Legacy)
```bash
GET /api/v1/telemetry/{device_id}/aggregated
```

**Query Parameters**:
- `field`: Measurement name (default: "temperature")
- `aggregation`: Function (default: "mean")
- `window`: Time window (default: "1h")
- `start_time`: Relative time (default: "-24h")

---

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "error": "data_type parameter is required"
}
```

### 401 Unauthorized
```json
{
  "success": false,
  "error": "API key required"
}
```

### 403 Forbidden
```json
{
  "success": false,
  "error": "Forbidden: device mismatch"
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": "Device not found"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Failed to retrieve telemetry data"
}
```

---

## Supported Aggregation Functions

- `avg` - Average value
- `sum` - Sum of all values
- `min` - Minimum value
- `max` - Maximum value
- `count` - Count of records

---

## Date Format

All dates should be in ISO 8601 format:
- `2024-12-10T03:00:00Z` (UTC)
- `2024-12-10T03:00:00+00:00` (with timezone)

---

## Testing Examples

### Python
```python
import requests

# Get telemetry data
response = requests.get(
    "http://localhost:5000/api/v1/telemetry/device/1",
    headers={"X-API-Key": "your_api_key"},
    params={
        "data_type": "temperature",
        "limit": 50,
        "page": 1
    }
)
data = response.json()
print(f"Retrieved {len(data['telemetry'])} records")

# Get aggregated data
response = requests.get(
    "http://localhost:5000/api/v1/telemetry/device/1/aggregated",
    headers={"X-API-Key": "your_api_key"},
    params={
        "data_type": "temperature",
        "aggregation": "avg"
    }
)
data = response.json()
print(f"Average temperature: {data['aggregation']['value']}")
```

### JavaScript
```javascript
// Get telemetry data
const response = await fetch(
  'http://localhost:5000/api/v1/telemetry/device/1?data_type=temperature&limit=50',
  {
    headers: {
      'X-API-Key': 'your_api_key'
    }
  }
);
const data = await response.json();
console.log(`Retrieved ${data.telemetry.length} records`);

// Get aggregated data
const aggResponse = await fetch(
  'http://localhost:5000/api/v1/telemetry/device/1/aggregated?data_type=temperature&aggregation=avg',
  {
    headers: {
      'X-API-Key': 'your_api_key'
    }
  }
);
const aggData = await aggResponse.json();
console.log(`Average temperature: ${aggData.aggregation.value}`);
```

---

## Migration Checklist

- [ ] Update API endpoint URLs to use `/device/<id>` pattern
- [ ] Add pagination parameters to queries
- [ ] Update date format to ISO 8601
- [ ] Handle new response format with `success` flag
- [ ] Update aggregation parameter names (field → data_type)
- [ ] Test error handling with new error format
- [ ] Update documentation and client libraries
