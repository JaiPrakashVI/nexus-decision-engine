"""
NEXUS Digital Twin Synchronization Manager
Synchronizes incoming telemetry streams with in-memory topological digital twin state.
"""

from datetime import datetime, timezone
import logging
from typing import Optional, List, Callable
from gateway.schemas.telemetry import TelemetryPayload
from digital_twin.graph.topology import (
    topology,
    OperationalState,
    StateSource,
    TwinNodeData,
)

logger = logging.getLogger("nexus.twin.sync")


class TwinSyncManager:
    def __init__(self):
        self._listeners: List[Callable[[str, dict], None]] = []

    def register_listener(self, callback: Callable[[str, dict], None]):
        self._listeners.append(callback)

    async def process_incoming_telemetry(self, payload: TelemetryPayload):
        """
        Updates in-memory digital twin node with fresh telemetry reading.
        """
        node_id = payload.device_id
        node = topology.get_node(node_id)

        # If node isn't pre-defined in default topology, dynamically add as sensor/meter
        if not node:
            topology.add_node(
                node_id=node_id,
                node_type="sensor",
                name=f"Field Asset {node_id}",
                lat=payload.latitude,
                lon=payload.longitude,
            )
            node = topology.get_node(node_id)

        # Update physical metrics
        node.current_pressure = payload.pressure_psi
        node.current_flow = payload.flow_rate_gpm
        node.current_temp = payload.temperature_c
        node.current_vibration = payload.vibration_rms
        node.current_power = payload.power_kw
        node.battery_pct = payload.battery_pct
        node.last_updated = payload.timestamp
        node.state_source = StateSource.OBSERVED
        node.confidence = 1.0

        # Evaluate operational status
        if payload.pressure_psi < 15.0 or payload.battery_pct < 5.0:
            node.operational_state = OperationalState.FAILED
        elif payload.pressure_psi < 35.0 or payload.vibration_rms > 6.0:
            node.operational_state = OperationalState.CRITICAL
        elif payload.pressure_psi < 45.0 or payload.vibration_rms > 3.0:
            node.operational_state = OperationalState.DEGRADED
        else:
            node.operational_state = OperationalState.OPERATIONAL

        # Broadcast state update to registered listeners (e.g. WebSocket router)
        update_packet = {
            "node_id": node_id,
            "state": node.operational_state.value,
            "source": node.state_source.value,
            "pressure": round(node.current_pressure, 2),
            "flow": round(node.current_flow, 2),
            "temp": round(node.current_temp, 2),
            "vibration": round(node.current_vibration, 2),
            "confidence": 1.0,
            "timestamp": payload.timestamp.isoformat(),
        }

        for listener in self._listeners:
            try:
                listener(node_id, update_packet)
            except Exception as e:
                logger.error(f"Error notifying twin listener: {e}")


twin_sync_manager = TwinSyncManager()
