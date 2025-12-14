# Metrics API Usage Guide

## Overview

The IoTFlow Connectivity Layer provides a Prometheus-compatible `/metrics` endpoint that exposes real-time system, Redis, IoTDB, MQTT, and application metrics. This guide shows you how to use the metrics API.

## Endpoint

```
GET /metrics
```

**Authentication:** Admin token required
**Content-Type:** text/plain (Prometheus format)

## Usage Examples

### 1. Using cURL

```bash
# Fetch all metrics
curl -H "Authorization: admin test" http://localhost:5000/metrics

# Get only Redis metrics
curl -s -H "Authorization: admin test" http://localhost:5000/metrics | grep "^redis_"

# Get only IoTDB metrics
curl -s -H "Authorization: admin test" http://localhost:5000/metrics | grep "^iotdb_"

# Get IoTFlow application metrics
curl -s -H "Authorization: admin test" http://localhost:5000/metrics | grep "^iotflow_"

# Get MQTT metrics
curl -s -H "Authorization: admin test" http://localhost:5000/metrics | grep "^mqtt_"

# Get system metrics
curl -s -H "Authorization: admin test" http://localhost:5000/metrics | grep "^system_"
```

### 2. Using Python

See the example script: `examples/metrics_api_demo.py`

```python
import requests

# Fetch metrics
response = requests.get(
    "http://localhost:5000/metrics",
    headers={"Authorization": "admin test"}
)

print(response.text)
```

### 3. Using JavaScript/Node.js

```javascript
const fetch = require('node-fetch');

async function getMetrics() {
    const response = await fetch('http://localhost:5000/metrics', {
        headers: {
            'Authorization': 'admin test'
        }
    });
    
    const metrics = await response.text();
    console.log(metrics);
}

getMetrics();
```

## Available Metrics Categories

### Redis Metrics

| Metric Name | Type | Description |
|------------|------|-------------|
| `redis_status` | Gauge | Redis server status (1=up, 0=down) |
| `redis_memory_used_bytes` | Gauge | Current Redis memory usage in bytes |
| `redis_memory_peak_bytes` | Gauge | Peak Redis memory usage in bytes |
| `redis_memory_fragmentation_ratio` | Gauge | Memory fragmentation ratio |
| `redis_keys_total` | Gauge | Total number of keys in Redis |
| `redis_keys_evicted_total` | Counter | Total number of evicted keys |
| `redis_commands_processed_total` | Counter | Total commands processed |
| `redis_cache_hits_total` | Counter | Total cache hits |
| `redis_cache_misses_total` | Counter | Total cache misses |

### IoTDB Metrics

| Metric Name | Type | Description |
|------------|------|-------------|
| `iotdb_connection_status` | Gauge | IoTDB connection status (1=connected, 0=disconnected) |
| `iotdb_query_success_rate` | Gauge | Query success rate percentage |
| `iotdb_write_success_rate` | Gauge | Write success rate percentage |

### IoTFlow Application Metrics

| Metric Name | Type | Description |
|------------|------|-------------|
| `iotflow_devices_total` | Gauge | Total number of registered devices |
| `iotflow_devices_active` | Gauge | Number of active devices |
| `iotflow_devices_online` | Gauge | Number of online devices |
| `iotflow_users_total` | Gauge | Total number of registered users |
| `iotflow_telemetry_messages_total` | Counter | Total telemetry messages received |
| `iotflow_control_commands_total` | Counter | Total control commands sent (with status label) |

### MQTT Metrics

| Metric Name | Type | Description |
|------------|------|-------------|
| `mqtt_connections_total` | Gauge | Total MQTT connections |
| `mqtt_connections_active` | Gauge | Active MQTT connections |
| `mqtt_messages_received_total` | Counter | Total MQTT messages received |
| `mqtt_messages_sent_total` | Counter | Total MQTT messages sent |
| `mqtt_messages_dropped_total` | Counter | Total MQTT messages dropped |
| `mqtt_messages_queued` | Gauge | Messages currently queued |
| `mqtt_topics_total` | Gauge | Total number of MQTT topics |
| `mqtt_subscriptions_total` | Gauge | Total number of subscriptions |
| `mqtt_bytes_sent_total` | Counter | Total bytes sent via MQTT |
| `mqtt_bytes_received_total` | Counter | Total bytes received via MQTT |

### System Metrics

| Metric Name | Type | Description |
|------------|------|-------------|
| `system_cpu_usage_percent` | Gauge | CPU usage percentage |
| `system_cpu_cores_total` | Gauge | Total number of CPU cores |
| `system_load_average` | Gauge | System load average (with period label: 1min, 5min, 15min) |
| `system_memory_usage_percent` | Gauge | Memory usage percentage |
| `system_memory_total_bytes` | Gauge | Total system memory in bytes |
| `system_memory_used_bytes` | Gauge | Used system memory in bytes |
| `system_disk_usage_percent` | Gauge | Disk usage percentage (with path label) |
| `system_disk_total_bytes` | Gauge | Total disk space in bytes (with path label) |
| `system_disk_used_bytes` | Gauge | Used disk space in bytes (with path label) |
| `system_disk_io_read_bytes_total` | Counter | Total disk I/O bytes read (with device label) |
| `system_disk_io_write_bytes_total` | Counter | Total disk I/O bytes written (with device label) |
| `system_network_bytes_sent_total` | Counter | Total network bytes sent |
| `system_network_bytes_received_total` | Counter | Total network bytes received |

### HTTP Request Metrics

| Metric Name | Type | Description |
|------------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests (with method, endpoint, status labels) |
| `http_request_latency_seconds` | Histogram | HTTP request latency (with method, endpoint labels) |
| `http_requests_in_progress` | Gauge | HTTP requests currently being processed |

### Application Info

| Metric Name | Type | Description |
|------------|------|-------------|
| `app_info` | Info | Application version and build information |
| `app_uptime_seconds` | Gauge | Application uptime in seconds |
| `app_start_time_seconds` | Gauge | Application start time as Unix timestamp |

## Integration with Monitoring Tools

### Prometheus Configuration

Add this to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'iotflow-connectivity'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scheme: 'http'
    # Add admin authentication
    authorization:
      type: Bearer
      credentials: 'admin test'
```

### Grafana Dashboard

1. Add Prometheus as a data source in Grafana
2. Create a new dashboard
3. Use PromQL queries like:
   - `redis_memory_used_bytes` - Redis memory usage
   - `iotdb_connection_status` - IoTDB connection status
   - `rate(iotflow_telemetry_messages_total[5m])` - Telemetry message rate
   - `system_cpu_usage_percent` - CPU usage
   - `system_memory_usage_percent` - Memory usage

### Example PromQL Queries

```promql
# Redis cache hit rate
rate(redis_cache_hits_total[5m]) / (rate(redis_cache_hits_total[5m]) + rate(redis_cache_misses_total[5m]))

# MQTT message throughput
rate(mqtt_messages_received_total[1m])

# IoTDB availability (over last hour)
avg_over_time(iotdb_connection_status[1h])

# System CPU usage trend
avg_over_time(system_cpu_usage_percent[15m])

# HTTP request rate by endpoint
sum(rate(http_requests_total[5m])) by (endpoint)
```

## Real-time Monitoring Script

Here's a simple script to monitor key metrics in real-time:

```python
#!/usr/bin/env python3
import requests
import time
import os

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def get_metric_value(metrics_text, metric_name):
    for line in metrics_text.split('\n'):
        if line.startswith(metric_name + ' '):
            return float(line.split()[1])
    return None

def monitor():
    url = "http://localhost:5000/metrics"
    headers = {"Authorization": "admin test"}
    
    while True:
        try:
            response = requests.get(url, headers=headers)
            metrics = response.text
            
            clear_screen()
            print("=" * 60)
            print("IoTFlow Real-time Metrics Monitor")
            print("=" * 60)
            print(f"\n⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            print("🔴 Redis")
            print(f"  Status: {'🟢 UP' if get_metric_value(metrics, 'redis_status') == 1.0 else '🔴 DOWN'}")
            print(f"  Memory: {get_metric_value(metrics, 'redis_memory_used_bytes')/1024/1024:.2f} MB")
            print(f"  Keys: {get_metric_value(metrics, 'redis_keys_total'):.0f}")
            
            print("\n💾 IoTDB")
            print(f"  Status: {'🟢 Connected' if get_metric_value(metrics, 'iotdb_connection_status') == 1.0 else '🔴 Disconnected'}")
            print(f"  Query Success Rate: {get_metric_value(metrics, 'iotdb_query_success_rate'):.1f}%")
            
            print("\n📡 MQTT")
            print(f"  Connections: {get_metric_value(metrics, 'mqtt_connections_active'):.0f}")
            print(f"  Topics: {get_metric_value(metrics, 'mqtt_topics_total'):.0f}")
            
            print("\n🖥️  System")
            print(f"  CPU: {get_metric_value(metrics, 'system_cpu_usage_percent'):.1f}%")
            print(f"  Memory: {get_metric_value(metrics, 'system_memory_usage_percent'):.1f}%")
            
            print("\n📊 IoTFlow")
            print(f"  Total Devices: {get_metric_value(metrics, 'iotflow_devices_total'):.0f}")
            print(f"  Active Devices: {get_metric_value(metrics, 'iotflow_devices_active'):.0f}")
            print(f"  Online Devices: {get_metric_value(metrics, 'iotflow_devices_online'):.0f}")
            
            print("\n" + "=" * 60)
            print("Press Ctrl+C to exit")
            
            time.sleep(5)  # Update every 5 seconds
            
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor()
```

Save this as `examples/monitor_metrics.py` and run it for real-time monitoring.

## Notes

- All metrics are collected fresh on each request to the `/metrics` endpoint
- The endpoint requires admin authentication
- Metrics follow the Prometheus text exposition format
- Counters continuously increase and should be used with `rate()` function in PromQL
- Gauges represent current values and can go up or down

## Troubleshooting

### Authentication Error

If you get a 401 error:
```bash
# Make sure you're using the correct admin token
curl -H "Authorization: admin YOUR_ADMIN_TOKEN" http://localhost:5000/metrics
```

### Connection Refused

If you can't connect:
```bash
# Check if Flask is running
curl http://localhost:5000/

# Check the port
lsof -i :5000
```

### Empty Metrics

If some metrics are 0 or empty:
- Redis metrics require Redis to be running
- IoTDB metrics require IoTDB connection
- MQTT metrics require MQTT broker to be configured
- IoTFlow device metrics require devices to be registered

## See Also

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [API Endpoints Documentation](../docs/api/API_ENDPOINTS_SUMMARY.md)
