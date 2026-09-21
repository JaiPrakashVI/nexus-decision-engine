# NEXUS Service Map — Who Talks to Whom

This table defines all inter-service communications, network protocols, payloads, and architectural purposes across NEXUS.

| Source Component | Destination Component | Network Protocol | Data Format / Payload | Architectural Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Sensor Simulator** | Secure Gateway | HTTPS / mTLS (Port 8443) | `TelemetryPayload` JSON + X.509 Client Cert | Transmit edge sensor measurements with cryptographic proof of identity |
| **Secure Gateway** | Redis Streams | Redis RESP Protocol (Port 6379) | Key-value dictionary / `XADD` | Append validated telemetry into append-only event stream log |
| **Stream Consumer** | Redis Streams | Redis RESP Protocol (Port 6379) | `XREADGROUP` / `XACK` / DLQ | Pull telemetry batches via consumer groups with acknowledgement |
| **Stream Consumer** | TimescaleDB | PostgreSQL TCP (Port 5432) | SQL `INSERT INTO telemetry` | Persist time-series readings in partitioned hypertables |
| **Stream Consumer** | Digital Twin Sync Manager | In-Process Async Callback | `TelemetryPayload` Object | Update in-memory topological node states in real time |
| **Digital Twin Engine** | NetworkX Dependency Graph | In-Memory Graph Memory | Directed DiGraph attributes | Maintain operational asset states, edges, and dependencies |
| **Reconstruction Engine** | Dependency Graph | In-Memory Graph Query | Predecessor/Successor node values | Reconstruct unobserved physical metrics using conservation laws |
| **Anomaly Detectors** | Database & Twin | In-Memory & SQL | Telemetry vectors & state transitions | Detect statistical drift, sensor freezes, and multi-variate faults |
| **Simulation Engine** | Isolated Sandbox Twin | In-Memory Deep Copy | Discrete-event step timeline | Simulate cascading failure propagation and candidate recovery actions |
| **Decision Engine** | Simulation Engine | Internal Method Call | Candidate Action & Target Nodes | Simulate candidate interventions to verify blast radius reduction |
| **Decision Engine** | Local LLM Client | HTTP REST (Port 11434) | JSON Prompt & Structured JSON Response | Multi-agent reasoning, risk forecasting, and adversarial critique |
| **Digital Twin API** | Web Browser / Frontend | HTTP REST (Port 8000) | JSON REST DTOs | Query topology, reconstruction scores, simulations, and decisions |
| **Digital Twin API** | Web Browser / Frontend | WebSockets (`/ws/telemetry`) | JSON Stream Events | Push live telemetry and graph updates to command center UI |
