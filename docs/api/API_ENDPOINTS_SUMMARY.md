# IoTFlow API Endpoints Summary

Complete reference for all REST API endpoints in the IoTFlow Connectivity Layer.

## Table of Contents
- [Authentication](#authentication)
- [Device Management](#device-management)
- [Telemetry Data](#telemetry-data)
- [MQTT Management](#mqtt-management)
- [Device Control](#device-control)
- [Administration](#administration)
- [System Health](#system-health)

---

## Authentication

### Authentication Methods

| Method | Header | Description |
|--------|--------|-------------|
| **API Key** | `X-API-Key: <device_api_key>` | Device-specific authentication |
| **Admin Token** | `Authorization: admin <token>` | Administrative operations |
| **None** | - | Public endpoints (health, registration) |

---

## Device Management

**Base Path:** `/api/v1/devices`

### 1. Register Device
**POST** `/api/v1/devices/register`

Register a new IoT device with user authentication.

**Authentication:** None (requires `user_id` in payload)

**Request Body:**
```json
{
  "name": "Smart Sensor 001",
  "device_type": "temperature_sensor",
  "user_id": "user123",
  "description": "Living room sensor",
  "location": "Living Room",
  "firmware_version": "1.2.3",
  "hardware_version": "v2.1"
}
```

**Response:** `201 Created`
```json
{
  "message": "Device registered successfully",
  "device": {
    "id": 1,
    "name": "Smart Sensor 001",
    "api_key": "rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB",
    "status": "active",
    "device_type": "temperature_sensor",
    "created_at": "2025-07-02T14:30:00Z"
  }
}
```

---

### 2. Get Device Status
**GET** `/api/v1/devices/status`

Get current device status and health information.

**Authentication:** API Key (device's own key)

**Response:** `200 OK`
```json
{
  "status": "success",
  "device": {
    "id": 1,
    "name": "Smart Sensor 001",
    "status": "active",
    "is_online": true,
    "last_seen": "2025-07-02T14:30:00Z",
    "telemetry_count": 1523
  }
}
```

---

### 3. Device Heartbeat
**POST** `/api/v1/devices/heartbeat`

Send heartbeat to indicate device is online.

**Authentication:** API Key

**Response:** `200 OK`
```json
{
  "message": "Heartbeat received",
  "device_id": 1,
  "timestamp": "2025-07-02T14:30:00Z",
  "status": "online"
}
```

---

### 4. Submit Telemetry (Device Endpoint)
**POST** `/api/v1/devices/telemetry`

Submit telemetry data from device.

**Authentication:** API Key

**Request Body:**
```json
{
  "data": {
    "temperature": 23.5,
    "humidity": 65.2,
    "pressure": 1013.25,
    "battery_level": 87
  },
  "metadata": {
    "location": "Living Room",
    "sensor_status": "active"
  },
  "timestamp": "2025-07-02T14:30:00Z"
}
```

**Response:** `201 Created`
```json
{
  "message": "Telemetry data received successfully",
  "device_id": 1,
  "device_name": "Smart Sensor 001",
  "timestamp": "2025-07-02T14:30:00Z",
  "stored_in_iotdb": true
}
```

---

### 5. Get Device Telemetry
**GET** `/api/v1/devices/telemetry`

Get telemetry data for the authenticated device.

**Authentication:** API Key

**Query Parameters:**
- `limit` (optional): Max records to return (default: 100, max: 1000)
- `start_time` (optional): Start time (default: -24h)
- `type` (optional): Filter by data type

**Response:** `200 OK`
```json
{
  "status": "success",
  "telemetry": [...],
  "count": 50,
  "limit": 100,
  "start_time": "-24h"
}
```

---

### 6. Update Device Configuration
**PUT** `/api/v1/devices/config`

Update device information (status, location, versions).

**Authentication:** API Key

**Request Body:**
```json
{
  "status": "active",
  "location": "Kitchen",
  "firmware_version": "1.3.0",
  "hardware_version": "v2.1"
}
```

**Response:** `200 OK`

---

### 7. Get Device Configuration
**GET** `/api/v1/devices/config`

Get device configuration settings.

**Authentication:** API Key

**Response:** `200 OK`
```json
{
  "status": "success",
  "device_id": 1,
  "configuration": {
    "sampling_rate": {
      "value": 30,
      "data_type": "integer",
      "updated_at": "2025-07-02T14:30:00Z"
    }
  }
}
```

---

### 8. Update Device Configuration
**POST** `/api/v1/devices/config`

Update or create device configuration key-value pair.

**Authentication:** API Key

**Request Body:**
```json
{
  "config_key": "sampling_rate",
  "config_value": "30",
  "data_type": "integer"
}
```

**Response:** `200 OK`

---

### 9. Get Device Credentials
**GET** `/api/v1/devices/credentials`

Get device credentials and MQTT topics using API key.

**Authentication:** API Key

**Response:** `200 OK`
```json
{
  "status": "success",
  "device": {
    "id": 1,
    "name": "Smart Sensor 001",
    "device_type": "temperature_sensor",
    "user_id": "user123",
    "status": "active",
    "mqtt_topics": {
      "telemetry": "iotflow/devices/1/telemetry/sensors",
      "status": "iotflow/devices/1/status",
      "commands": "iotflow/devices/1/commands/control",
      "heartbeat": "iotflow/devices/1/status/heartbeat"
    }
  }
}
```

---

### 10. Get MQTT Credentials
**GET** `/api/v1/devices/mqtt-credentials`

Get MQTT connection details for device.

**Authentication:** API Key

**Response:** `200 OK`
```json
{
  "status": "success",
  "credentials": {
    "mqtt_host": "localhost",
    "mqtt_port": 1883,
    "client_id": "device_1_Smart_Sensor_001",
    "api_key": "rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB",
    "anonymous_connection": true,
    "topics": {
      "telemetry_publish": "iotflow/devices/1/telemetry",
      "status_publish": "iotflow/devices/1/status",
      "commands_subscribe": "iotflow/devices/1/commands",
      "config_subscribe": "iotflow/devices/1/config"
    }
  }
}
```

---

### 11. Get All Device Statuses
**GET** `/api/v1/devices/statuses`

Get status of all devices (condensed info for dashboard).

**Authentication:** None

**Query Parameters:**
- `limit` (optional): Max devices to return (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:** `200 OK`
```json
{
  "status": "success",
  "devices": [
    {
      "id": 1,
      "name": "Smart Sensor 001",
      "device_type": "temperature_sensor",
      "status": "active",
      "is_online": true
    }
  ],
  "meta": {
    "total": 150,
    "limit": 100,
    "offset": 0,
    "cache_used": true
  }
}
```

---

### 12. Get Device Status by ID
**GET** `/api/v1/devices/<device_id>/status`

Get status of a specific device.

**Authentication:** None

**Response:** `200 OK`
```json
{
  "status": "success",
  "device": {
    "id": 1,
    "name": "Smart Sensor 001",
    "device_type": "temperature_sensor",
    "status": "active",
    "is_online": true,
    "last_seen": "2025-07-02T14:30:00Z",
    "status_source": "redis_cache_verified"
  }
}
```

---

## Telemetry Data

**Base Path:** `/api/v1/telemetry`

### 1. Store Telemetry
**POST** `/api/v1/telemetry`

Store telemetry data in IoTDB.

**Authentication:** API Key

**Request Body:**
```json
{
  "data": {
    "temperature": 24.5,
    "humidity": 62.0,
    "pressure": 1012.5
  },
  "metadata": {
    "location": "Office"
  },
  "timestamp": "2025-07-02T14:30:00Z"
}
```

**Response:** `201 Created`
```json
{
  "message": "Telemetry data stored successfully",
  "device_id": 1,
  "device_name": "Smart Sensor 001",
  "timestamp": "2025-07-02T14:30:00Z"
}
```

---

### 2. Get Device Telemetry
**GET** `/api/v1/telemetry/<device_id>`

Get telemetry data for a specific device.

**Authentication:** API Key (device's own key or admin)

**Query Parameters:**
- `start_time` (optional): Start time (default: -1h)
- `limit` (optional): Max records (default: 1000, max: 10000)

**Response:** `200 OK`
```json
{
  "device_id": 1,
  "device_name": "Smart Sensor 001",
  "device_type": "temperature_sensor",
  "start_time": "-1h",
  "data": [...],
  "count": 120,
  "iotdb_available": true
}
```

---

### 3. Get Latest Telemetry
**GET** `/api/v1/telemetry/<device_id>/latest`

Get the latest telemetry data for a device.

**Authentication:** API Key (device's own key or admin)

**Response:** `200 OK`
```json
{
  "device_id": 1,
  "device_name": "Smart Sensor 001",
  "device_type": "temperature_sensor",
  "latest_data": {
    "timestamp": "2025-07-02T14:30:00Z",
    "temperature": 23.5,
    "humidity": 65.2
  },
  "iotdb_available": true
}
```

---

### 4. Get Aggregated Telemetry
**GET** `/api/v1/telemetry/<device_id>/aggregated`

Get aggregated telemetry data for a device.

**Authentication:** API Key (device's own key or admin)

**Query Parameters:**
- `field` (required): Field to aggregate (e.g., "temperature")
- `aggregation` (required): Function (mean, sum, count, min, max, first, last, median)
- `window` (optional): Time window (default: 1h)
- `start_time` (optional): Start time (default: -24h)

**Response:** `200 OK`
```json
{
  "device_id": 1,
  "device_name": "Smart Sensor 001",
  "field": "temperature",
  "aggregation": "mean",
  "window": "1h",
  "start_time": "-24h",
  "data": [...],
  "count": 24,
  "iotdb_available": true
}
```

---

### 5. Delete Device Telemetry
**DELETE** `/api/v1/telemetry/<device_id>`

Delete telemetry data for a device within a time range.

**Authentication:** API Key (device's own key or admin)

**Request Body:**
```json
{
  "start_time": "2025-07-01T00:00:00Z",
  "stop_time": "2025-07-02T00:00:00Z"
}
```

**Response:** `200 OK`
```json
{
  "message": "Telemetry data deleted for device Smart Sensor 001",
  "device_id": 1,
  "start_time": "2025-07-01T00:00:00Z",
  "stop_time": "2025-07-02T00:00:00Z"
}
```

---

### 6. Get Telemetry System Status
**GET** `/api/v1/telemetry/status`

Get IoTDB service status and statistics.

**Authentication:** None

**Response:** `200 OK`
```json
{
  "iotdb_available": true,
  "iotdb_host": "localhost",
  "iotdb_port": 6667,
  "iotdb_database": "root.iotflow",
  "total_devices": 150,
  "status": "healthy"
}
```

---

### 7. Get User Telemetry
**GET** `/api/v1/telemetry/user/<user_id>`

Get telemetry data for all devices belonging to a user.

**Authentication:** API Key (from any device owned by the user)

**Query Parameters:**
- `limit` (optional): Max records (default: 100, max: 1000)
- `start_time` (optional): Start time (default: -24h)
- `end_time` (optional): End time

**Response:** `200 OK`
```json
{
  "status": "success",
  "user_id": 123,
  "telemetry": [...],
  "count": 250,
  "total_count": 5000,
  "limit": 100
}
```

---

## MQTT Management

**Base Path:** `/api/v1/mqtt`

### 1. Get MQTT Status
**GET** `/api/v1/mqtt/status`

Get MQTT broker and client status.

**Authentication:** None

**Response:** `200 OK`
```json
{
  "status": "success",
  "mqtt_status": {
    "connected": true,
    "host": "localhost",
    "port": 1883,
    "use_tls": false
  },
  "broker_info": {
    "host": "localhost",
    "port": 1883,
    "connected": true,
    "tls_enabled": false
  }
}
```

---

### 2. Publish MQTT Message
**POST** `/api/v1/mqtt/publish`

Publish a message to MQTT broker.

**Authentication:** None (consider adding auth in production)

**Request Body:**
```json
{
  "topic": "iotflow/devices/1/commands",
  "payload": {"command": "restart"},
  "qos": 1,
  "retain": false
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Message published successfully",
  "topic": "iotflow/devices/1/commands",
  "qos": 1,
  "retain": false
}
```

---

### 3. Subscribe to MQTT Topic
**POST** `/api/v1/mqtt/subscribe`

Subscribe to an MQTT topic (admin only).

**Authentication:** Admin Token

**Request Body:**
```json
{
  "topic": "iotflow/devices/+/telemetry",
  "qos": 1
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Subscribed successfully",
  "topic": "iotflow/devices/+/telemetry",
  "qos": 1
}
```

---

### 4. Get Device Topics
**GET** `/api/v1/mqtt/topics/device/<device_id>`

Get all MQTT topics for a specific device.

**Authentication:** None

**Response:** `200 OK`
```json
{
  "status": "success",
  "device_id": "1",
  "topics": {
    "telemetry": [
      {
        "name": "device_telemetry",
        "path": "iotflow/devices/1/telemetry",
        "qos": 1,
        "retain": false,
        "description": "Device telemetry data"
      }
    ],
    "commands": [...]
  },
  "total_topics": 8
}
```

---

### 5. Get Topic Structure
**GET** `/api/v1/mqtt/topics/structure`

Get the complete MQTT topic structure.

**Authentication:** None

**Response:** `200 OK`
```json
{
  "status": "success",
  "base_topic": "iotflow",
  "wildcard_patterns": {...},
  "topic_structures": {...},
  "total_structures": 15
}
```

---

### 6. Validate MQTT Topic
**POST** `/api/v1/mqtt/topics/validate`

Validate an MQTT topic.

**Authentication:** None

**Request Body:**
```json
{
  "topic": "iotflow/devices/1/telemetry"
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "topic": "iotflow/devices/1/telemetry",
  "is_valid": true,
  "parsed": {
    "device_id": "1",
    "topic_type": "telemetry"
  }
}
```

---

### 7. Send Device Command
**POST** `/api/v1/mqtt/device/<device_id>/command`

Send a command to a specific device via MQTT.

**Authentication:** Admin Token

**Request Body:**
```json
{
  "command_type": "control",
  "command": "restart",
  "qos": 2,
  "command_id": "cmd_12345",
  "timestamp": "2025-07-02T14:30:00Z"
}
```

**Valid command types:** `config`, `control`, `firmware`

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Command sent successfully",
  "device_id": "1",
  "command_type": "control",
  "topic": "iotflow/devices/1/commands/control",
  "qos": 2
}
```

---

### 8. Send Fleet Command
**POST** `/api/v1/mqtt/fleet/<group_id>/command`

Send a command to a fleet/group of devices.

**Authentication:** Admin Token

**Request Body:**
```json
{
  "command": "update_firmware",
  "qos": 2,
  "command_id": "fleet_cmd_001",
  "timestamp": "2025-07-02T14:30:00Z"
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Fleet command sent successfully",
  "group_id": "warehouse_sensors",
  "topic": "iotflow/fleet/warehouse_sensors/commands",
  "qos": 2
}
```

---

### 9. Get MQTT Metrics
**GET** `/api/v1/mqtt/monitoring/metrics`

Get MQTT monitoring metrics.

**Authentication:** Admin Token

**Response:** `200 OK`
```json
{
  "status": "success",
  "metrics": {
    "connection_status": {...},
    "topics": {
      "total_structures": 15,
      "base_topic": "iotflow"
    },
    "handlers": {
      "message_handlers": 5,
      "subscription_callbacks": 3
    }
  },
  "timestamp": "2025-07-02T14:30:00Z"
}
```

---

### 10. MQTT Telemetry Endpoint
**POST** `/api/v1/mqtt/telemetry/<device_id>`

Submit telemetry via MQTT REST proxy with API key authentication.

**Authentication:** API Key

**Request Body:**
```json
{
  "data": {
    "temperature": 24.5,
    "humidity": 62.0
  },
  "timestamp": "2025-07-02T14:30:00Z"
}
```

**Response:** `201 Created`
```json
{
  "status": "success",
  "message": "Telemetry data processed successfully",
  "device_id": 1,
  "device_name": "Smart Sensor 001",
  "topic": "iotflow/devices/1/telemetry",
  "timestamp": "2025-07-02T14:30:00Z"
}
```

---

## Device Control

**Base Path:** `/api/v1/devices`

### 1. Control Device
**POST** `/api/v1/devices/<device_id>/control`

Send a control command to a device.

**Authentication:** None (consider adding auth in production)

**Request Body:**
```json
{
  "command": "turn_on",
  "parameters": {
    "brightness": 80,
    "color": "warm_white"
  }
}
```

**Response:** `201 Created`
```json
{
  "message": "Command sent via MQTT",
  "control_id": 42
}
```

---

### 2. Update Control Status
**POST** `/api/v1/devices/<device_id>/control/<control_id>/status`

Update the status of a control command (device callback).

**Authentication:** None (consider adding auth in production)

**Request Body:**
```json
{
  "status": "acknowledged"
}
```

**Valid statuses:** `acknowledged`, `failed`

**Response:** `200 OK`
```json
{
  "message": "Status updated"
}
```

---

### 3. Get Pending Controls
**GET** `/api/v1/devices/<device_id>/control/pending`

Get pending control commands for a device.

**Authentication:** None (consider adding auth in production)

**Response:** `200 OK`
```json
[
  {
    "id": 42,
    "command": "turn_on",
    "parameters": {
      "brightness": 80
    },
    "created_at": "2025-07-02T14:30:00Z"
  }
]
```

---

## Administration

**Base Path:** `/api/v1/admin`

**All admin endpoints require Admin Token authentication.**

### 1. List All Devices
**GET** `/api/v1/admin/devices`

List all devices with basic information.

**Authentication:** Admin Token

**Response:** `200 OK`
```json
{
  "status": "success",
  "total_devices": 150,
  "devices": [
    {
      "id": 1,
      "name": "Smart Sensor 001",
      "device_type": "temperature_sensor",
      "status": "active",
      "created_at": "2025-07-01T10:00:00Z",
      "auth_records_count": 1,
      "config_count": 3
    }
  ]
}
```

---

### 2. Get Device Details
**GET** `/api/v1/admin/devices/<device_id>`

Get detailed device information including auth and config.

**Authentication:** Admin Token

**Response:** `200 OK`
```json
{
  "status": "success",
  "device": {...},
  "auth_records": [...],
  "configurations": {...}
}
```

---

### 3. Update Device Status
**PUT** `/api/v1/admin/devices/<device_id>/status`

Update device status.

**Authentication:** Admin Token

**Request Body:**
```json
{
  "status": "maintenance"
}
```

**Valid statuses:** `active`, `inactive`, `maintenance`

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Device status updated from active to maintenance",
  "device_id": 1,
  "old_status": "active",
  "new_status": "maintenance"
}
```

---

### 4. Get System Statistics
**GET** `/api/v1/admin/stats`

Get system statistics.

**Authentication:** Admin Token

**Response:** `200 OK`
```json
{
  "status": "success",
  "timestamp": "2025-07-02T14:30:00Z",
  "device_stats": {
    "total": 150,
    "active": 120,
    "inactive": 20,
    "maintenance": 10,
    "online": 95,
    "offline": 25
  },
  "auth_stats": {
    "total_records": 150,
    "active_records": 145
  },
  "config_stats": {
    "total_configs": 450,
    "active_configs": 420
  }
}
```

---

### 5. Delete Device
**DELETE** `/api/v1/admin/devices/<device_id>`

Delete a device and all related data.

**Authentication:** Admin Token

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Device Smart Sensor 001 deleted successfully",
  "device_id": 1,
  "note": "Telemetry data in IoTDB is not automatically deleted"
}
```

---

### 6. Get Cache Statistics
**GET** `/api/v1/admin/cache/device-status`

Get statistics about the device status cache.

**Authentication:** Admin Token

**Response:** `200 OK`
```json
{
  "status": "success",
  "cache_stats": {
    "device_status_count": 150,
    "device_lastseen_count": 150,
    "redis_memory_used": "2.5M",
    "redis_uptime": 86400,
    "redis_version": "7.0.0"
  }
}
```

---

### 7. Clear All Device Cache
**DELETE** `/api/v1/admin/cache/device-status`

Clear all device status cache data from Redis.

**Authentication:** Admin Token

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "All device status caches cleared successfully"
}
```

---

### 8. Clear Device Cache
**DELETE** `/api/v1/admin/cache/devices/<device_id>`

Clear cached data for a specific device.

**Authentication:** Admin Token

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Cache cleared for device 1"
}
```

---

### 9. Get Redis-DB Sync Status
**GET** `/api/v1/admin/redis-db-sync/status`

Get Redis-to-Database synchronization status.

**Authentication:** Admin Token

**Response:** `200 OK`
```json
{
  "status": "success",
  "redis_db_sync": {
    "enabled": true,
    "redis_available": true,
    "callback_count": 2
  }
}
```

---

### 10. Enable Redis-DB Sync
**POST** `/api/v1/admin/redis-db-sync/enable`

Enable Redis-to-Database synchronization.

**Authentication:** Admin Token

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Redis-to-Database synchronization enabled"
}
```

---

### 11. Disable Redis-DB Sync
**POST** `/api/v1/admin/redis-db-sync/disable`

Disable Redis-to-Database synchronization.

**Authentication:** Admin Token

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Redis-to-Database synchronization disabled"
}
```

---

### 12. Force Sync Device to Database
**POST** `/api/v1/admin/redis-db-sync/force-sync/<device_id>`

Force synchronization of a specific device status to database.

**Authentication:** Admin Token

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Device 1 status synchronized successfully",
  "sync_result": {
    "device_id": 1,
    "redis_status": "online",
    "database_status": "active"
  }
}
```

---

### 13. Bulk Sync Devices to Database
**POST** `/api/v1/admin/redis-db-sync/bulk-sync`

Force synchronization of all devices with Redis status to database.

**Authentication:** Admin Token

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Bulk synchronization completed",
  "sync_results": {
    "total_devices": 150,
    "synced_devices": 145,
    "failed_devices": 0,
    "skipped_devices": 5,
    "details": [...]
  }
}
```

---

## System Health

**Base Path:** `/`

### 1. Root Endpoint
**GET** `/`

Get API information.

**Authentication:** None

**Response:** `200 OK`
```json
{
  "name": "IoT Device Connectivity Layer",
  "version": "1.0.0",
  "description": "REST API for IoT device connectivity and telemetry data management",
  "endpoints": {
    "health": "/health",
    "devices": "/api/v1/devices",
    "admin": "/api/v1/admin",
    "mqtt": "/api/v1/mqtt"
  },
  "documentation": "See README.md for API documentation"
}
```

---

### 2. Health Check
**GET** `/health`

Basic health check endpoint.

**Authentication:** None

**Query Parameters:**
- `detailed` (optional): Set to "true" for detailed health info

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "message": "IoT Connectivity Layer is running",
  "version": "1.0.0"
}
```

**Detailed Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-02T14:30:00Z",
  "services": {
    "database": "connected",
    "redis": "connected",
    "iotdb": "connected",
    "mqtt": "connected"
  },
  "system": {
    "cpu_usage": 25.5,
    "memory_usage": 45.2,
    "disk_usage": 60.0
  }
}
```

---

### 3. System Status
**GET** `/status`

Detailed system status and metrics.

**Authentication:** None

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2025-07-02T14:30:00Z",
  "services": {
    "database": {
      "status": "connected",
      "type": "postgresql",
      "response_time_ms": 5
    },
    "redis": {
      "status": "connected",
      "memory_used": "2.5M",
      "uptime_seconds": 86400
    },
    "iotdb": {
      "status": "connected",
      "host": "localhost",
      "port": 6667
    },
    "mqtt": {
      "status": "connected",
      "broker": "localhost:1883"
    }
  },
  "system": {
    "cpu_usage_percent": 25.5,
    "memory_usage_percent": 45.2,
    "disk_usage_percent": 60.0
  }
}
```

---

### 4. Prometheus Metrics
**GET** `/metrics`

Prometheus metrics endpoint for monitoring.

**Authentication:** None

**Response:** `200 OK` (text/plain)
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/v1/devices/status",status="200"} 1523

# HELP http_request_duration_seconds HTTP request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/devices/status",le="0.1"} 1200
...
```

---

## Quick Reference Tables

### Endpoints by Category

| Category | Endpoint Count | Base Path |
|----------|----------------|-----------|
| Device Management | 12 | `/api/v1/devices` |
| Telemetry Data | 7 | `/api/v1/telemetry` |
| MQTT Management | 10 | `/api/v1/mqtt` |
| Device Control | 3 | `/api/v1/devices/<id>/control` |
| Administration | 13 | `/api/v1/admin` |
| System Health | 4 | `/` |
| **Total** | **49** | - |

---

### Authentication Summary

| Auth Type | Header | Endpoints |
|-----------|--------|-----------|
| **None** | - | 10 endpoints (health, registration, public status) |
| **API Key** | `X-API-Key: <key>` | 20 endpoints (device operations) |
| **Admin Token** | `Authorization: admin <token>` | 19 endpoints (admin operations) |

---

### HTTP Status Codes

| Code | Meaning | Common Scenarios |
|------|---------|------------------|
| `200` | OK | Successful GET, PUT, DELETE requests |
| `201` | Created | Successful POST (device registration, telemetry) |
| `400` | Bad Request | Invalid request body, missing required fields |
| `401` | Unauthorized | Missing or invalid API key/admin token |
| `403` | Forbidden | Device accessing another device's data |
| `404` | Not Found | Device or resource not found |
| `409` | Conflict | Device name already exists |
| `500` | Internal Server Error | Server-side errors, database issues |
| `503` | Service Unavailable | Service (Redis, IoTDB, MQTT) not available |

---

### Common Query Parameters

| Parameter | Type | Description | Default | Used In |
|-----------|------|-------------|---------|---------|
| `limit` | integer | Max records to return | 100 | Telemetry, device lists |
| `offset` | integer | Pagination offset | 0 | Device lists |
| `start_time` | string | Start time (ISO 8601 or relative) | -24h | Telemetry queries |
| `end_time` | string | End time (ISO 8601) | now | Telemetry queries |
| `detailed` | boolean | Include detailed info | false | Health checks |
| `field` | string | Field to aggregate | - | Aggregated telemetry |
| `aggregation` | string | Aggregation function | mean | Aggregated telemetry |
| `window` | string | Time window | 1h | Aggregated telemetry |

---

### Time Format Examples

**Relative Time:**
- `-1h` - Last 1 hour
- `-24h` - Last 24 hours
- `-7d` - Last 7 days
- `-30d` - Last 30 days

**ISO 8601:**
- `2025-07-02T14:30:00Z` - UTC time
- `2025-07-02T14:30:00+00:00` - UTC with timezone

---

## Error Response Format

All error responses follow this structure:

```json
{
  "error": "Error Type",
  "message": "Detailed error message"
}
```

**Examples:**

```json
{
  "error": "API key required",
  "message": "X-API-Key header is required"
}
```

```json
{
  "error": "Device name already exists",
  "message": "Please choose a different device name"
}
```

```json
{
  "error": "Failed to store telemetry data",
  "message": "IoTDB may not be available. Check logs for details."
}
```

---

## Rate Limiting

Rate limits are applied per device (API key) or per IP address:

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Device Registration | 10 requests | 5 minutes (per IP) |
| Telemetry Submission | 100 requests | 1 minute (per device) |
| Heartbeat | 30 requests | 1 minute (per device) |
| MQTT Credentials | 10 requests | 1 minute (per IP) |
| General API | 60 requests | 1 minute (per device/IP) |

**Rate Limit Headers:**
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window

---

## Best Practices

### 1. Device Authentication
- Store API keys securely on devices
- Never expose API keys in client-side code
- Rotate API keys periodically

### 2. Telemetry Submission
- Use MQTT for real-time, high-frequency data
- Use HTTP REST for occasional updates or when MQTT unavailable
- Batch telemetry data when possible
- Include timestamps for accurate time-series data

### 3. Error Handling
- Implement exponential backoff for retries
- Handle rate limiting gracefully
- Check service availability before operations
- Log errors for debugging

### 4. Performance
- Use Redis cache for device status checks
- Query telemetry with appropriate time ranges
- Use aggregated endpoints for analytics
- Implement pagination for large datasets

### 5. Security
- Use HTTPS in production
- Implement TLS for MQTT connections
- Validate all input data
- Monitor for unusual activity

---

## Example Usage Scenarios

### Scenario 1: Device Registration and First Telemetry

```bash
# 1. Register device
curl -X POST http://localhost:5000/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sensor_001",
    "device_type": "temperature_sensor",
    "user_id": "user123"
  }'

# Response includes api_key: "abc123..."

# 2. Submit telemetry
curl -X POST http://localhost:5000/api/v1/devices/telemetry \
  -H "X-API-Key: abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "temperature": 23.5,
      "humidity": 65.2
    }
  }'
```

### Scenario 2: Monitoring Device Fleet

```bash
# 1. Get all device statuses
curl http://localhost:5000/api/v1/devices/statuses

# 2. Get specific device details
curl http://localhost:5000/api/v1/devices/1/status

# 3. Get system statistics (admin)
curl http://localhost:5000/api/v1/admin/stats \
  -H "Authorization: admin your_token"
```

### Scenario 3: Querying Historical Data

```bash
# 1. Get last 24 hours of data
curl "http://localhost:5000/api/v1/telemetry/1?start_time=-24h&limit=1000" \
  -H "X-API-Key: abc123..."

# 2. Get aggregated hourly averages
curl "http://localhost:5000/api/v1/telemetry/1/aggregated?field=temperature&aggregation=mean&window=1h&start_time=-7d" \
  -H "X-API-Key: abc123..."

# 3. Get latest reading
curl "http://localhost:5000/api/v1/telemetry/1/latest" \
  -H "X-API-Key: abc123..."
```

---

## Additional Resources

- **Main Documentation:** [README.md](README.md)
- **IoTDB Integration:** [docs/iotdb_integration.md](docs/iotdb_integration.md)
- **Device Status Cache:** [docs/device_status_cache.md](docs/device_status_cache.md)
- **ESP32 Examples:** [esp32_examples/](esp32_examples/)
- **Device Simulator:** [simulators/](simulators/)

---

**Document Version:** 1.0  
**Last Updated:** December 8, 2025  
**IoTFlow Version:** 0.2
