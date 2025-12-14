"""
Prometheus metrics definitions for IoTFlow Connectivity Layer.
All metrics are defined here and used by collectors and middleware.
"""
from prometheus_client import Counter, Histogram, Gauge, Info

# =============================================================================
# 1. SYSTEM METRICS
# =============================================================================

# CPU Metrics
SYSTEM_CPU_USAGE = Gauge("system_cpu_usage_percent", "CPU usage percentage")

SYSTEM_CPU_CORES = Gauge("system_cpu_cores_total", "Total number of CPU cores")

SYSTEM_LOAD_AVERAGE = Gauge("system_load_average", "System load average", ["period"])  # 1min, 5min, 15min

# Memory Metrics
SYSTEM_MEMORY_USAGE = Gauge("system_memory_usage_percent", "Memory usage percentage")

SYSTEM_MEMORY_TOTAL = Gauge("system_memory_total_bytes", "Total system memory in bytes")

SYSTEM_MEMORY_USED = Gauge("system_memory_used_bytes", "Used system memory in bytes")

# Disk Metrics
SYSTEM_DISK_USAGE = Gauge("system_disk_usage_percent", "Disk usage percentage", ["path"])  # mount point

SYSTEM_DISK_TOTAL = Gauge("system_disk_total_bytes", "Total disk space in bytes", ["path"])

SYSTEM_DISK_USED = Gauge("system_disk_used_bytes", "Used disk space in bytes", ["path"])

# Disk I/O Metrics
SYSTEM_DISK_IO_READ_BYTES = Counter("system_disk_io_read_bytes_total", "Total disk I/O bytes read", ["device"])

SYSTEM_DISK_IO_WRITE_BYTES = Counter("system_disk_io_write_bytes_total", "Total disk I/O bytes written", ["device"])

SYSTEM_DISK_IO_READ_RATE = Gauge(
    "system_disk_io_read_rate_bytes_per_second", "Current disk read rate in bytes per second", ["device"]
)

SYSTEM_DISK_IO_WRITE_RATE = Gauge(
    "system_disk_io_write_rate_bytes_per_second", "Current disk write rate in bytes per second", ["device"]
)

# Network Metrics
SYSTEM_NETWORK_BYTES_SENT = Counter("system_network_bytes_sent_total", "Total network bytes sent")

SYSTEM_NETWORK_BYTES_RECEIVED = Counter("system_network_bytes_received_total", "Total network bytes received")

SYSTEM_NETWORK_PACKETS_SENT = Counter("system_network_packets_sent_total", "Total network packets sent")

SYSTEM_NETWORK_PACKETS_RECEIVED = Counter("system_network_packets_received_total", "Total network packets received")

# =============================================================================
# 2. DATABASE METRICS (PostgreSQL)
# =============================================================================

DATABASE_CONNECTIONS_TOTAL = Gauge("database_connections_total", "Total database connections")

DATABASE_CONNECTIONS_ACTIVE = Gauge("database_connections_active", "Active database connections")

DATABASE_CONNECTIONS_IDLE = Gauge("database_connections_idle", "Idle database connections")

DATABASE_TABLE_ROWS = Gauge("database_table_rows", "Number of rows in database table", ["table"])

DATABASE_QUERY_DURATION = Histogram(
    "database_query_duration_seconds", "Database query execution duration in seconds", ["query_type"]
)

# =============================================================================
# 3. MQTT METRICS
# =============================================================================

MQTT_CONNECTIONS_TOTAL = Gauge("mqtt_connections_total", "Total MQTT connections")

MQTT_CONNECTIONS_ACTIVE = Gauge("mqtt_connections_active", "Active MQTT connections")

MQTT_MESSAGES_RECEIVED = Counter("mqtt_messages_received_total", "Total MQTT messages received")

MQTT_MESSAGES_SENT = Counter("mqtt_messages_sent_total", "Total MQTT messages sent")

MQTT_MESSAGES_DROPPED = Counter("mqtt_messages_dropped_total", "Total MQTT messages dropped")

MQTT_MESSAGES_QUEUED = Gauge("mqtt_messages_queued", "MQTT messages currently queued")

MQTT_TOPICS_TOTAL = Gauge("mqtt_topics_total", "Total number of MQTT topics")

MQTT_SUBSCRIPTIONS_TOTAL = Gauge("mqtt_subscriptions_total", "Total number of MQTT subscriptions")

MQTT_BYTES_SENT = Counter("mqtt_bytes_sent_total", "Total bytes sent via MQTT")

MQTT_BYTES_RECEIVED = Counter("mqtt_bytes_received_total", "Total bytes received via MQTT")

# =============================================================================
# 4. REDIS METRICS
# =============================================================================

REDIS_STATUS = Gauge("redis_status", "Redis server status (1=up, 0=down)")

REDIS_MEMORY_USED = Gauge("redis_memory_used_bytes", "Redis memory usage in bytes")

REDIS_MEMORY_PEAK = Gauge("redis_memory_peak_bytes", "Redis peak memory usage in bytes")

REDIS_MEMORY_FRAGMENTATION = Gauge("redis_memory_fragmentation_ratio", "Redis memory fragmentation ratio")

REDIS_KEYS_TOTAL = Gauge("redis_keys_total", "Total number of Redis keys")

REDIS_KEYS_EVICTED = Counter("redis_keys_evicted_total", "Total number of evicted Redis keys")

REDIS_COMMANDS_PROCESSED = Counter("redis_commands_processed_total", "Total Redis commands processed")

REDIS_CACHE_HITS = Counter("redis_cache_hits_total", "Total Redis cache hits")

REDIS_CACHE_MISSES = Counter("redis_cache_misses_total", "Total Redis cache misses")

# =============================================================================
# 5. APPLICATION METRICS
# =============================================================================

APP_INFO = Info("app_info", "Application information")

APP_UPTIME_SECONDS = Gauge("app_uptime_seconds", "Application uptime in seconds")

APP_START_TIME = Gauge("app_start_time_seconds", "Application start time as Unix timestamp")

# IoTFlow Specific Metrics
IOTFLOW_DEVICES_TOTAL = Gauge("iotflow_devices_total", "Total number of registered devices")

IOTFLOW_DEVICES_ACTIVE = Gauge("iotflow_devices_active", "Number of active devices")

IOTFLOW_DEVICES_ONLINE = Gauge("iotflow_devices_online", "Number of online devices")

IOTFLOW_USERS_TOTAL = Gauge("iotflow_users_total", "Total number of registered users")

IOTFLOW_TELEMETRY_MESSAGES = Counter("iotflow_telemetry_messages_total", "Total telemetry messages received")

IOTFLOW_CONTROL_COMMANDS = Counter(
    "iotflow_control_commands_total", "Total control commands sent", ["status"]  # pending, completed, failed
)

# =============================================================================
# 7. IOTDB METRICS
# =============================================================================

IOTDB_CONNECTION_STATUS = Gauge("iotdb_connection_status", "IoTDB connection status (1=connected, 0=disconnected)")

IOTDB_QUERY_SUCCESS_RATE = Gauge("iotdb_query_success_rate", "IoTDB query success rate percentage")

IOTDB_WRITE_SUCCESS_RATE = Gauge("iotdb_write_success_rate", "IoTDB write success rate percentage")

# =============================================================================
# 6. HTTP REQUEST METRICS
# =============================================================================

HTTP_REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])

HTTP_REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds", "HTTP request latency in seconds", ["method", "endpoint"]
)

HTTP_REQUESTS_IN_PROGRESS = Gauge("http_requests_in_progress", "Number of HTTP requests currently being processed")

HTTP_REQUEST_SIZE_BYTES = Histogram("http_request_size_bytes", "HTTP request size in bytes", ["method", "endpoint"])

HTTP_RESPONSE_SIZE_BYTES = Histogram("http_response_size_bytes", "HTTP response size in bytes", ["method", "endpoint"])

# Legacy metrics for backward compatibility
HTTP_REQUEST_COUNT_ALL = Counter("http_requests_all_total", "Total HTTP requests across all endpoints")

TELEMETRY_MESSAGES = Counter("telemetry_messages_total", "Total telemetry messages stored")
