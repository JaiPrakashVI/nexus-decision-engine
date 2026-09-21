"""
NEXUS Observability & Prometheus Metrics
Tracks ingestion rates, validation rejections, processing latency, and mTLS security results.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

TELEMETRY_RECEIVED = Counter(
    "nexus_telemetry_received_total",
    "Total number of telemetry packets received at the gateway",
    ["status", "device_type"]
)

TELEMETRY_LATENCY = Histogram(
    "nexus_telemetry_latency_seconds",
    "End-to-end ingestion and validation latency in seconds",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

TELEMETRY_REJECTIONS = Counter(
    "nexus_telemetry_rejections_total",
    "Total number of rejected telemetry payloads",
    ["reason"]
)

MTLS_VERIFICATIONS = Counter(
    "nexus_mtls_verifications_total",
    "Total client certificate validations performed",
    ["result"]
)

ACTIVE_CONNECTED_DEVICES = Gauge(
    "nexus_active_devices_total",
    "Number of active reporting cyber-physical devices in current window"
)

STREAM_PUBLISH_LATENCY = Histogram(
    "nexus_stream_publish_latency_seconds",
    "Time taken to append accepted telemetry to Redis Stream",
    buckets=[0.0005, 0.001, 0.002, 0.005, 0.01, 0.025, 0.05]
)
