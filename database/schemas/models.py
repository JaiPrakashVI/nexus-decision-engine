"""
NEXUS Relational & Time-Series Database Models
Defines tables for devices, hypertable telemetry, state snapshots, anomalies, incidents, interventions, and experiments.
"""

from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    BigInteger,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(64), primary_key=True, index=True)
    device_type = Column(String(32), nullable=False)
    status = Column(String(16), default="ACTIVE", nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    registered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    meta_info = Column(JSON, nullable=True)

    telemetry = relationship("TelemetryReading", back_populates="device", cascade="all, delete-orphan")


class TelemetryReading(Base):
    """
    Core time-series table. In PostgreSQL + TimescaleDB, this is converted into a hypertable partitioned by time.
    """
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(64), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    sequence_number = Column(BigInteger, nullable=False)
    trace_id = Column(String(64), nullable=False, index=True)
    pressure_psi = Column(Float, nullable=False)
    flow_rate_gpm = Column(Float, nullable=False)
    temperature_c = Column(Float, nullable=False)
    vibration_rms = Column(Float, default=0.0)
    power_kw = Column(Float, default=0.0)
    battery_pct = Column(Float, default=100.0)
    reconstructed = Column(Boolean, default=False)
    confidence = Column(Float, default=1.0)

    device = relationship("Device", back_populates="telemetry")

    __table_args__ = (
        Index("idx_device_time", "device_id", "timestamp"),
    )


class StateSnapshot(Base):
    """
    Tracks digital twin state evaluations, differentiating observed, inferred, and unknown states.
    """
    __tablename__ = "state_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    node_id = Column(String(64), nullable=False, index=True)
    operational_state = Column(String(32), nullable=False)  # OPERATIONAL, DEGRADED, FAILED, OFFLINE
    state_source = Column(String(16), nullable=False)       # OBSERVED, INFERRED, UNKNOWN
    confidence = Column(Float, nullable=False, default=1.0)
    divergence_score = Column(Float, default=0.0)
    state_details = Column(JSON, nullable=True)


class AnomalyRecord(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    device_id = Column(String(64), nullable=False, index=True)
    anomaly_type = Column(String(64), nullable=False)  # SPIKE, DRIFT, FLATLINE, MULTIVARIATE
    severity = Column(String(16), nullable=False)       # LOW, MEDIUM, HIGH, CRITICAL
    score = Column(Float, nullable=False)
    detector = Column(String(32), nullable=False)       # Z_SCORE, EWMA, ISOLATION_FOREST
    metrics_snapshot = Column(JSON, nullable=True)


class MissingEventRecord(Base):
    """
    Records detected process gaps and unobserved state transitions (Dark Processes).
    """
    __tablename__ = "missing_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    device_id = Column(String(64), nullable=False, index=True)
    expected_transition = Column(String(128), nullable=False)
    observed_transition = Column(String(128), nullable=False)
    unexplained_latency_ms = Column(Float, default=0.0)
    confidence = Column(Float, default=0.5)
    details = Column(JSON, nullable=True)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    root_cause_node = Column(String(64), nullable=False)
    severity = Column(String(16), nullable=False)
    status = Column(String(16), default="OPEN")  # OPEN, MITIGATING, RESOLVED
    affected_nodes = Column(JSON, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class InterventionRecord(Base):
    __tablename__ = "interventions"

    id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), ForeignKey("incidents.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    proposed_by = Column(String(32), nullable=False)  # DETERMINISTIC, AGENT_PLANNER
    action_name = Column(String(64), nullable=False)
    target_nodes = Column(JSON, nullable=False)
    parameters = Column(JSON, nullable=True)
    simulated_recovery_time_sec = Column(Float, nullable=False)
    actual_recovery_time_sec = Column(Float, nullable=True)
    constraints_passed = Column(Boolean, default=True)


class ExperimentRecord(Base):
    """
    Stores reproducible research experiment metadata, configurations, and evaluation metrics.
    """
    __tablename__ = "experiments"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    random_seed = Column(Integer, nullable=False)
    loss_rate = Column(Float, nullable=False)
    delay_ms = Column(Integer, nullable=False)
    noise_level = Column(String(16), nullable=False)
    config = Column(JSON, nullable=False)
    metrics = Column(JSON, nullable=False)
