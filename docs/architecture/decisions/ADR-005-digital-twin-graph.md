# ADR-005: NetworkX Directed Graph for Cyber-Physical Topology Representation

## Context
NEXUS requires an in-memory topological model to represent physical asset connectivity, fluid flow direction, electrical power dependencies, downstream blast radius, and upstream root-cause tracing.

## Alternatives Considered
1. **Graph Database (Neo4j)**: Heavy separate JVM infrastructure, introduces additional network serialization overhead on every telemetry tick.
2. **Ad-hoc Adjacency Lists**: Prone to bugs in path-finding, cycle detection, and topological sorting.
3. **NetworkX Directed Graph (`nx.DiGraph`)**: Standardized in-memory graph library in Python with rich graph traversal and topological reachability algorithms.

## Decision
We selected **NetworkX (`nx.DiGraph`)**.

## Rationale
- Zero external database dependencies; runs entirely in process memory.
- Instantaneous traversal speeds ($< 1\text{ms}$) for calculating downstream blast radius (`nx.descendants`) and upstream dependencies (`nx.ancestors`).
- Easily serialized to JSON for real-time visualization in the React operations command center.
