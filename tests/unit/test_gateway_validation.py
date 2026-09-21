"""
Unit tests for Secure Gateway validation, replay detection, and rate limiting.
"""

import pytest
from datetime import datetime, timezone, timedelta
import uuid
from pydantic import ValidationError

from gateway.schemas.telemetry import TelemetryPayload
from gateway.api.replay_detector import ReplayDetector
from gateway.api.rate_limiter import TokenBucketRateLimiter
from gateway.authentication.device_registry import DeviceRegistry, DeviceStatus


def test_valid_telemetry_payload():
    payload = TelemetryPayload(
        device_id="sensor_001",
        timestamp=datetime.now(timezone.utc),
        sequence_number=1,
        trace_id=str(uuid.uuid4()),
        latitude=43.54,
        longitude=-80.25,
        pressure_psi=65.2,
        flow_rate_gpm=52.4,
        temperature_c=21.0,
        battery_pct=95.0,
        schema_version="1.0"
    )
    assert payload.device_id == "sensor_001"
    assert payload.pressure_psi == 65.2


def test_invalid_coordinates_rejected():
    with pytest.raises(ValidationError):
        TelemetryPayload(
            device_id="sensor_001",
            timestamp=datetime.now(timezone.utc),
            sequence_number=1,
            trace_id=str(uuid.uuid4()),
            latitude=120.0,  # Invalid: > 90
            longitude=-80.25,
            pressure_psi=65.2,
            flow_rate_gpm=52.4,
            temperature_c=21.0,
        )


def test_replay_detector_rejects_duplicate_trace_id():
    detector = ReplayDetector()
    t_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    valid, reason = detector.check_and_record("dev_01", 1, t_id, now)
    assert valid is True

    # Replay same trace_id
    valid2, reason2 = detector.check_and_record("dev_01", 2, t_id, now)
    assert valid2 is False
    assert "Duplicate event" in reason2


def test_replay_detector_rejects_timestamp_drift():
    detector = ReplayDetector(max_drift_past_sec=60, max_drift_future_sec=30)
    now = datetime.now(timezone.utc)

    # 5 minutes in past
    old_time = now - timedelta(seconds=300)
    valid, reason = detector.check_and_record("dev_01", 1, str(uuid.uuid4()), old_time)
    assert valid is False
    assert "too old" in reason

    # 5 minutes in future
    future_time = now + timedelta(seconds=300)
    valid_f, reason_f = detector.check_and_record("dev_01", 2, str(uuid.uuid4()), future_time)
    assert valid_f is False
    assert "future" in reason_f


def test_rate_limiter_throttling():
    limiter = TokenBucketRateLimiter(rate_per_sec=2.0, burst=3.0)
    # Burst 3 requests allowed
    assert limiter.is_allowed("client_A") is True
    assert limiter.is_allowed("client_A") is True
    assert limiter.is_allowed("client_A") is True
    # 4th request without delay should be rejected
    assert limiter.is_allowed("client_A") is False


def test_device_registry_authorization():
    registry = DeviceRegistry()
    registry.register_device("pump_99", "pump", status=DeviceStatus.ACTIVE)
    assert registry.is_authorized("pump_99") is True

    registry.revoke_device("pump_99")
    assert registry.is_authorized("pump_99") is False
    assert registry.is_authorized("non_existent_device") is False
