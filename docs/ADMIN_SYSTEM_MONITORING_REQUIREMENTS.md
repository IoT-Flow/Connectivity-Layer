# Admin System Monitoring with Prometheus - Requirements

**Date:** December 10, 2025  
**Backend:** Flask (Connectivity Layer - Python)  
**Monitoring Stack:** Prometheus + Grafana  
**Target:** Admin system statistics and monitoring endpoints

---

## 🎯 Objective

Implement Prometheus-compatible metrics endpoints in the Flask backend (Connectivity Layer) for system monitoring, statistics, and health checks. Metrics will be exposed in Prometheus format and scraped by Prometheus server, then visualized in Grafana.

---

## 📊 Architecture

```
Flask App (Connectivity Layer)
    ↓ (exposes /metrics)
Prometheus (scrapes metrics every 15s)
    ↓ (stores time-series data)
Grafana (queries & visualizes)
    ↓ (displays dashboards)
Admin User
```

---

## 📊 Required Endpoints

### 1. Prometheus Metrics Endpoint
**Endpoint:** `GET /metrics`  
**Authentication:** Optional (can be restricted by IP in production)  
**Purpose:** Expose all system metrics in Prometheus format for scraping

**Prometheus Metrics Format:**
```prometheus
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{version="3.11.5",implementation="CPython"} 1.0

# HELP flask_app_uptime_seconds Application uptime in seconds
# TYPE flask_app_uptime_seconds counter
flask_app_uptime_seconds 453840

# HELP system_cpu_usage_percent CPU usage percentage
# TYPE system_cpu_usage_percent gauge
system_cpu_usage_percent 45.2

# HELP system_cpu_count Number of CPU cores
# TYPE system_cpu_count gauge
system_cpu_count 8

# HELP system_memory_total_bytes Total system memory in bytes
# TYPE system_memory_total_bytes gauge
system_memory_total_bytes 17179869184

# HELP system_memory_used_bytes Used system memory in bytes
# TYPE system_memory_used_bytes gauge
system_memory_used_bytes 8589934592

# HELP system_memory_usage_percent Memory usage percentage
# TYPE system_memory_usage_percent gauge
system_memory_usage_percent 50.0

# HELP system_disk_total_bytes Total disk space in bytes
# TYPE system_disk_total_bytes gauge
system_disk_total_bytes{path="/"} 536870912000

# HELP system_disk_used_bytes Used disk space in bytes
# TYPE system_disk_used_bytes gauge
system_disk_used_bytes{path="/"} 268435456000

# HELP system_disk_usage_percent Disk usage percentage
# TYPE system_disk_usage_percent gauge
system_disk_usage_percent{path="/"} 50.0

# HELP network_bytes_sent_total Total bytes sent
# TYPE network_bytes_sent_total counter
network_bytes_sent_total 1073741824

# HELP network_bytes_received_total Total bytes received
# TYPE network_bytes_received_total counter
network_bytes_received_total 2147483648
```

---

### 2. Database Metrics (in /metrics)
**Included in:** `GET /metrics`  
**Purpose:** Expose database performance and usage metrics

**Prometheus Metrics:**
```prometheus
# HELP database_connection_pool_size Database connection pool size
# TYPE database_connection_pool_size gauge
database_connection_pool_size 20

# HELP database_connections_active Active database connections
# TYPE database_connections_active gauge
database_connections_active 5

# HELP database_connections_idle Idle database connections
# TYPE database_connections_idle gauge
database_connections_idle 15

# HELP database_table_rows Row count per table
# TYPE database_table_rows gauge
database_table_rows{table="devices"} 1500
database_table_rows{table="users"} 50
database_table_rows{table="device_auth"} 1500
database_table_rows{table="device_configurations"} 3000

# HELP database_queries_total Total database queries executed
# TYPE database_queries_total counter
database_queries_total 150000

# HELP database_query_duration_seconds Database query execution time
# TYPE database_query_duration_seconds histogram
database_query_duration_seconds_bucket{le="0.005"} 10000
database_query_duration_seconds_bucket{le="0.01"} 25000
database_query_duration_seconds_bucket{le="0.025"} 40000
database_query_duration_seconds_bucket{le="0.05"} 45000
database_query_duration_seconds_bucket{le="0.1"} 48000
database_query_duration_seconds_bucket{le="+Inf"} 50000
database_query_duration_seconds_sum 775.5
database_query_duration_seconds_count 50000
```

---

### 3. MQTT Broker Metrics (in /metrics)
**Included in:** `GET /metrics`  
**Purpose:** Expose MQTT broker performance and connection metrics

**Prometheus Metrics:**
```prometheus
# HELP mqtt_broker_uptime_seconds MQTT broker uptime in seconds
# TYPE mqtt_broker_uptime_seconds counter
mqtt_broker_uptime_seconds 453840

# HELP mqtt_connections_total Total MQTT connections
# TYPE mqtt_connections_total gauge
mqtt_connections_total 150

# HELP mqtt_connections_active Active MQTT connections
# TYPE mqtt_connections_active gauge
mqtt_connections_active 120

# HELP mqtt_messages_received_total Total MQTT messages received
# TYPE mqtt_messages_received_total counter
mqtt_messages_received_total 1000000

# HELP mqtt_messages_sent_total Total MQTT messages sent
# TYPE mqtt_messages_sent_total counter
mqtt_messages_sent_total 1200000

# HELP mqtt_messages_dropped_total Total MQTT messages dropped
# TYPE mqtt_messages_dropped_total counter
mqtt_messages_dropped_total 100

# HELP mqtt_messages_queued Current queued messages
# TYPE mqtt_messages_queued gauge
mqtt_messages_queued 50

# HELP mqtt_subscriptions_total Total active subscriptions
# TYPE mqtt_subscriptions_total gauge
mqtt_subscriptions_total 300

# HELP mqtt_topics_total Total topics
# TYPE mqtt_topics_total gauge
mqtt_topics_total 150

# HELP mqtt_bandwidth_bytes_received_total Total bytes received via MQTT
# TYPE mqtt_bandwidth_bytes_received_total counter
mqtt_bandwidth_bytes_received_total 536870912

# HELP mqtt_bandwidth_bytes_sent_total Total bytes sent via MQTT
# TYPE mqtt_bandwidth_bytes_sent_total counter
mqtt_bandwidth_bytes_sent_total 1073741824

# HELP mqtt_message_rate_per_second Current message rate per second
# TYPE mqtt_message_rate_per_second gauge
mqtt_message_rate_per_second 150.5
```

---

### 4. IoTDB Metrics (in /metrics)
**Included in:** `GET /metrics`  
**Purpose:** Expose IoTDB time-series database metrics

**Prometheus Metrics:**
```prometheus
# HELP iotdb_status IoTDB status (1 = running, 0 = down)
# TYPE iotdb_status gauge
iotdb_status 1

# HELP iotdb_storage_groups_total Total storage groups
# TYPE iotdb_storage_groups_total gauge
iotdb_storage_groups_total 5

# HELP iotdb_storage_size_bytes Storage size in bytes
# TYPE iotdb_storage_size_bytes gauge
iotdb_storage_size_bytes{type="total"} 5368709120
iotdb_storage_size_bytes{type="data"} 4294967296
iotdb_storage_size_bytes{type="wal"} 536870912
iotdb_storage_size_bytes{type="index"} 536870912

# HELP iotdb_timeseries_total Total timeseries
# TYPE iotdb_timeseries_total gauge
iotdb_timeseries_total 1500

# HELP iotdb_timeseries_active Active timeseries
# TYPE iotdb_timeseries_active gauge
iotdb_timeseries_active 1200

# HELP iotdb_devices_total Total devices in IoTDB
# TYPE iotdb_devices_total gauge
iotdb_devices_total 150

# HELP iotdb_data_points_total Total data points stored
# TYPE iotdb_data_points_total counter
iotdb_data_points_total 50000000

# HELP iotdb_write_rate_per_second Current write rate per second
# TYPE iotdb_write_rate_per_second gauge
iotdb_write_rate_per_second 5000

# HELP iotdb_read_rate_per_second Current read rate per second
# TYPE iotdb_read_rate_per_second gauge
iotdb_read_rate_per_second 2000

# HELP iotdb_write_latency_seconds Write operation latency
# TYPE iotdb_write_latency_seconds histogram
iotdb_write_latency_seconds_sum 26.0
iotdb_write_latency_seconds_count 5000

# HELP iotdb_read_latency_seconds Read operation latency
# TYPE iotdb_read_latency_seconds histogram
iotdb_read_latency_seconds_sum 7.6
iotdb_read_latency_seconds_count 2000
```

---

### 5. Redis Cache Metrics (in /metrics)
**Included in:** `GET /metrics`  
**Purpose:** Expose Redis cache performance metrics

**Prometheus Metrics:**
```prometheus
# HELP redis_status Redis status (1 = running, 0 = down)
# TYPE redis_status gauge
redis_status 1

# HELP redis_uptime_seconds Redis uptime in seconds
# TYPE redis_uptime_seconds counter
redis_uptime_seconds 453840

# HELP redis_memory_used_bytes Redis memory usage in bytes
# TYPE redis_memory_used_bytes gauge
redis_memory_used_bytes 536870912

# HELP redis_memory_peak_bytes Redis peak memory usage in bytes
# TYPE redis_memory_peak_bytes gauge
redis_memory_peak_bytes 1073741824

# HELP redis_memory_fragmentation_ratio Redis memory fragmentation ratio
# TYPE redis_memory_fragmentation_ratio gauge
redis_memory_fragmentation_ratio 1.2

# HELP redis_keys_total Total keys in Redis
# TYPE redis_keys_total gauge
redis_keys_total 5000

# HELP redis_keys_with_expiry Total keys with expiration set
# TYPE redis_keys_with_expiry gauge
redis_keys_with_expiry 3000

# HELP redis_keys_evicted_total Total evicted keys
# TYPE redis_keys_evicted_total counter
redis_keys_evicted_total 100

# HELP redis_commands_total Total commands processed
# TYPE redis_commands_total counter
redis_commands_total 10000000

# HELP redis_commands_per_second Commands processed per second
# TYPE redis_commands_per_second gauge
redis_commands_per_second 5000

# HELP redis_cache_hit_ratio Cache hit ratio (percentage)
# TYPE redis_cache_hit_ratio gauge
redis_cache_hit_ratio 95.5

# HELP redis_cache_hits_total Total cache hits
# TYPE redis_cache_hits_total counter
redis_cache_hits_total 9550000

# HELP redis_cache_misses_total Total cache misses
# TYPE redis_cache_misses_total counter
redis_cache_misses_total 450000
```

---

### 6. Application Metrics (in /metrics)
**Included in:** `GET /metrics`  
**Purpose:** Expose Flask application-specific metrics

**Prometheus Metrics:**
```prometheus
# HELP flask_http_requests_total Total HTTP requests
# TYPE flask_http_requests_total counter
flask_http_requests_total{method="GET",endpoint="/api/v1/devices",status="200"} 100000
flask_http_requests_total{method="POST",endpoint="/api/v1/telemetry",status="200"} 200000
flask_http_requests_total{method="POST",endpoint="/api/v1/telemetry",status="400"} 500
flask_http_requests_total{method="GET",endpoint="/api/v1/devices",status="401"} 100

# HELP flask_http_request_duration_seconds HTTP request duration
# TYPE flask_http_request_duration_seconds histogram
flask_http_request_duration_seconds_bucket{method="POST",endpoint="/api/v1/telemetry",le="0.01"} 50000
flask_http_request_duration_seconds_bucket{method="POST",endpoint="/api/v1/telemetry",le="0.025"} 150000
flask_http_request_duration_seconds_bucket{method="POST",endpoint="/api/v1/telemetry",le="0.05"} 190000
flask_http_request_duration_seconds_bucket{method="POST",endpoint="/api/v1/telemetry",le="0.1"} 198000
flask_http_request_duration_seconds_bucket{method="POST",endpoint="/api/v1/telemetry",le="+Inf"} 200000
flask_http_request_duration_seconds_sum{method="POST",endpoint="/api/v1/telemetry"} 5100.0
flask_http_request_duration_seconds_count{method="POST",endpoint="/api/v1/telemetry"} 200000

# HELP flask_http_requests_in_progress Current HTTP requests in progress
# TYPE flask_http_requests_in_progress gauge
flask_http_requests_in_progress 12

# HELP iotflow_devices_total Total registered devices
# TYPE iotflow_devices_total gauge
iotflow_devices_total 1500

# HELP iotflow_devices_active Active devices (seen in last 5 minutes)
# TYPE iotflow_devices_active gauge
iotflow_devices_active 1200

# HELP iotflow_telemetry_messages_total Total telemetry messages received
# TYPE iotflow_telemetry_messages_total counter
iotflow_telemetry_messages_total 50000000

# HELP iotflow_telemetry_messages_rate Current telemetry message rate per second
# TYPE iotflow_telemetry_messages_rate gauge
iotflow_telemetry_messages_rate 138.9
  },
  "status_codes": {
    "2xx": 450000,
    "3xx": 10000,
    "4xx": 35000,
    "5xx": 5000
  },
  "errors": {
    "total_today": 5000,
    "rate_per_hour": 208,
    "top_errors": [
      {
        "type": "ValidationError",
        "count": 3000,
        "percentage": 60.0
      },
      {
        "type": "DatabaseError",
        "count": 1500,
        "percentage": 30.0
      }
    ]
  },
  "workers": {
    "total": 4,
    "active": 4,
    "idle": 0
  }
}
```

---

### 7. Device Statistics
**Endpoint:** `GET /api/v1/admin/stats/devices`  
**Authentication:** Admin JWT Token required  
**Purpose:** Get device-related statistics

**Response Structure:**
```json
{
  "timestamp": "2025-12-10T10:00:00Z",
  "devices": {
    "total": 1500,
    "online": 1200,
    "offline": 300,
    "by_type": {
      "temperature_sensor": 500,
      "humidity_sensor": 400,
      "motion_sensor": 300,
      "camera": 200,
      "other": 100
    },
    "by_status": {
      "active": 1200,
      "inactive": 200,
      "error": 50,
      "maintenance": 50
    }
  },
  "telemetry": {
    "total_points_today": 1200000,
    "total_points_this_hour": 50000,
    "rate_per_second": 13.9,
    "avg_interval_seconds": 30
  },
  "alerts": {
    "active": 25,
    "resolved_today": 100,
    "critical": 5,
    "warning": 15,
    "info": 5
  },
  "top_devices": [
    {
      "device_id": 123,
      "name": "Sensor-001",
      "message_count": 10000,
      "last_seen": "2025-12-10T09:59:00Z"
    },
    {
      "device_id": 456,
      "name": "Sensor-002",
      "message_count": 9500,
      "last_seen": "2025-12-10T09:58:30Z"
    }
  ]
}
```

---

### 8. Health Check
**Endpoint:** `GET /api/v1/admin/health`  
**Authentication:** Admin JWT Token required  
**Purpose:** Comprehensive system health check

**Response Structure:**
```json
{
  "timestamp": "2025-12-10T10:00:00Z",
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5.2,
      "message": "Connected to PostgreSQL"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 1.5,
      "message": "Connected to Redis"
    },
    "iotdb": {
      "status": "healthy",
      "response_time_ms": 8.3,
      "message": "Connected to IoTDB"
    },
    "mqtt": {
      "status": "healthy",
      "response_time_ms": 3.1,
      "message": "MQTT broker responding"
    },
    "disk_space": {
      "status": "healthy",
      "free_percent": 50.0,
      "message": "Sufficient disk space"
    },
    "memory": {
      "status": "warning",
      "used_percent": 85.0,
      "message": "Memory usage high"
    },
    "cpu": {
      "status": "healthy",
      "usage_percent": 45.0,
      "message": "CPU usage normal"
    }
  },
  "overall_health_score": 85.7
}
```

---

### 9. Real-Time Monitoring Stream
**Endpoint:** `GET /api/v1/admin/monitor/stream` (Server-Sent Events)  
**Authentication:** Admin JWT Token required  
**Purpose:** Real-time system monitoring stream

**Response Format:** Server-Sent Events (SSE)

**Event Types:**
```json
// CPU Update Event
{
  "event": "cpu",
  "data": {
    "timestamp": "2025-12-10T10:00:00Z",
    "usage_percent": 45.2,
    "load_average": [2.5, 2.3, 2.1]
  }
}

// Memory Update Event
{
  "event": "memory",
  "data": {
    "timestamp": "2025-12-10T10:00:00Z",
    "used_mb": 8192,
    "percent_used": 50.0
  }
}

// MQTT Message Rate Event
{
  "event": "mqtt",
  "data": {
    "timestamp": "2025-12-10T10:00:00Z",
    "messages_per_second": 150.5,
    "active_connections": 120
  }
}

// Alert Event
{
  "event": "alert",
  "data": {
    "timestamp": "2025-12-10T10:00:00Z",
    "severity": "warning",
    "component": "memory",
    "message": "Memory usage exceeded 85%"
  }
}
```

---

### 10. Historical Metrics
**Endpoint:** `GET /api/v1/admin/stats/historical`  
**Authentication:** Admin JWT Token required  
**Purpose:** Get historical system metrics

**Query Parameters:**
- `metric` (required): Type of metric (cpu, memory, requests, mqtt_messages, etc.)
- `start_time` (required): ISO 8601 timestamp
- `end_time` (required): ISO 8601 timestamp
- `interval` (optional): Aggregation interval (1m, 5m, 15m, 1h, 1d) - default: 1h

**Response Structure:**
```json
{
  "metric": "cpu",
  "interval": "1h",
  "start_time": "2025-12-09T10:00:00Z",
  "end_time": "2025-12-10T10:00:00Z",
  "data_points": [
    {
      "timestamp": "2025-12-09T10:00:00Z",
      "value": 42.5,
      "min": 35.0,
      "max": 55.0,
      "avg": 42.5
    },
    {
      "timestamp": "2025-12-09T11:00:00Z",
      "value": 45.2,
      "min": 38.0,
      "max": 60.0,
      "avg": 45.2
    }
  ],
  "summary": {
    "min": 35.0,
    "max": 75.0,
    "avg": 48.3,
    "total_points": 24
  }
}
```

---

---

## 🔒 Security Requirements

### /metrics Endpoint Security
1. **No Authentication Required** for Prometheus scraping (scraper runs on trusted network)
2. **IP Whitelisting** (recommended): Restrict /metrics to Prometheus server IP only
3. **Network Isolation**: Keep /metrics on internal network, not exposed to internet
4. **Optional Basic Auth**: Can add HTTP Basic Auth if needed

### Admin Dashboard Endpoints
1. **JWT Token Required**: Dashboard endpoints require valid admin JWT token
2. **Role Verification**: User must have `is_admin: true`
3. **Rate Limiting**: 100 requests/minute per admin
4. **CORS**: Configure appropriate CORS headers for frontend access

### Security Headers
```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

---

## 📦 Required Python Packages

```bash
# Add to requirements.txt
prometheus-client>=0.19.0  # Prometheus metrics export
psutil>=5.9.0             # System monitoring (CPU, memory, disk)
redis>=5.0.0              # Redis metrics
psycopg2-binary>=2.9.0    # PostgreSQL metrics
paho-mqtt>=1.6.0          # MQTT monitoring
```

---

## 🏗️ Implementation Structure

### Directory Structure
```
Connectivity-Layer/
├── src/
│   ├── metrics.py                 # Prometheus metrics definitions
│   ├── routes/
│   │   └── metrics_route.py       # /metrics endpoint
│   └── services/
│       ├── metrics_collector.py   # Collect and update all metrics
│       ├── system_metrics.py      # System metrics (CPU, memory, disk)
│       ├── database_metrics.py    # Database metrics
│       ├── mqtt_metrics.py        # MQTT broker metrics
│       ├── iotdb_metrics.py       # IoTDB metrics
│       └── redis_metrics.py       # Redis metrics
├── tests/
│   └── test_metrics.py            # Metrics tests
└── prometheus/
    ├── prometheus.yml             # Prometheus configuration
    └── alerting_rules.yml         # Alert rules
```

### Example Implementation

**src/metrics.py** - Define all Prometheus metrics:
```python
from prometheus_client import Counter, Gauge, Histogram, Info

# Application info
app_info = Info('flask_app', 'Flask application information')

# System metrics
cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
memory_used_bytes = Gauge('system_memory_used_bytes', 'Used memory in bytes')
disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage', ['path'])

# Database metrics
db_connections_active = Gauge('database_connections_active', 'Active database connections')
db_table_rows = Gauge('database_table_rows', 'Row count per table', ['table'])
db_query_duration = Histogram('database_query_duration_seconds', 'Database query duration')

# MQTT metrics
mqtt_connections = Gauge('mqtt_connections_total', 'Total MQTT connections')
mqtt_messages_received = Counter('mqtt_messages_received_total', 'Total MQTT messages received')
mqtt_messages_sent = Counter('mqtt_messages_sent_total', 'Total MQTT messages sent')

# IoTDB metrics
iotdb_status = Gauge('iotdb_status', 'IoTDB status (1=running, 0=down)')
iotdb_timeseries = Gauge('iotdb_timeseries_total', 'Total timeseries')
iotdb_data_points = Counter('iotdb_data_points_total', 'Total data points stored')

# Redis metrics
redis_status = Gauge('redis_status', 'Redis status (1=running, 0=down)')
redis_memory_used = Gauge('redis_memory_used_bytes', 'Redis memory usage')
redis_keys_total = Gauge('redis_keys_total', 'Total keys in Redis')

# Application metrics
http_requests_total = Counter('flask_http_requests_total', 'Total HTTP requests', 
                               ['method', 'endpoint', 'status'])
http_request_duration = Histogram('flask_http_request_duration_seconds', 'HTTP request duration',
                                   ['method', 'endpoint'])
http_requests_in_progress = Gauge('flask_http_requests_in_progress', 'Current requests in progress')

# IoTFlow specific
iotflow_devices_total = Gauge('iotflow_devices_total', 'Total registered devices')
iotflow_devices_active = Gauge('iotflow_devices_active', 'Active devices')
iotflow_telemetry_messages = Counter('iotflow_telemetry_messages_total', 'Total telemetry messages')
```

**src/routes/metrics_route.py** - Expose /metrics endpoint:
```python
from flask import Blueprint, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
@require_admin
def get_mqtt_stats():
    """Get MQTT broker statistics"""
    stats = mqtt_monitor.get_stats()
    return jsonify(stats), 200

@admin_monitoring_bp.route('/api/v1/admin/health', methods=['GET'])
@require_admin
def health_check():
    """Comprehensive health check"""
    health = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'status': 'healthy',
        'checks': {
            'database': database_monitor.check_health(),
            'redis': redis_monitor.check_health(),
            'mqtt': mqtt_monitor.check_health(),
            'iotdb': iotdb_monitor.check_health(),
        }
    }
    
    # Calculate overall health
    healthy_count = sum(1 for check in health['checks'].values() 
                       if check['status'] == 'healthy')
    total_checks = len(health['checks'])
    health['overall_health_score'] = (healthy_count / total_checks) * 100
    
    status_code = 200 if health['overall_health_score'] > 50 else 503
    return jsonify(health), status_code
```

**src/services/system_monitor.py:**
```python
import psutil
import platform
from datetime import datetime

class SystemMonitor:
    def __init__(self):
        self.boot_time = datetime.fromtimestamp(psutil.boot_time())
    
    def get_stats(self):
        """Collect comprehensive system statistics"""
        uptime = datetime.now() - self.boot_time
        
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'system': {
                'uptime': str(uptime),
                'uptime_seconds': int(uptime.total_seconds()),
                'python_version': platform.python_version(),
                'hostname': platform.node(),
                'platform': platform.platform(),
            },
            'cpu': {
                'usage_percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'load_average': list(psutil.getloadavg()),
            },
            'memory': self._get_memory_stats(),
            'disk': self._get_disk_stats(),
            'network': self._get_network_stats(),
        }
    
    def _get_memory_stats(self):
        mem = psutil.virtual_memory()
        return {
            'total_mb': mem.total // (1024 * 1024),
            'used_mb': mem.used // (1024 * 1024),
            'free_mb': mem.free // (1024 * 1024),
            'percent_used': mem.percent,
            'available_mb': mem.available // (1024 * 1024),
        }
    
    def _get_disk_stats(self):
        disk = psutil.disk_usage('/')
        return {
            'total_gb': disk.total // (1024 ** 3),
            'used_gb': disk.used // (1024 ** 3),
            'free_gb': disk.free // (1024 ** 3),
            'percent_used': disk.percent,
        }
    
    def _get_network_stats(self):
        net = psutil.net_io_counters()
        return {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv,
        }
```

**src/middleware/admin_auth.py:**
```python
from functools import wraps
from flask import request, jsonify
import jwt
import os

def require_admin(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Access denied. No token provided.'}), 401
        
        try:
            # Verify token
            payload = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
            
            # Check admin status
            if not payload.get('is_admin'):
                return jsonify({'message': 'Access denied. Admin privileges required.'}), 403
            
            # Attach user info to request
            request.user = payload
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function
```

---

## 🧪 Testing Requirements

### Unit Tests
- Test each monitoring service independently
- Mock external dependencies (Redis, PostgreSQL, MQTT)
- Test error handling and edge cases
- Test data aggregation and formatting

### Integration Tests
- Test endpoint authentication and authorization
- Test rate limiting
- Test response format and structure
- Test health check logic
- Test SSE streaming functionality

### Performance Tests
- Benchmark response times (target: < 100ms for stats endpoints)
- Test concurrent requests (target: 50 concurrent admins)
- Test memory usage during monitoring
- Test streaming performance (SSE)

### Example Test
```python
def test_system_stats_endpoint_requires_admin(client, regular_user_token):
    """Test that system stats endpoint requires admin privileges"""
    response = client.get(
        '/api/v1/admin/stats/system',
        headers={'Authorization': f'Bearer {regular_user_token}'}
    )
    assert response.status_code == 403
    assert 'Admin privileges required' in response.json['message']

def test_system_stats_returns_correct_structure(client, admin_token):
    """Test system stats response structure"""
    response = client.get(
        '/api/v1/admin/stats/system',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 200
    data = response.json
    
    assert 'timestamp' in data
    assert 'system' in data
    assert 'cpu' in data
    assert 'memory' in data
    assert 'disk' in data
    assert 'network' in data
```

---

## 📈 Performance Considerations

### Caching Strategy
```python
from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/1',
    'CACHE_DEFAULT_TIMEOUT': 30  # 30 seconds cache
})

@admin_monitoring_bp.route('/api/v1/admin/stats/system', methods=['GET'])
@require_admin
@cache.cached(timeout=30, key_prefix='system_stats')
def get_system_stats():
    # ... implementation
```

### Async Data Collection
- Use background tasks for expensive operations
- Implement periodic metric collection (every 10 seconds)
- Store recent metrics in Redis for quick retrieval

### Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

@admin_monitoring_bp.route('/api/v1/admin/stats/system', methods=['GET'])
@require_admin
@limiter.limit("60 per minute")
def get_system_stats():
    # ... implementation
```

---

## 🔗 Integration with Dashboard

### JavaScript/TypeScript Client Example
```typescript
// services/adminMonitoringService.ts
import axios from 'axios';

const FLASK_API_URL = process.env.REACT_APP_FLASK_API_URL || 'http://localhost:5000';

export const adminMonitoringService = {
  async getSystemStats() {
    const token = localStorage.getItem('token');
    const response = await axios.get(
      `${FLASK_API_URL}/api/v1/admin/stats/system`,
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    return response.data;
  },

  async getDatabaseStats() {
    const token = localStorage.getItem('token');
    const response = await axios.get(
      `${FLASK_API_URL}/api/v1/admin/stats/database`,
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    return response.data;
  },

  async getMQTTStats() {
    const token = localStorage.getItem('token');
    const response = await axios.get(
      `${FLASK_API_URL}/api/v1/admin/stats/mqtt`,
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    return response.data;
  },

  async getHealthStatus() {
    const token = localStorage.getItem('token');
    const response = await axios.get(
      `${FLASK_API_URL}/api/v1/admin/health`,
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    return response.data;
  },

  // Server-Sent Events for real-time monitoring
  subscribeToRealTimeMonitoring(onMessage: (event: any) => void) {
    const token = localStorage.getItem('token');
    const eventSource = new EventSource(
      `${FLASK_API_URL}/api/v1/admin/monitor/stream?token=${token}`
    );

    eventSource.addEventListener('cpu', (event) => {
      onMessage({ type: 'cpu', data: JSON.parse(event.data) });
    });

    eventSource.addEventListener('memory', (event) => {
      onMessage({ type: 'memory', data: JSON.parse(event.data) });
    });

    eventSource.addEventListener('mqtt', (event) => {
      onMessage({ type: 'mqtt', data: JSON.parse(event.data) });
    });

    eventSource.addEventListener('alert', (event) => {
      onMessage({ type: 'alert', data: JSON.parse(event.data) });
    });

    return () => eventSource.close();
  }
};
```

---

## 📋 Implementation Checklist

### Phase 1: Core Infrastructure (Week 1)
- [ ] Set up admin authentication middleware
- [ ] Implement system monitor service (CPU, memory, disk, network)
- [ ] Implement database monitor service
- [ ] Create base admin monitoring blueprint
- [ ] Add health check endpoint
- [ ] Write unit tests for monitoring services

### Phase 2: Specialized Monitoring (Week 2)
- [ ] Implement MQTT broker monitoring
- [ ] Implement IoTDB monitoring
- [ ] Implement Redis monitoring
- [ ] Implement application metrics collector
- [ ] Add device statistics endpoint
- [ ] Write integration tests

### Phase 3: Advanced Features (Week 3)
- [ ] Implement real-time SSE streaming
- [ ] Add historical metrics endpoint
- [ ] Implement caching strategy
- [ ] Add rate limiting
- [ ] Performance optimization
- [ ] Load testing

### Phase 4: Integration & Documentation (Week 4)
- [ ] Integrate with dashboard frontend
- [ ] Create admin monitoring UI components
- [ ] Add alerting system
- [ ] Write API documentation
- [ ] Create user guide
- [ ] Final testing and deployment

---

## 🎨 Dashboard UI Components

### System Monitoring Dashboard Page
```
┌────────────────────────────────────────────────────────────────────────────┐
│  System Monitoring                                 🔄 Auto-refresh: ON (30s)│
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ 💻 CPU       │  │ 🧠 Memory    │  │ 💾 Disk      │  │ 📡 Network   │ │
│  │ 45.2%        │  │ 8.2 GB       │  │ 250 GB       │  │ 1.5 MB/s     │ │
│  │ 8 cores      │  │ 50% used     │  │ 50% used     │  │ ↑↓ Active    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                                            │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │ 📊 Real-Time CPU Usage                                            │   │
│  │ [~~~~~~~~~~~~~~CPU USAGE CHART~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~]    │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│  ┌────────────────────────────┐  ┌────────────────────────────────────┐ │
│  │ 🗄️  Database               │  │ 📨 MQTT Broker                     │ │
│  │ PostgreSQL 15.3            │  │ 120 active connections             │ │
│  │ 2.0 GB  •  5 active conn.  │  │ 150.5 msg/s  •  300 subscriptions │ │
│  └────────────────────────────┘  └────────────────────────────────────┘ │
│                                                                            │
│  ┌────────────────────────────┐  ┌────────────────────────────────────┐ │
│  │ ⏱️  IoTDB                  │  │ 🔴 Redis Cache                     │ │
│  │ 5.1 GB  •  1500 timeseries │  │ 512 MB  •  5000 keys  •  95.5% hit │ │
│  │ 5000 writes/s              │  │ 5000 commands/s                    │ │
│  └────────────────────────────┘  └────────────────────────────────────┘ │
│                                                                            │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │ ⚠️  Alerts & Warnings                                              │   │
│  │ • Memory usage high (85%) - Warning                                │   │
│  │ • Slow query detected (2.5s) - Info                                │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 📚 Additional Resources

### Documentation Links
- Flask-SSE: https://flask-sse.readthedocs.io/
- psutil: https://psutil.readthedocs.io/
- Prometheus Client: https://prometheus.io/docs/
- Redis Monitoring: https://redis.io/docs/management/monitoring/

### Best Practices
- Cache expensive operations (system stats)
- Use background workers for periodic collection
- Implement proper error handling
- Add logging for all monitoring operations
- Use connection pooling for database queries
- Implement circuit breakers for external services

---

**Status:** Ready for Implementation  
**Priority:** High  
**Estimated Effort:** 3-4 weeks  
**Dependencies:** Flask backend, Redis, PostgreSQL, MQTT broker, IoTDB
