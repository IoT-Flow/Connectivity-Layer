from prometheus_client import Counter, Histogram

# HTTP request metrics
HTTP_REQUEST_COUNT = Counter(
    'http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'http_status']
)
HTTP_REQUEST_LATENCY = Histogram(
    'http_request_latency_seconds', 'HTTP request latency in seconds', ['method', 'endpoint']
)

# Total HTTP requests across all endpoints
HTTP_REQUEST_COUNT_ALL = Counter(
    'http_requests_all_total', 'Total HTTP requests across all endpoints'
)

# Telemetry messages counter
TELEMETRY_MESSAGES = Counter(
    'telemetry_messages_total', 'Total telemetry messages stored'
)
