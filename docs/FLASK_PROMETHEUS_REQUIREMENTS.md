# Flask Backend - Prometheus Metrics Requirements

**Date:** December 10, 2025  
**Backend:** Flask (Connectivity Layer - Python)  
**Purpose:** Expose system metrics to Prometheus

---

## 🎯 Objective

Expose application and system metrics via `/metrics` endpoint in Prometheus format for scraping and monitoring.

---

## 📊 Architecture Flow

```
Flask App (Port 5000)
    ↓ exposes
/metrics endpoint (Prometheus format)
    ↓ scraped every 15s
Prometheus Server (Port 9090)
    ↓ stores time-series data
HTTP API
    ↓ queried by
Node.js Backend
    ↓ serves to
Frontend
```

---

## 📦 Required Packages

Add to `requirements.txt`:
```
prometheus-client>=0.19.0
psutil>=5.9.0
redis>=5.0.0
psycopg2-binary>=2.9.0
```

---

## 📋 Required Metrics Categories

### 1. System Metrics
- **CPU**: Usage percentage, core count, load average
- **Memory**: Total, used, free, usage percentage
- **Disk**: Total, used, free, usage percentage (per mount point)
- **Network**: Bytes sent/received, packets sent/received

### 2. Database Metrics (PostgreSQL)
- **Connections**: Total, active, idle
- **Tables**: Row counts per table (devices, users, device_auth, etc.)
- **Queries**: Total count, execution duration (histogram)

### 3. MQTT Metrics
- **Connections**: Total, active connections
- **Messages**: Received, sent, dropped, queued
- **Topics**: Total topics, subscriptions
- **Bandwidth**: Bytes sent/received via MQTT

### 4. Redis Metrics
- **Status**: Up/down (1/0)
- **Memory**: Used, peak, fragmentation ratio
- **Keys**: Total, evicted
- **Performance**: Commands processed, cache hits/misses

### 5. Application Metrics
- **App Info**: Version, Python version, uptime
- **HTTP Requests**: Total count by method/endpoint/status, duration (histogram), in-progress
- **IoTFlow Specific**: Total devices, active devices, telemetry messages received

---

## 🏗️ Implementation Requirements

### File Structure
```
Connectivity-Layer/
├── src/
│   ├── metrics.py                    # Define all Prometheus metrics
│   ├── routes/
│   │   └── prometheus_route.py       # /metrics endpoint
│   ├── services/
│   │   ├── metrics_collector.py      # Background collector coordinator
│   │   ├── system_metrics.py         # Collect system metrics
│   │   ├── database_metrics.py       # Collect DB metrics
│   │   ├── mqtt_metrics.py           # Collect MQTT metrics
│   │   ├── redis_metrics.py          # Collect Redis metrics
│   │   └── application_metrics.py    # Collect app metrics
│   └── middleware/
│       └── metrics_middleware.py     # Track HTTP request metrics
└── app.py                            # Register route & start collector
```

### Endpoint Specification
- **URL**: `GET /metrics`
- **Format**: Prometheus text format
- **Authentication**: None (IP whitelisting recommended)
- **Update Frequency**: Metrics updated every 15 seconds in background
- **Response Time**: < 100ms

### Metrics Format Requirements
Each metric must include:
- `# HELP` comment describing the metric
- `# TYPE` comment specifying gauge/counter/histogram/info
- Proper labels for multi-dimensional metrics (e.g., `table`, `path`, `method`, `endpoint`)

### Background Collection
- Run metrics collection in separate daemon thread
- Collect metrics every 15 seconds
- Handle errors gracefully without crashing app
- Use try-catch for each collector

### HTTP Request Tracking
- Automatically track all HTTP requests via middleware
- Record: method, endpoint, status code, duration
- Increment counters and update histograms
- Track concurrent requests in progress

---

## 🔒 Security Requirements

1. **IP Whitelisting**: Restrict `/metrics` to Prometheus server IP only
2. **Internal Network**: Keep endpoint on internal network, not public internet
3. **No Sensitive Data**: Never expose passwords, tokens, or PII in metrics
4. **Rate Limiting**: Limit scrape frequency to avoid performance impact
5. **Resource Limits**: Metrics collection should use < 5% CPU, < 50MB RAM

---

## 📈 Prometheus Configuration

Create `prometheus/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'flask_iotflow_connectivity'
    scrape_interval: 15s
    static_configs:
      - targets: ['flask-app:5000']
        labels:
          service: 'connectivity-layer'
          environment: 'production'
```

---

## 🧪 Testing Requirements

### Functional Tests
1. `/metrics` endpoint returns 200 status
2. Response is valid Prometheus format
3. All required metric types are present
4. Metrics values are reasonable (e.g., CPU 0-100%)
5. Background collector thread starts and runs
6. HTTP request metrics are tracked correctly

### Performance Tests
1. `/metrics` response time < 100ms
2. Metrics collection doesn't block HTTP requests
3. Memory usage stable over time (no leaks)
4. CPU usage from metrics < 5%

### Integration Tests
1. Prometheus can successfully scrape endpoint
2. Metrics appear in Prometheus UI
3. No scrape errors in Prometheus logs

---

## ✅ Acceptance Criteria

- [ ] `/metrics` endpoint accessible and returns Prometheus format
- [ ] All 5 metric categories implemented and collecting
- [ ] Background collection runs every 15 seconds
- [ ] HTTP request middleware tracks all requests
- [ ] Metrics include proper HELP and TYPE comments
- [ ] Prometheus successfully scrapes without errors
- [ ] Response time consistently < 100ms
- [ ] No performance degradation to Flask app
- [ ] Documentation complete
- [ ] Tests passing

---

## 📊 Example Metrics Output

```prometheus
# HELP system_cpu_usage_percent CPU usage percentage
# TYPE system_cpu_usage_percent gauge
system_cpu_usage_percent 45.2

# HELP flask_http_requests_total Total HTTP requests
# TYPE flask_http_requests_total counter
flask_http_requests_total{method="POST",endpoint="/api/v1/telemetry",status="200"} 150000

# HELP iotflow_devices_total Total registered devices
# TYPE iotflow_devices_total gauge
iotflow_devices_total 1500
```

---

## 🔄 Next Steps

1. Implement Flask metrics (this document)
2. Configure Prometheus to scrape Flask
3. Implement Node.js proxy API (next document)
4. Create frontend dashboards
