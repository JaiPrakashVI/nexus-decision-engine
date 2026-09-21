"""
Failure and Chaos Mode Tests for NEXUS.
Verifies graceful degradation under security violations, corrupted inputs, duplicate replays, and offline AI.
"""

from pathlib import Path
import pytest
from cryptography import x509
from datetime import datetime, timezone
import uuid

from gateway.authentication.cert_validator import CertificateValidator
from gateway.api.replay_detector import ReplayDetector
from gateway.schemas.telemetry import TelemetryPayload
from agents.llm.client import LocalLLMClient


def test_untrusted_rogue_cert_rejected():
    validator = CertificateValidator(ca_cert_path="certs/ca.crt")
    unauthorized_cert_path = Path("certs/unauthorized.crt")

    if unauthorized_cert_path.exists():
        with open(unauthorized_cert_path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())
        is_valid, reason, dev_id = validator.validate_client_cert(cert)
        # Should be rejected because it's signed by the rogue CA, not the trusted NEXUS Root CA
        assert is_valid is False
        assert "signature verification failed" in reason.lower()


def test_malformed_telemetry_rejected():
    # Negative pressure should fail schema validation
    with pytest.raises(Exception):
        TelemetryPayload(
            device_id="sensor_001",
            timestamp=datetime.now(timezone.utc),
            sequence_number=1,
            trace_id=str(uuid.uuid4()),
            latitude=43.54,
            longitude=-80.25,
            pressure_psi=-15.0,  # Impossible negative hydraulic pressure
            flow_rate_gpm=50.0,
            temperature_c=20.0,
        )


def test_duplicate_telemetry_rejected_by_replay_guard():
    detector = ReplayDetector()
    t_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # First packet passes
    ok1, _ = detector.check_and_record("dev_01", 1, t_id, now)
    assert ok1 is True

    # Duplicate packet with same trace_id fails
    ok2, reason = detector.check_and_record("dev_01", 1, t_id, now)
    assert ok2 is False
    assert "Duplicate" in reason


@pytest.mark.asyncio
async def test_offline_llm_graceful_fallback():
    # Force invalid URL to test network failure handling
    client = LocalLLMClient(base_url="http://invalid-host-that-does-not-exist:9999", timeout=1)
    res = await client.generate_structured(
        system_prompt="Test prompt",
        user_prompt="Evaluate incident",
        expected_schema_name="RecoveryPlanner"
    )
    # Must not throw exception; must return valid deterministic fallback
    assert res is not None
    assert res["source"] == "deterministic_fallback_agent"
    assert "data" in res
    assert res["data"]["recommended_action"] == "ACTIVATE_BACKUP_PUMP"
