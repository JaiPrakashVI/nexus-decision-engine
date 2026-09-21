"""
Unit tests for Digital Twin state reconstruction, confidence decay, and physical value estimation.
"""

from datetime import datetime, timezone, timedelta
import pytest

from digital_twin.graph.topology import (
    topology,
    OperationalState,
    StateSource,
)
from digital_twin.reconstruction.estimator import StateReconstructor


def test_fresh_telemetry_is_observed():
    reconstructor = StateReconstructor(obs_window_sec=5.0)
    now = datetime.now(timezone.utc)
    node = topology.get_node("pump_01")
    assert node is not None
    node.last_updated = now

    state, source, conf, vals = reconstructor.evaluate_node_state("pump_01", now)
    assert source == StateSource.OBSERVED
    assert conf == 1.0
    assert "pressure_psi" in vals


def test_missing_telemetry_triggers_inferred_with_decay():
    reconstructor = StateReconstructor(obs_window_sec=2.0, max_infer_window_sec=30.0, decay_rate_lambda=0.05)
    now = datetime.now(timezone.utc)
    node = topology.get_node("pump_01")
    assert node is not None

    # Telemetry is 10 seconds stale (exceeds 2s obs window, within 30s infer window)
    node.last_updated = now - timedelta(seconds=10.0)

    state, source, conf, vals = reconstructor.evaluate_node_state("pump_01", now)
    assert source == StateSource.INFERRED
    # Confidence should decay below 1.0 but stay above 0.2
    assert 0.2 <= conf < 1.0
    assert vals["pressure_psi"] > 0.0


def test_prolonged_gap_triggers_unknown():
    reconstructor = StateReconstructor(obs_window_sec=2.0, max_infer_window_sec=20.0)
    now = datetime.now(timezone.utc)
    node = topology.get_node("pump_01")
    assert node is not None

    # Telemetry is 2 minutes stale
    node.last_updated = now - timedelta(seconds=120.0)

    state, source, conf, vals = reconstructor.evaluate_node_state("pump_01", now)
    assert source == StateSource.UNKNOWN
    assert conf <= 0.2


def test_global_reconstruction_completeness_calculation():
    reconstructor = StateReconstructor()
    summary = reconstructor.update_all_nodes()
    assert "completeness_score" in summary
    assert "observability_score" in summary
    assert 0.0 <= summary["completeness_score"] <= 1.0
    assert 0.0 <= summary["observability_score"] <= 1.0
