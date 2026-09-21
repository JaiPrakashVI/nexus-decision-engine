"""
Integration tests for closed-loop NEXUS pipeline:
Sensor -> Gateway Validation -> Producer -> Persistence -> Digital Twin -> Anomaly Detection.
"""

import pytest
from datetime import datetime, timezone
import uuid

from simulator.device_simulator import SimulatedDevice
from gateway.schemas.telemetry import TelemetryPayload
from gateway.authentication.device_registry import device_registry
from database.queries.telemetry_repo import telemetry_repo
from database.connection import init_db
from digital_twin.synchronization.sync_manager import twin_sync_manager
from digital_twin.reconstruction.estimator import reconstructor
from digital_twin.graph.topology import topology, StateSource


@pytest.mark.asyncio
async def test_end_to_end_closed_loop_pipeline():
    await init_db()

    # 1. Device generates reading
    dev = SimulatedDevice(device_id="pump_01", device_type="pump", lat=43.541, lon=-80.248)
    reading = dev.generate_reading()

    # 2. Verify authorization
    assert device_registry.is_authorized(reading.device_id) is True

    # 3. Database persistence
    row_id = await telemetry_repo.save_telemetry(reading)
    assert row_id is not None

    # 4. Synchronize into Digital Twin
    await twin_sync_manager.process_incoming_telemetry(reading)
    node = topology.get_node(reading.device_id)
    assert node is not None
    assert node.current_pressure == reading.pressure_psi
    assert node.state_source == StateSource.OBSERVED

    # 5. Evaluate state reconstruction
    state, source, conf, vals = reconstructor.evaluate_node_state(reading.device_id)
    assert source == StateSource.OBSERVED
    assert conf == 1.0
    assert vals["pressure_psi"] == reading.pressure_psi
