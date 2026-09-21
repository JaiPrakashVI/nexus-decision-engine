"""
NEXUS Telemetry Schemas
Strict Pydantic models for data ingestion, validation, and serialization.
"""

from datetime import datetime, timezone
from typing import Literal
import uuid
from pydantic import BaseModel, Field, field_validator


class TelemetryPayload(BaseModel):
    device_id: str = Field(
        ...,
        min_length=3,
        max_length=64,
        description="Unique identifier of the sending cyber-physical device"
    )
    timestamp: datetime = Field(
        ...,
        description="ISO 8601 UTC timestamp of measurement capture"
    )
    sequence_number: int = Field(
        ...,
        ge=0,
        description="Monotonically increasing sequence number per device"
    )
    trace_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Distributed tracing identifier passed along the closed-loop pipeline"
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="WGS84 latitude coordinate"
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="WGS84 longitude coordinate"
    )
    pressure_psi: float = Field(
        ...,
        ge=0.0,
        le=500.0,
        description="Hydraulic pressure measurement in PSI"
    )
    flow_rate_gpm: float = Field(
        ...,
        ge=0.0,
        le=5000.0,
        description="Volumetric flow rate in gallons per minute"
    )
    temperature_c: float = Field(
        ...,
        ge=-40.0,
        le=150.0,
        description="Operating temperature in degrees Celsius"
    )
    vibration_rms: float = Field(
        default=0.0,
        ge=0.0,
        le=50.0,
        description="Vibration root-mean-square in mm/s for mechanical wear detection"
    )
    power_kw: float = Field(
        default=0.0,
        ge=0.0,
        le=1000.0,
        description="Electrical power consumption in kW"
    )
    battery_pct: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Sensor node battery level percentage"
    )
    schema_version: str = Field(
        default="1.0",
        description="Semantic version of telemetry contract"
    )

    @field_validator("schema_version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        if v not in {"1.0", "1.1"}:
            raise ValueError(f"Unsupported schema version: {v}. Supported: ['1.0', '1.1']")
        return v

    @field_validator("timestamp")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v


class IngestionStatus(BaseModel):
    status: Literal["ACCEPTED", "REJECTED", "DUPLICATE", "DEGRADED"]
    device_id: str
    trace_id: str
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: str = "Telemetry processed successfully"
    reconstructed: bool = False
    confidence: float = 1.0


class BatchTelemetryPayload(BaseModel):
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: list[TelemetryPayload]
