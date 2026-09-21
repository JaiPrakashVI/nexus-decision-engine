"""
NEXUS State Reconstruction & Uncertainty Estimation Engine
Reconstructs operational states and physical measurements when telemetry is missing or delayed.
Explicitly distinguishes OBSERVED, INFERRED, and UNKNOWN states with Bayesian-inspired confidence decay.
"""

from datetime import datetime, timezone, timedelta
import math
from typing import Dict, Optional, Tuple, Any
import logging

from digital_twin.graph.topology import (
    topology,
    OperationalState,
    StateSource,
    TwinNodeData,
)

logger = logging.getLogger("nexus.reconstruction")


class StateReconstructor:
    def __init__(
        self,
        obs_window_sec: float = 5.0,
        max_infer_window_sec: float = 60.0,
        decay_rate_lambda: float = 0.04
    ):
        self.obs_window = timedelta(seconds=obs_window_sec)
        self.max_infer_window = timedelta(seconds=max_infer_window_sec)
        self.decay_rate = decay_rate_lambda

    def evaluate_node_state(
        self,
        node_id: str,
        current_time: Optional[datetime] = None
    ) -> Tuple[OperationalState, StateSource, float, Dict[str, float]]:
        """
        Evaluates a node's operational state and reconstructs missing values if unobserved.
        Returns: (state, source, confidence, reconstructed_values)
        """
        now = current_time or datetime.now(timezone.utc)
        node = topology.get_node(node_id)
        if not node:
            return OperationalState.OFFLINE, StateSource.UNKNOWN, 0.0, {}

        elapsed = now - node.last_updated

        # 1. Freshly Observed State
        if elapsed <= self.obs_window:
            return (
                node.operational_state,
                StateSource.OBSERVED,
                1.0,
                {
                    "pressure_psi": node.current_pressure,
                    "flow_rate_gpm": node.current_flow,
                    "temperature_c": node.current_temp,
                    "vibration_rms": node.current_vibration,
                }
            )

        # 2. Inferred State via Graph Neighbor Conservation
        if elapsed <= self.max_infer_window:
            # Exponential confidence decay: C(t) = exp(-lambda * (elapsed - tau_obs))
            delta_sec = (elapsed - self.obs_window).total_seconds()
            confidence = max(0.2, math.exp(-self.decay_rate * delta_sec))

            reconstructed_vals = self._reconstruct_physical_values(node)

            # Determine inferred operational state from reconstructed values
            inferred_state = self._infer_operational_state(node, reconstructed_vals)

            # Update node's in-memory twin state
            node.state_source = StateSource.INFERRED
            node.confidence = confidence
            node.current_pressure = reconstructed_vals["pressure_psi"]
            node.current_flow = reconstructed_vals["flow_rate_gpm"]

            return inferred_state, StateSource.INFERRED, confidence, reconstructed_vals

        # 3. Unknown State (Telemetry missing beyond inference threshold)
        node.state_source = StateSource.UNKNOWN
        node.confidence = 0.1
        return (
            OperationalState.DEGRADED if node.operational_state != OperationalState.FAILED else OperationalState.FAILED,
            StateSource.UNKNOWN,
            0.1,
            {
                "pressure_psi": node.nominal_pressure * 0.5,
                "flow_rate_gpm": 0.0,
                "temperature_c": node.current_temp,
                "vibration_rms": 0.0,
            }
        )

    def _reconstruct_physical_values(self, node: TwinNodeData) -> Dict[str, float]:
        """
        Physics-based reconstruction using conservation of mass and hydraulic gradients.
        """
        predecessors = topology.get_predecessors(node.node_id)
        successors = topology.get_successors(node.node_id)

        est_flow = node.current_flow
        est_pressure = node.current_pressure

        # Flow Reconstruction: Check upstream feeding flows
        if predecessors:
            upstream_flows = [
                topology.get_node(p).current_flow
                for p in predecessors
                if topology.get_node(p) is not None
            ]
            if upstream_flows:
                # Average upstream flow adjusted by node nominal capacity ratio
                est_flow = sum(upstream_flows) / len(upstream_flows)

        # Pressure Reconstruction: Downstream pressure drop model
        if predecessors:
            upstream_pressures = [
                topology.get_node(p).current_pressure
                for p in predecessors
                if topology.get_node(p) is not None
            ]
            if upstream_pressures:
                # Slight friction head-loss along transmission
                avg_upstream_p = sum(upstream_pressures) / len(upstream_pressures)
                est_pressure = max(0.0, avg_upstream_p - 2.5)
        elif successors:
            downstream_pressures = [
                topology.get_node(s).current_pressure
                for s in successors
                if topology.get_node(s) is not None
            ]
            if downstream_pressures:
                avg_downstream_p = sum(downstream_pressures) / len(downstream_pressures)
                est_pressure = avg_downstream_p + 2.5

        return {
            "pressure_psi": round(est_pressure, 2),
            "flow_rate_gpm": round(est_flow, 2),
            "temperature_c": round(node.current_temp, 2),
            "vibration_rms": round(node.current_vibration, 2),
        }

    def _infer_operational_state(self, node: TwinNodeData, vals: Dict[str, float]) -> OperationalState:
        """Categorizes state based on reconstructed physical thresholds."""
        p = vals["pressure_psi"]
        q = vals["flow_rate_gpm"]

        if p < 15.0 or q < 5.0:
            return OperationalState.FAILED
        if p < 35.0 or p > 130.0:
            return OperationalState.CRITICAL
        if p < 45.0 or vals.get("vibration_rms", 0.0) > 4.0:
            return OperationalState.DEGRADED
        return OperationalState.OPERATIONAL

    def update_all_nodes(self) -> Dict[str, Any]:
        """Runs reconstruction across the entire digital twin topology."""
        now = datetime.now(timezone.utc)
        results = {}
        observed_count = 0
        inferred_count = 0
        unknown_count = 0

        for node_id in topology.get_all_nodes():
            state, source, conf, vals = self.evaluate_node_state(node_id, now)
            results[node_id] = {
                "state": state.value,
                "source": source.value,
                "confidence": round(conf, 3),
                "values": vals,
            }
            if source == StateSource.OBSERVED:
                observed_count += 1
            elif source == StateSource.INFERRED:
                inferred_count += 1
            else:
                unknown_count += 1

        total = len(results) or 1
        completeness = round(observed_count / total, 3)
        observability = round((observed_count + 0.6 * inferred_count) / total, 3)

        return {
            "timestamp": now.isoformat(),
            "total_nodes": total,
            "observed_nodes": observed_count,
            "inferred_nodes": inferred_count,
            "unknown_nodes": unknown_count,
            "completeness_score": completeness,
            "observability_score": observability,
            "nodes": results,
        }


reconstructor = StateReconstructor()
