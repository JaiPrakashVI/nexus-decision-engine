# NEXUS Architectural Specification

This document provides a concise reference to the high-level architecture, design patterns, and engineering principles of NEXUS.

---

## Closed-Loop Core Spine
NEXUS enforces a closed-loop cyber-physical architecture:
```
Imperfect Telemetry
  ↓
Secure Ingestion (mTLS, Pydantic, Rate Limiting, Replay Guard)
  ↓
Event Decoupling (Redis Streams: telemetry:stream)
  ↓
Persistence Worker & TimescaleDB Hypertables
  ↓
Digital Twin Topology Graph (NetworkX DiGraph)
  ↓
State Reconstruction & Bayesian Confidence Decay
  ↓
Anomaly & Dark Process Detection
  ↓
Cascading Disruption Simulation Sandbox
  ↓
Deterministic Decision Engine (Physical Constraints & SOP Actions)
  ↓
Local Agentic AI Advisory Ensemble (5 Specialized Roles)
  ↓
Simulation-Verified Recommendation & Evaluated Recovery
```

---

## Service Boundaries
1. **Gateway**: Terminates client mTLS connections, performs schema/bounds validation, enforces token-bucket rate limits, rejects replays, and publishes to Redis Streams.
2. **Streaming Event Broker**: Redis Streams providing decoupled, append-only log ingestion.
3. **Stream Consumer**: Reads message batches with consumer groups, writes to TimescaleDB hypertables, handles DLQ routing, and notifies in-memory twin listeners.
4. **Digital Twin Service**: In-memory NetworkX directed graph, state reconstruction estimator, cascading failure simulator, deterministic constraint solver, local LLM orchestration, and WebSocket server.
5. **Operations Command Center**: Single-page application built with React 18, Vite, TypeScript, and Tailwind CSS.

---

## Architectural Decision Records (ADRs)
For complete rationale, trade-offs, and context on technology selection, consult:
- [ADR-001: Service Boundaries & Modular Architecture](docs/architecture/decisions/ADR-001-service-boundaries.md)
- [ADR-002: Redis Streams for Ingestion Decoupling](docs/architecture/decisions/ADR-002-redis-streams.md)
- [ADR-003: TimescaleDB for Hybrid Time-Series Persistence](docs/architecture/decisions/ADR-003-timescaledb.md)
- [ADR-004: Local LLM & Isolation from Infrastructure Actuation](docs/architecture/decisions/ADR-004-local-llm.md)
- [ADR-005: NetworkX Directed Graph Topology](docs/architecture/decisions/ADR-005-digital-twin-graph.md)
- [ADR-006: Mutual TLS (mTLS) Cryptographic Device Authentication](docs/architecture/decisions/ADR-006-mtls.md)
