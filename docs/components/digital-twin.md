# Component Deep-Dive: Digital Twin Engine

The Digital Twin Engine is the central cyber-physical model in NEXUS. It represents live operational reality and physical asset dependencies rather than simply storing historical records in a relational database.

---

## 1. What is the Digital Twin?
The Digital Twin in NEXUS is an in-memory directed dependency graph built with **NetworkX (`nx.DiGraph`)** located at `digital_twin/graph/topology.py`.

It maps physical assets:
- **Water Sources**: Aquifer wells, river intake stations.
- **Power Substations**: Electrical grid supply substations.
- **Pumping Stations**: Primary lift pumps, booster stations, auxiliary backup pumps.
- **Transmission Pipelines**: Main trunk lines, cross-connect lines, service pipes.
- **Valves**: Inlet isolation valves, bypass valves, pressure reducing valves.
- **Storage Reservoirs**: Elevated storage tanks, balancing basins.
- **Consumer Districts**: Commercial core, residential sectors, industrial parks.

---

## 2. Graph Dependency Modeling
In the NetworkX graph, directed edges represent physical flow and operational dependencies:
$$\text{Edge}(u \to v) \implies v \text{ depends operationally on } u$$

Example topology connections:
- `substation_01` $\to$ `pump_01` (Relation: `powers`)
- `source_01` $\to$ `pump_01` (Relation: `feeds`)
- `pump_01` $\to$ `valve_01` (Relation: `supplies`)
- `valve_01` $\to$ `pipe_01` (Relation: `flows_into`)
- `pipe_01` $\to$ `storage_02` (Relation: `fills`)
- `storage_02` $\to$ `pipe_06` $\to$ `district_gamma` (Relation: `supplies`)

---

## 3. Graph Algorithms Implemented
- **Downstream Blast Radius (`nx.descendants(graph, node_id)`)**:
  Identifies all downstream nodes that will experience pressure loss or starvation if the target node fails.
- **Upstream Root-Cause Ancestors (`nx.ancestors(graph, node_id)`)**:
  Traces all upstream suppliers to diagnose the originating point of an observed pressure drop.
- **Predecessors & Successors**:
  Fast $O(1)$ query used by the State Reconstruction Engine to balance incoming flows and pressure drops.

---

## 4. State Synchronization
When the stream consumer receives a fresh telemetry packet:
1. `TwinSyncManager` updates the node's physical fields (`current_pressure`, `current_flow`, `battery_pct`).
2. The node's state source is set to `OBSERVED`.
3. Its Bayesian confidence is set to `1.0`.
4. Operational status is evaluated:
   - Pressure $< 15\text{ PSI}$ or Battery $< 5\% \implies$ `FAILED`
   - Pressure $< 35\text{ PSI}$ or Vibration $> 6.0\text{ mm/s} \implies$ `CRITICAL`
   - Pressure $< 45\text{ PSI}$ or Vibration $> 3.0\text{ mm/s} \implies$ `DEGRADED`
   - Otherwise $\implies$ `OPERATIONAL`
5. An event is dispatched to active WebSockets to update the React Command Center in real time.
