"""
NEXUS Secure Telemetry Gateway Routes
Handles single and batch telemetry ingestion, device authentication, rate limiting, and observability.
"""

import time
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from gateway.schemas.telemetry import (
    TelemetryPayload,
    IngestionStatus,
    BatchTelemetryPayload,
)
from gateway.authentication.device_registry import device_registry, DeviceRecord, DeviceStatus
from gateway.api.rate_limiter import rate_limiter
from gateway.api.replay_detector import replay_detector
from streaming.redis.producer import stream_producer
from streaming.redis.client import redis_manager
from gateway.api.metrics import (
    TELEMETRY_RECEIVED,
    TELEMETRY_LATENCY,
    TELEMETRY_REJECTIONS,
    ACTIVE_CONNECTED_DEVICES,
)

router = APIRouter()


@router.post(
    "/api/v1/telemetry",
    response_model=IngestionStatus,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest single telemetry reading"
)
async def ingest_telemetry(payload: TelemetryPayload, request: Request):
    start_time = time.monotonic()
    device_id = payload.device_id

    # 1. Rate Limiting Check
    if not rate_limiter.is_allowed(device_id):
        TELEMETRY_REJECTIONS.labels(reason="rate_limit_exceeded").inc()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for device '{device_id}'"
        )

    # 2. Device Authorization Check
    device = device_registry.get_device(device_id)
    if not device or device.status != DeviceStatus.ACTIVE:
        TELEMETRY_REJECTIONS.labels(reason="unauthorized_device").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Device '{device_id}' is not registered or has been revoked"
        )

    # 3. Replay, Duplicate & Timestamp Sanity Check
    is_valid, reason = replay_detector.check_and_record(
        device_id=device_id,
        seq_no=payload.sequence_number,
        trace_id=payload.trace_id,
        timestamp=payload.timestamp
    )
    if not is_valid:
        TELEMETRY_REJECTIONS.labels(reason="replay_or_drift").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason
        )

    # 4. Out-of-order check
    status_code = "ACCEPTED"
    if replay_detector.is_out_of_order(device_id, payload.sequence_number):
        status_code = "DEGRADED"

    # 5. Publish to Redis Stream
    msg_id = await stream_producer.publish(payload)

    # 6. Record Metrics
    dev_type = device.device_type if device else "unknown"
    TELEMETRY_RECEIVED.labels(status=status_code, device_type=dev_type).inc()
    TELEMETRY_LATENCY.observe(time.monotonic() - start_time)

    return IngestionStatus(
        status=status_code,
        device_id=device_id,
        trace_id=payload.trace_id,
        message=f"Event ingested successfully [redis_id: {msg_id}]"
    )


@router.post(
    "/api/v1/telemetry/batch",
    response_model=list[IngestionStatus],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest batch of telemetry readings"
)
async def ingest_batch_telemetry(batch: BatchTelemetryPayload, request: Request):
    results = []
    for item in batch.items:
        try:
            status_resp = await ingest_telemetry(item, request)
            results.append(status_resp)
        except HTTPException as e:
            results.append(
                IngestionStatus(
                    status="REJECTED",
                    device_id=item.device_id,
                    trace_id=item.trace_id,
                    message=e.detail,
                    confidence=0.0
                )
            )
    return results


@router.get("/health", summary="Service health status")
async def health_check():
    return {
        "status": "healthy",
        "service": "nexus-gateway",
        "redis_connected": redis_manager.is_available,
        "environment": "active",
    }


@router.get("/metrics", response_class=PlainTextResponse, summary="Prometheus metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/api/v1/devices", summary="List registered devices")
async def list_devices():
    return {
        "count": len(device_registry._devices),
        "devices": [
            {
                "device_id": d.device_id,
                "status": d.status,
                "device_type": d.device_type,
            }
            for d in device_registry._devices.values()
        ]
    }
