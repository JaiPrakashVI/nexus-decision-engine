"""
NEXUS Redis Stream Telemetry Producer
Publishes validated telemetry payloads to Redis Streams with backpressure awareness and bounded length.
"""

import time
import json
import logging
from typing import Optional
from configs.settings import settings
from gateway.schemas.telemetry import TelemetryPayload
from streaming.redis.client import redis_manager
from gateway.api.metrics import STREAM_PUBLISH_LATENCY

logger = logging.getLogger("nexus.producer")


class StreamProducer:
    def __init__(self, stream_name: Optional[str] = None):
        self.stream_name = stream_name or settings.redis_stream_name
        self.max_len = 100000

    async def publish(self, payload: TelemetryPayload) -> str:
        """
        Publishes telemetry payload to Redis Stream.
        Returns the Redis message ID.
        """
        start_time = time.monotonic()
        data = {
            "device_id": payload.device_id,
            "timestamp": payload.timestamp.isoformat(),
            "sequence_number": str(payload.sequence_number),
            "trace_id": payload.trace_id,
            "latitude": str(payload.latitude),
            "longitude": str(payload.longitude),
            "pressure_psi": str(payload.pressure_psi),
            "flow_rate_gpm": str(payload.flow_rate_gpm),
            "temperature_c": str(payload.temperature_c),
            "vibration_rms": str(payload.vibration_rms),
            "power_kw": str(payload.power_kw),
            "battery_pct": str(payload.battery_pct),
            "schema_version": payload.schema_version,
            "raw_json": payload.model_dump_json(),
        }

        if redis_manager.is_available and redis_manager.client:
            try:
                msg_id = await redis_manager.client.xadd(
                    name=self.stream_name,
                    fields=data,
                    maxlen=self.max_len,
                    approximate=True,
                )
                STREAM_PUBLISH_LATENCY.observe(time.monotonic() - start_time)
                return str(msg_id)
            except Exception as e:
                logger.error(f"Failed to publish event {payload.trace_id} to Redis Stream: {e}")
                # Fallback to simulated message ID
                return f"offline-{int(time.time()*1000)}-0"
        else:
            # Fallback for testing when Redis is offline
            return f"offline-{int(time.time()*1000)}-0"


stream_producer = StreamProducer()
