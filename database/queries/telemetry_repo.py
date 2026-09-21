"""
NEXUS Database Repository & Query Layer
Encapsulates CRUD operations for telemetry, digital-twin state, anomalies, and experiments.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db_session
from database.schemas.models import (
    Device,
    TelemetryReading,
    StateSnapshot,
    AnomalyRecord,
    MissingEventRecord,
    Incident,
    InterventionRecord,
    ExperimentRecord,
)
from gateway.schemas.telemetry import TelemetryPayload


class TelemetryRepository:

    @staticmethod
    async def save_telemetry(payload: TelemetryPayload, reconstructed: bool = False, confidence: float = 1.0) -> int:
        async with get_db_session() as session:
            # Upsert device record if missing
            device = await session.get(Device, payload.device_id)
            if not device:
                device = Device(
                    id=payload.device_id,
                    device_type="sensor",
                    status="ACTIVE",
                    latitude=payload.latitude,
                    longitude=payload.longitude,
                )
                session.add(device)
                await session.flush()

            reading = TelemetryReading(
                device_id=payload.device_id,
                timestamp=payload.timestamp,
                sequence_number=payload.sequence_number,
                trace_id=payload.trace_id,
                pressure_psi=payload.pressure_psi,
                flow_rate_gpm=payload.flow_rate_gpm,
                temperature_c=payload.temperature_c,
                vibration_rms=payload.vibration_rms,
                power_kw=payload.power_kw,
                battery_pct=payload.battery_pct,
                reconstructed=reconstructed,
                confidence=confidence,
            )
            session.add(reading)
            await session.flush()
            return reading.id

    @staticmethod
    async def get_latest_telemetry(device_id: str) -> Optional[TelemetryReading]:
        async with get_db_session() as session:
            stmt = (
                select(TelemetryReading)
                .where(TelemetryReading.device_id == device_id)
                .order_by(desc(TelemetryReading.timestamp))
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_history(device_id: str, limit: int = 50) -> List[TelemetryReading]:
        async with get_db_session() as session:
            stmt = (
                select(TelemetryReading)
                .where(TelemetryReading.device_id == device_id)
                .order_by(desc(TelemetryReading.timestamp))
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def record_anomaly(
        device_id: str,
        anomaly_type: str,
        severity: str,
        score: float,
        detector: str,
        metrics: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        async with get_db_session() as session:
            record = AnomalyRecord(
                timestamp=timestamp or datetime.now(timezone.utc),
                device_id=device_id,
                anomaly_type=anomaly_type,
                severity=severity,
                score=score,
                detector=detector,
                metrics_snapshot=metrics,
            )
            session.add(record)

    @staticmethod
    async def record_missing_event(
        device_id: str,
        expected: str,
        observed: str,
        unexplained_latency_ms: float = 0.0,
        confidence: float = 0.5,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        async with get_db_session() as session:
            record = MissingEventRecord(
                timestamp=timestamp or datetime.now(timezone.utc),
                device_id=device_id,
                expected_transition=expected,
                observed_transition=observed,
                unexplained_latency_ms=unexplained_latency_ms,
                confidence=confidence,
                details=details,
            )
            session.add(record)

    @staticmethod
    async def save_state_snapshot(
        node_id: str,
        state: str,
        source: str,
        confidence: float,
        divergence_score: float = 0.0,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        async with get_db_session() as session:
            snapshot = StateSnapshot(
                timestamp=timestamp or datetime.now(timezone.utc),
                node_id=node_id,
                operational_state=state,
                state_source=source,
                confidence=confidence,
                divergence_score=divergence_score,
                state_details=details,
            )
            session.add(snapshot)

    @staticmethod
    async def save_experiment(
        exp_id: str,
        name: str,
        seed: int,
        loss_rate: float,
        delay_ms: int,
        noise_level: str,
        config: Dict[str, Any],
        metrics: Dict[str, Any]
    ):
        async with get_db_session() as session:
            rec = ExperimentRecord(
                id=exp_id,
                name=name,
                timestamp=datetime.now(timezone.utc),
                random_seed=seed,
                loss_rate=loss_rate,
                delay_ms=delay_ms,
                noise_level=noise_level,
                config=config,
                metrics=metrics,
            )
            session.add(rec)


telemetry_repo = TelemetryRepository()
