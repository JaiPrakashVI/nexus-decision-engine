"""
NEXUS Stream Ingestion Consumer Service
Consumes from Redis Streams consumer group, persists to TimescaleDB, and feeds the Digital Twin.
Includes dead-letter queue (DLQ) routing, acknowledgement, and graceful shutdown.
"""

import asyncio
import signal
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from configs.settings import settings
from gateway.schemas.telemetry import TelemetryPayload
from streaming.redis.client import redis_manager
from database.queries.telemetry_repo import telemetry_repo
from database.connection import init_db

logger = logging.getLogger("nexus.consumer")


class TelemetryConsumer:
    def __init__(
        self,
        stream_name: Optional[str] = None,
        group_name: Optional[str] = None,
        consumer_name: str = "worker-01"
    ):
        self.stream_name = stream_name or settings.redis_stream_name
        self.group_name = group_name or settings.redis_consumer_group
        self.consumer_name = consumer_name
        self.dlq_stream = settings.redis_dlq_stream
        self.running = False

    async def setup_group(self):
        """Ensure stream and consumer group exist."""
        if not redis_manager.client:
            return
        try:
            await redis_manager.client.xgroup_create(
                name=self.stream_name,
                groupname=self.group_name,
                id="0",
                mkstream=True,
            )
            logger.info(f"Consumer group '{self.group_name}' created for stream '{self.stream_name}'.")
        except Exception as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group '{self.group_name}' already exists.")
            else:
                logger.warning(f"Consumer group initialization warning: {e}")

    async def process_message(self, msg_id: str, fields: dict):
        """Deserialize, persist, and dispatch to digital twin."""
        try:
            # Reconstruct TelemetryPayload
            raw_json = fields.get("raw_json")
            if raw_json:
                payload = TelemetryPayload.model_validate_json(raw_json)
            else:
                payload = TelemetryPayload(
                    device_id=fields["device_id"],
                    timestamp=datetime.fromisoformat(fields["timestamp"]),
                    sequence_number=int(fields["sequence_number"]),
                    trace_id=fields["trace_id"],
                    latitude=float(fields["latitude"]),
                    longitude=float(fields["longitude"]),
                    pressure_psi=float(fields["pressure_psi"]),
                    flow_rate_gpm=float(fields["flow_rate_gpm"]),
                    temperature_c=float(fields["temperature_c"]),
                    vibration_rms=float(fields.get("vibration_rms", 0.0)),
                    power_kw=float(fields.get("power_kw", 0.0)),
                    battery_pct=float(fields.get("battery_pct", 100.0)),
                    schema_version=fields.get("schema_version", "1.0"),
                )

            # Persist to database
            await telemetry_repo.save_telemetry(payload)

            # Dispatch to Digital Twin (imported dynamically to prevent circular dependencies)
            from digital_twin.synchronization.sync_manager import twin_sync_manager
            await twin_sync_manager.process_incoming_telemetry(payload)

            # Acknowledge message in Redis Stream
            if redis_manager.client:
                await redis_manager.client.xack(self.stream_name, self.group_name, msg_id)

        except Exception as e:
            logger.error(f"Failed to process message {msg_id}: {e}")
            # Route to Dead Letter Queue (DLQ)
            if redis_manager.client:
                try:
                    await redis_manager.client.xadd(
                        name=self.dlq_stream,
                        fields={**fields, "error": str(e), "original_msg_id": msg_id},
                        maxlen=10000,
                    )
                    await redis_manager.client.xack(self.stream_name, self.group_name, msg_id)
                    logger.warning(f"Routed failed message {msg_id} to DLQ.")
                except Exception as dlq_err:
                    logger.error(f"DLQ forwarding failed: {dlq_err}")

    async def start(self):
        self.running = True
        logger.info(f"Starting TelemetryConsumer ({self.consumer_name}) on stream '{self.stream_name}'...")
        await self.setup_group()

        while self.running:
            try:
                if not redis_manager.is_available or not redis_manager.client:
                    await asyncio.sleep(1.0)
                    continue

                # Read batch of messages from consumer group
                response = await redis_manager.client.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={self.stream_name: ">"},
                    count=50,
                    block=2000,
                )

                if response:
                    for stream, messages in response:
                        for msg_id, fields in messages:
                            await self.process_message(msg_id, fields)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error reading from Redis Stream: {e}")
                await asyncio.sleep(1.0)

    def stop(self):
        logger.info("Stopping TelemetryConsumer...")
        self.running = False


async def run_consumer_service():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    await redis_manager.initialize()

    consumer = TelemetryConsumer()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, consumer.stop)
        except NotImplementedError:
            pass  # Windows signal handler compatibility

    try:
        await consumer.start()
    finally:
        await redis_manager.close()


if __name__ == "__main__":
    asyncio.run(run_consumer_service())
