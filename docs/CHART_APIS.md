# Chart API Documentation

## Overview
The Chart API provides endpoints for creating, managing, and retrieving chart configurations for visualizing IoT telemetry data.

Base URL: `/api/v1/charts`

---

## Chart Management

### Create Chart
Create a new chart configuration.

**Endpoint:** `POST /api/v1/charts`

**Request Body:**
```json
{
  "name": "Temperature Monitor",
  "title": "Device Temperature Overview",
  "description": "Monitor temperature for a specific device",
  "type": "line",
  "user_id": "abc123def456",
  "device_id": 1,
  "time_range": "24h",
  "refresh_interval": 30,
  "aggregation": "mean",
  "group_by": "device",
  "appearance_config": {
    "theme": "dark",
    "show_legend": true,
    "show_grid": true
  }
}
```

**Parameters:**
- `name` (required): Chart name
- `type` (required): Chart type - one of: `line`, `bar`, `pie`, `scatter`, `area`
- `user_id` (required): User ID who owns the chart
- `device_id` (optional): Device ID to monitor
- `title` (optional): Display title for the chart
- `description` (optional): Chart description
- `time_range` (optional): Default time range (e.g., "1h", "24h", "7d"). Default: "24h"
- `refresh_interval` (optional): Auto-refresh interval in seconds. Default: 30
- `aggregation` (optional): Data aggregation method. Default: "none"
- `group_by` (optional): Group data by "device" or "measurement". Default: "device"
- `appearance_config` (optional): JSON object with appearance settings

**Response:** `201 Created`
```json
{
  "status": "success",
  "message": "Chart created successfully",
  "chart": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Temperature Monitor",
    "title": "Device Temperature Overview",
    "description": "Monitor temperature across all devices",
    "type": "line",
    "user_id": 1,
    "device_id": 1,
    "time_range": "24h",
    "refresh_interval": 30,
    "aggregation": "mean",
    "group_by": "device",
    "appearance_config": {...},
    "created_at": "2025-11-22T07:00:00Z",
    "updated_at": "2025-11-22T07:00:00Z",
    "is_active": true
  }
}
```

---

### List Charts
Get all active charts with optional filtering.

**Endpoint:** `GET /api/v1/charts`

**Query Parameters:**
- `user_id` (optional): Filter by user ID
- `limit` (optional): Maximum number of results. Default: 100
- `offset` (optional): Pagination offset. Default: 0

**Example:**
```bash
GET /api/v1/charts?user_id=abc123def456&limit=10&offset=0
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "charts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Temperature Monitor",
      "type": "line",
      ...
    }
  ],
  "meta": {
    "total": 25,
    "limit": 10,
    "offset": 0
  }
}
```

---

### Get Chart by ID
Retrieve a specific chart with its associated devices and measurements.

**Endpoint:** `GET /api/v1/charts/{chart_id}`

**Response:** `200 OK`
```json
{
  "status": "success",
  "chart": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Temperature Monitor",
    "type": "line",
    "device_id": 1,
    "device": {
      "id": 1,
      "name": "Sensor-01",
      "device_type": "temperature_sensor",
      ...
    },
    "measurements": [
      {
        "id": 1,
        "measurement_name": "temperature",
        "display_name": "Temperature (°C)",
        "color": "#FF5733"
      }
    ],
    ...
  }
}
```

---

### Update Chart
Update an existing chart configuration.

**Endpoint:** `PUT /api/v1/charts/{chart_id}`

**Request Body:**
```json
{
  "name": "Updated Chart Name",
  "title": "New Title",
  "type": "bar",
  "device_id": 2,
  "time_range": "12h",
  "refresh_interval": 60,
  "appearance_config": {
    "theme": "light"
  }
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Chart updated successfully",
  "chart": {...}
}
```

---

### Delete Chart
Soft delete a chart (marks as inactive).

**Endpoint:** `DELETE /api/v1/charts/{chart_id}`

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Chart 'Temperature Monitor' deleted successfully"
}
```

---

## Measurement Configuration

### Add Measurement to Chart
Add a measurement type to track in the chart.

**Endpoint:** `POST /api/v1/charts/{chart_id}/measurements`

**Request Body:**
```json
{
  "measurement_name": "temperature",
  "display_name": "Temperature (°C)",
  "color": "#FF5733"
}
```

**Parameters:**
- `measurement_name` (required): Name of the measurement field
- `display_name` (optional): Human-readable display name. Default: measurement_name
- `color` (optional): Hex color code for visualization. Default: "#000000"

**Response:** `201 Created`
```json
{
  "status": "success",
  "message": "Measurement added to chart successfully",
  "measurement": {
    "id": 1,
    "measurement_name": "temperature",
    "display_name": "Temperature (°C)",
    "color": "#FF5733"
  }
}
```

---

### Remove Measurement from Chart
Remove a measurement from a chart.

**Endpoint:** `DELETE /api/v1/charts/{chart_id}/measurements/{measurement_id}`

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Measurement removed from chart successfully"
}
```

---

## Data Retrieval

### Get Chart Data
Retrieve actual telemetry data for visualization based on chart configuration.

**Endpoint:** `GET /api/v1/charts/{chart_id}/data`

**Query Parameters:**
- `start` (optional): Start time (ISO 8601 format)
- `end` (optional): End time (ISO 8601 format)
- `limit` (optional): Maximum number of data points. Default: 1000

**Example:**
```bash
GET /api/v1/charts/{chart_id}/data?start=2025-11-22T00:00:00Z&end=2025-11-22T23:59:59Z&limit=500
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "chart_id": "550e8400-e29b-41d4-a716-446655440000",
  "chart_name": "Temperature Monitor",
  "chart_type": "line",
  "data": [
    {
      "device_id": 1,
      "measurement_name": "temperature",
      "timestamp": "2025-11-22T07:00:00Z",
      "value": 25.5
    },
    {
      "device_id": 1,
      "measurement_name": "temperature",
      "timestamp": "2025-11-22T07:01:00Z",
      "value": 25.7
    }
  ],
  "series": [
    {
      "name": "Temperature (°C)",
      "color": "#FF5733",
      "data": [
        {
          "x": "2025-11-22T07:00:00Z",
          "y": 25.5
        },
        {
          "x": "2025-11-22T07:01:00Z",
          "y": 25.7
        }
      ]
    }
  ],
  "count": 2
}
```

---

## Complete Workflow Example

### 1. Create a Chart
```bash
curl -X POST http://localhost:5000/api/v1/charts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Temperature Dashboard",
    "type": "line",
    "user_id": "abc123def456",
    "device_id": 1,
    "time_range": "24h",
    "refresh_interval": 30
  }'
```

### 2. Add Measurements to Chart
```bash
curl -X POST http://localhost:5000/api/v1/charts/{chart_id}/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "measurement_name": "temperature",
    "display_name": "Temperature (°C)",
    "color": "#FF5733"
  }'

curl -X POST http://localhost:5000/api/v1/charts/{chart_id}/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "measurement_name": "humidity",
    "display_name": "Humidity (%)",
    "color": "#3498DB"
  }'
```

### 3. Retrieve Chart Data
```bash
curl -X GET "http://localhost:5000/api/v1/charts/{chart_id}/data?limit=100"
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Missing required fields",
  "message": "name, type, and user_id are required"
}
```

### 404 Not Found
```json
{
  "error": "Chart not found",
  "message": "No chart found with ID: {chart_id}"
}
```

### 500 Internal Server Error
```json
{
  "error": "Chart creation failed",
  "message": "An error occurred while creating the chart"
}
```

---

## Chart Types

- **line**: Line chart for time-series data
- **bar**: Bar chart for comparing values
- **pie**: Pie chart for showing proportions
- **scatter**: Scatter plot for correlation analysis
- **area**: Area chart for cumulative data

---

## Time Range Format

Supported time range formats:
- `1h` - 1 hour
- `6h` - 6 hours
- `12h` - 12 hours
- `24h` - 24 hours (1 day)
- `7d` - 7 days
- `30d` - 30 days

---

## Notes

- Charts use soft deletion (marked as inactive rather than removed from database)
- The `series` array in chart data is pre-formatted for easy integration with charting libraries
- Device and measurement associations are many-to-many relationships
- All timestamps are in ISO 8601 format with UTC timezone
