"""
NEXUS Digital Twin Graph Topology
Directed dependency graph built with NetworkX representing cyber-physical smart municipal infrastructure.
"""

from typing import Dict, List, Set, Optional, Any
import networkx as nx
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class OperationalState(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    FAILED = "FAILED"
    OFFLINE = "OFFLINE"


class StateSource(str, Enum):
    OBSERVED = "OBSERVED"   # Fresh telemetry received directly
    INFERRED = "INFERRED"   # Reconstructed from adjacent graph nodes
    UNKNOWN = "UNKNOWN"     # Missing beyond maximum latency threshold


@dataclass
class TwinNodeData:
    node_id: str
    node_type: str  # source, pump, pipe, valve, reservoir, substation, district
    name: str
    latitude: float
    longitude: float
    capacity: float = 100.0
    nominal_pressure: float = 60.0
    current_pressure: float = 60.0
    current_flow: float = 50.0
    current_temp: float = 20.0
    current_vibration: float = 0.5
    current_power: float = 10.0
    battery_pct: float = 100.0
    operational_state: OperationalState = OperationalState.OPERATIONAL
    state_source: StateSource = StateSource.OBSERVED
    confidence: float = 1.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class InfrastructureTopology:
    """
    Manages the cyber-physical dependency graph using NetworkX.
    Nodes represent assets (pumps, pipes, valves, reservoirs, districts).
    Directed edges represent physical flow and operational dependencies (u -> v means v depends on u).
    """

    def __init__(self):
        self.graph: nx.DiGraph = nx.DiGraph()
        self._nodes: Dict[str, TwinNodeData] = {}
        self.build_default_topology()

    def build_default_topology(self):
        """Constructs a realistic 25-node municipal water & power distribution grid."""
        self.graph.clear()
        self._nodes.clear()

        # 1. Sources
        self.add_node("source_01", "source", "Aquifer Wellfield Alpha", 43.540, -80.250, capacity=500.0, nominal_pressure=80.0)
        self.add_node("source_02", "source", "River Intake Station Beta", 43.555, -80.235, capacity=400.0, nominal_pressure=75.0)

        # 2. Power Substations
        self.add_node("substation_01", "substation", "Grid Substation North", 43.545, -80.245, capacity=1000.0)
        self.add_node("substation_02", "substation", "Grid Substation South", 43.535, -80.255, capacity=1000.0)

        # 3. Pumping Stations (Power dependent)
        self.add_node("pump_01", "pump", "Primary Lift Pump 1", 43.541, -80.248, capacity=300.0, nominal_pressure=85.0)
        self.add_node("pump_02", "pump", "Booster Pump Station 2", 43.550, -80.240, capacity=300.0, nominal_pressure=85.0)
        self.add_node("pump_03", "pump", "Auxiliary Backup Pump 3", 43.542, -80.247, capacity=200.0, nominal_pressure=80.0)

        # 4. Transmission Pipes
        self.add_node("pipe_01", "pipe", "Main Trunk Line A", 43.543, -80.246, capacity=400.0)
        self.add_node("pipe_02", "pipe", "Main Trunk Line B", 43.548, -80.242, capacity=400.0)
        self.add_node("pipe_03", "pipe", "Cross-Connect Line C", 43.545, -80.244, capacity=250.0)
        self.add_node("pipe_04", "pipe", "Reservoir Feeder Line", 43.546, -80.238, capacity=350.0)
        self.add_node("pipe_05", "pipe", "Highland Service Pipe", 43.552, -80.230, capacity=200.0)
        self.add_node("pipe_06", "pipe", "Industrial Service Pipe", 43.538, -80.260, capacity=300.0)

        # 5. Isolation & Pressure Control Valves
        self.add_node("valve_01", "valve", "Inlet Isolation Valve 1", 43.542, -80.247, capacity=300.0)
        self.add_node("valve_02", "valve", "Bypass Control Valve 2", 43.544, -80.245, capacity=250.0)
        self.add_node("valve_03", "valve", "Pressure Reducing Valve 3", 43.549, -80.241, capacity=300.0)
        self.add_node("valve_04", "valve", "Reservoir Flow Valve 4", 43.546, -80.237, capacity=350.0)

        # 6. Storage Reservoirs
        self.add_node("storage_01", "reservoir", "Highland Storage Tank", 43.553, -80.228, capacity=1000.0, nominal_pressure=55.0)
        self.add_node("storage_02", "reservoir", "Downtown Balancing Basin", 43.537, -80.262, capacity=800.0, nominal_pressure=50.0)

        # 7. Distribution Zones / Consumer Districts
        self.add_node("district_alpha", "district", "Metro Commercial Core", 43.545, -80.235, capacity=250.0, nominal_pressure=55.0)
        self.add_node("district_beta", "district", "North Residential Sector", 43.555, -80.225, capacity=200.0, nominal_pressure=50.0)
        self.add_node("district_gamma", "district", "South Industrial Park", 43.535, -80.265, capacity=350.0, nominal_pressure=60.0)

        # 8. Define Directed Dependency Edges
        # Power dependencies
        self.add_edge("substation_01", "pump_01", relation="powers")
        self.add_edge("substation_01", "pump_02", relation="powers")
        self.add_edge("substation_02", "pump_03", relation="powers")

        # Hydraulic Flow path 1 (Source 1 -> Pump 1 -> Valve 1 -> Pipe 1 -> Pipe 3)
        self.add_edge("source_01", "pump_01", relation="feeds")
        self.add_edge("source_01", "pump_03", relation="feeds")
        self.add_edge("pump_01", "valve_01", relation="supplies")
        self.add_edge("pump_03", "valve_01", relation="supplies")
        self.add_edge("valve_01", "pipe_01", relation="flows_into")
        self.add_edge("pipe_01", "pipe_03", relation="connects_to")

        # Hydraulic Flow path 2 (Source 2 -> Pump 2 -> Valve 2 -> Pipe 2 -> Pipe 3)
        self.add_edge("source_02", "pump_02", relation="feeds")
        self.add_edge("pump_02", "valve_02", relation="supplies")
        self.add_edge("valve_02", "pipe_02", relation="flows_into")
        self.add_edge("pipe_02", "pipe_03", relation="connects_to")

        # Flow from Pipe 3 into Valves and Feeder Pipes
        self.add_edge("pipe_03", "valve_03", relation="flows_into")
        self.add_edge("valve_03", "pipe_04", relation="flows_into")
        self.add_edge("pipe_04", "valve_04", relation="flows_into")

        # Reservoir filling & delivery
        self.add_edge("valve_04", "storage_01", relation="fills")
        self.add_edge("pipe_01", "storage_02", relation="fills")

        # Distribution from pipes and reservoirs into consumer districts
        self.add_edge("storage_01", "pipe_05", relation="discharges")
        self.add_edge("pipe_05", "district_beta", relation="supplies")

        self.add_edge("pipe_04", "district_alpha", relation="supplies")

        self.add_edge("storage_02", "pipe_06", relation="discharges")
        self.add_edge("pipe_06", "district_gamma", relation="supplies")

    def add_node(self, node_id: str, node_type: str, name: str, lat: float, lon: float, **kwargs):
        data = TwinNodeData(
            node_id=node_id,
            node_type=node_type,
            name=name,
            latitude=lat,
            longitude=lon,
            **kwargs
        )
        self._nodes[node_id] = data
        self.graph.add_node(node_id, **data.__dict__)

    def add_edge(self, u: str, v: str, relation: str = "depends_on"):
        self.graph.add_edge(u, v, relation=relation)

    def get_node(self, node_id: str) -> Optional[TwinNodeData]:
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> Dict[str, TwinNodeData]:
        return self._nodes

    def get_downstream_blast_radius(self, failed_node_id: str) -> List[str]:
        """Returns all downstream nodes that depend on this node."""
        if failed_node_id not in self.graph:
            return []
        descendants = nx.descendants(self.graph, failed_node_id)
        return list(descendants)

    def get_upstream_sources(self, node_id: str) -> List[str]:
        """Returns all upstream predecessor nodes feeding this node."""
        if node_id not in self.graph:
            return []
        ancestors = nx.ancestors(self.graph, node_id)
        return list(ancestors)

    def get_predecessors(self, node_id: str) -> List[str]:
        if node_id not in self.graph:
            return []
        return list(self.graph.predecessors(node_id))

    def get_successors(self, node_id: str) -> List[str]:
        if node_id not in self.graph:
            return []
        return list(self.graph.successors(node_id))

    def to_dict(self) -> Dict[str, Any]:
        """Exports graph structure and live node data for the frontend dashboard."""
        nodes_list = []
        for n_id, data in self._nodes.items():
            nodes_list.append({
                "id": data.node_id,
                "name": data.name,
                "type": data.node_type,
                "lat": data.latitude,
                "lon": data.longitude,
                "state": data.operational_state.value,
                "source": data.state_source.value,
                "confidence": round(data.confidence, 3),
                "pressure": round(data.current_pressure, 2),
                "flow": round(data.current_flow, 2),
                "temp": round(data.current_temp, 2),
                "vibration": round(data.current_vibration, 2),
                "power": round(data.current_power, 2),
                "battery": round(data.battery_pct, 1),
                "last_updated": data.last_updated.isoformat(),
            })

        edges_list = []
        for u, v, attrs in self.graph.edges(data=True):
            edges_list.append({
                "source": u,
                "target": v,
                "relation": attrs.get("relation", "depends_on"),
            })

        return {
            "node_count": len(nodes_list),
            "edge_count": len(edges_list),
            "nodes": nodes_list,
            "edges": edges_list,
        }


topology = InfrastructureTopology()
