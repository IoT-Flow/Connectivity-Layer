# IoTFlow Examples

This directory contains example scripts and tools for working with the IoTFlow system.

## Available Examples

### 1. metrics_api_demo.py
**Purpose:** Demonstrates how to fetch and parse metrics programmatically

**Usage:**
```bash
python examples/metrics_api_demo.py
```

**Features:**
- Fetches metrics from `/metrics` endpoint
- Parses Prometheus format metrics
- Displays Redis, IoTDB, MQTT, IoTFlow, and system metrics
- Shows how to filter metrics by category

### 2. monitor_metrics.py
**Purpose:** Real-time dashboard for monitoring system health

**Usage:**
```bash
python examples/monitor_metrics.py

# With custom options
python examples/monitor_metrics.py --url http://localhost:5000 --token test --interval 5
```

### 3. device_status_usage.py
**Purpose:** Comprehensive examples of device online/offline status tracking

**Usage:**
```python
# Import in your Flask app
from examples.device_status_usage import create_app, get_all_device_statuses

# See file for 10 different usage examples including:
# - Flask app integration
# - API endpoints
# - Background monitoring
# - Alerts for offline devices
# - WebSocket integration
# - Celery periodic tasks
# - Prometheus metrics
```

**Features:**
- Flask app setup with status tracker
- REST API endpoint examples
- Background task monitoring
- Offline device alerts
- WebSocket real-time updates
- Celery task integration
- Prometheus metrics
- Custom timeout configurations

**Features:**
- Real-time metrics display (refreshes every 5 seconds by default)
- Visual progress bars for CPU and memory
- Color-coded status indicators
- Monitors Redis, IoTDB, MQTT, system resources, and application metrics
- Clean terminal UI with automatic refresh

**Command-line Options:**
- `--url`: Base URL of Flask server (default: http://localhost:5000)
- `--token`: Admin authentication token (default: test)
- `--interval`: Refresh interval in seconds (default: 5)

## Quick Start

### 1. Run the Demo Script
```bash
cd /home/chameau/service_web/Connectivity-Layer
python examples/metrics_api_demo.py
```

### 2. Start Real-time Monitoring
```bash
python examples/monitor_metrics.py
```

Press `Ctrl+C` to exit the monitor.

## API Endpoint

All examples use the metrics endpoint:

```
GET /metrics
Authorization: admin <token>
```

## Metrics Categories

### Redis Metrics
- Connection status
- Memory usage
- Key count
- Cache hit/miss rates
- Command statistics

### IoTDB Metrics
- Connection status
- Query success rate
- Write success rate

### MQTT Metrics
- Active connections
- Topics and subscriptions
- Message counts (sent/received)
- Bytes transferred

### System Metrics
- CPU usage and load average
- Memory usage
- Disk usage and I/O
- Network statistics

### IoTFlow Application Metrics
- Device counts (total, active, online)
- User counts
- Telemetry message counts
- HTTP request statistics

## Integration Examples

### Using with curl
```bash
# Get all metrics
curl -H "Authorization: admin test" http://localhost:5000/metrics

# Get only Redis metrics
curl -s -H "Authorization: admin test" http://localhost:5000/metrics | grep "^redis_"
```

### Using with Python requests
```python
import requests

response = requests.get(
    "http://localhost:5000/metrics",
    headers={"Authorization": "admin test"}
)

print(response.text)
```

### Using with JavaScript/Node.js
```javascript
const fetch = require('node-fetch');

async function getMetrics() {
    const response = await fetch('http://localhost:5000/metrics', {
        headers: { 'Authorization': 'admin test' }
    });
    const metrics = await response.text();
    console.log(metrics);
}
```

## Documentation

For detailed documentation, see:
- [Metrics API Usage Guide](../docs/METRICS_API_USAGE.md)
- [API Endpoints Summary](../docs/api/API_ENDPOINTS_SUMMARY.md)

## Requirements

All examples require:
- Python 3.7+
- `requests` library

Install dependencies:
```bash
pip install requests
```

## Troubleshooting

### Connection Refused
Make sure the Flask server is running:
```bash
curl http://localhost:5000/
```

### Authentication Error
Verify your admin token:
```bash
curl -H "Authorization: admin YOUR_TOKEN" http://localhost:5000/metrics
```

### Missing Metrics
Some metrics may be 0 or unavailable if services aren't running:
- Redis metrics require Redis to be running
- IoTDB metrics require IoTDB connection
- MQTT metrics require MQTT broker configuration
