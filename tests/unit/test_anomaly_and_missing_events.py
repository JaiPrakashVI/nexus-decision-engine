"""
Unit tests for Statistical and ML anomaly detection and missing-event (Dark Process) detection.
"""

import pytest
import asyncio
from anomaly_detection.diagnostics.statistical import StreamingStatisticalDetector
from anomaly_detection.diagnostics.ml_detector import MultivariateMLDetector
from anomaly_detection.missing_events.detector import DarkProcessDetector
from digital_twin.state.state_machine import ProcessPhase


def test_statistical_detector_detects_spikes():
    detector = StreamingStatisticalDetector(window_size=30, z_threshold=3.0)
    # Feed 20 baseline nominal readings
    for _ in range(20):
        detector.check_reading("dev_01", "pressure", 60.0)

    # Inject sharp spike
    is_anom, atype, score, severity = detector.check_reading("dev_01", "pressure", 140.0)
    assert is_anom is True
    assert "SPIKE" in atype
    assert score > 3.0


def test_statistical_detector_detects_sensor_freeze():
    detector = StreamingStatisticalDetector()
    # Feed 15 identical floats
    for i in range(14):
        detector.check_reading("dev_02", "temperature", 22.45)

    is_anom, atype, score, severity = detector.check_reading("dev_02", "temperature", 22.45)
    assert is_anom is True
    assert atype == "SENSOR_FLATLINE"


def test_multivariate_ml_detector_detects_cavitation():
    detector = MultivariateMLDetector()
    # High power (50 kW) with zero flow (0 GPM) is a severe anomaly
    is_anom, score, severity = detector.evaluate_vector(
        pressure=10.0, flow=0.0, temp=22.0, vibration=5.5, power=50.0
    )
    assert is_anom is True
    assert score > 0.5


@pytest.mark.asyncio
async def test_dark_process_detects_missing_transition():
    dp_detector = DarkProcessDetector()
    # Operational -> Emergency Shutdown directly (skipping Alert phase)
    evt = await dp_detector.check_transition("pump_01", ProcessPhase.EMERGENCY_SHUTDOWN)
    assert evt is not None
    assert "ALERT" in evt.expected_transition
    assert "OPERATIONAL -> EMERGENCY_SHUTDOWN" in evt.observed_transition
