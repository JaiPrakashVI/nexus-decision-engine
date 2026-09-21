# ADR-001: Service Boundaries & Decoupled Modular Monolith Architecture

## Context
NEXUS requires high-throughput telemetry ingestion, time-series persistence, in-memory graph representation, physics-informed state reconstruction, discrete-event simulation, and local agentic AI decision support. We must decide on the macro-architectural boundary structure: microservices vs. modular monolith vs. serverless.

## Decision
We adopted a **decoupled modular architecture** composed of clear service boundaries:
1. **Secure Telemetry Gateway**: Standalone boundary terminating HTTPS/mTLS connections, performing rate limiting, and publishing to the event log.
2. **Streaming Event Broker**: Redis Streams providing decoupled log-based ingestion.
3. **Consumer & Persistence Worker**: Background service consuming from Redis and persisting to TimescaleDB.
4. **Digital Twin & Decision Service**: Standalone service hosting the NetworkX topology graph, state reconstruction engine, cascading failure simulator, local LLM orchestration, and WebSocket streaming.
5. **Command Center Frontend**: Standalone React/Vite single-page application.

## Rationale
- Decouples wire-speed edge ingestion from analytical computation and database write latency.
- Avoids the operational overhead, network serialization costs, and distributed tracing failures of dozens of microservices.
- Preserves high developmental velocity and allows reproducible local execution on developer workstations.

## Trade-Offs & Consequences
- Requires running Redis as the streaming intermediary.
- Simplifies deployment via Docker Compose or standalone local Python processes.
