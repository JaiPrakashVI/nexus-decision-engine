# NEXUS Data Flow Architecture

This document traces the path of data across all components, from physical sensor capture to presentation in the operations command center.

---

## High-Level Data Flow Diagram

```mermaid
flowchart TD
    subgraph Edge ["1. Edge Tier"]
        SIM[Sensor Simulator]
        FAULT[Fault Injection Engine]
        SIM -->|Raw Telemetry| FAULT
    end

    subgraph GatewayTier ["2. Secure Gateway Tier"]
        MTLS[mTLS Terminating Gateway]
        VAL[Pydantic Schema Validator]
        REPLAY[Replay & Drift Detector]
        RATE[Token Bucket Rate Limiter]

        FAULT -->|HTTPS + Client Cert| MTLS
        MTLS --> VAL
        VAL --> REPLAY
        REPLAY --> RATE
    end

    subgraph StreamingTier ["3. Event Decoupling Tier"]
        RS[(Redis Streams: telemetry:stream)]
        DLQ[(Dead Letter Queue: telemetry:dlq)]
        CON[Consumer Worker Group]

        RATE -->|XADD Accepted| RS
        RS -->|XREADGROUP| CON
        CON -.->|Failed / Poisoned| DLQ
    end

    subgraph PersistenceTier ["4. Persistent Storage Tier"]
        TS[(TimescaleDB Hypertable)]
        CON -->|Async SQL Insert| TS
    end

    subgraph DigitalTwinTier ["5. Digital Twin & Analytics Tier"]
        SYNC[Sync Manager]
        GRAPH[NetworkX Dependency Graph]
        RECON[State Reconstruction Engine]
        ANOM[Anomaly & Dark Process Detectors]
        SIM_ENG[Cascading Simulation Engine]

        CON -->|In-Memory Callback| SYNC
        SYNC --> GRAPH
        GRAPH <--> RECON
        GRAPH --> ANOM
        ANOM -->|Trigger Cascade| SIM_ENG
    end

    subgraph IntelligenceTier ["6. Closed-Loop Decision & AI Tier"]
        DEC_ENG[Deterministic Decision Engine]
        LLM[Local LLM Multi-Agent Ensemble]

        SIM_ENG <--> DEC_ENG
        DEC_ENG <-->|Structured Context / JSON| LLM
    end

    subgraph PresentationTier ["7. Command Center UI"]
        API[FastAPI Gateway & WebSocket Server]
        WS[WebSocket Stream: /ws/telemetry]
        UI[React 18 Operations Command Center]

        SYNC --> API
        DEC_ENG --> API
        API --> WS
        WS --> UI
    end
```

---

## Step-by-Step Data Transformations

1. **Edge Generation & Degradation**:
   Measurements are captured in SI units (`pressure_psi`, `flow_rate_gpm`, `temperature_c`). The Fault Injection Engine selectively applies packet loss (0% to 40%), Gaussian noise, transmission jitter, or duplicate cloning.
2. **Gateway Ingestion & Sanitization**:
   The gateway checks client identity against Root CA, extracts the Common Name, verifies the device registry, sanitizes timestamps, checks sequence numbers, and validates physical coordinate bounds.
3. **Stream Buffering**:
   Accepted records are converted into Redis Stream field dictionaries and buffered with bounded length (`MAXLEN ~ 100000`).
4. **Time-Series Persistence**:
   The consumer worker formats payloads into SQLAlchemy model instances and flushes to TimescaleDB hypertables.
5. **Topological Graph Reflection**:
   The `TwinSyncManager` updates the node attributes in `InfrastructureTopology`. If fresh telemetry arrived, `state_source` is set to `OBSERVED` with confidence 1.0. If missing, `StateReconstructor` applies mass conservation ($\sum Q_{in} = \sum Q_{out}$) and head-loss gradients to infer physical state with exponential confidence decay $C(t) = e^{-\lambda \Delta t}$.
6. **Failure & Intervention Simulation**:
   When an asset fails, an isolated sandbox copy of the graph is created. Discrete-event steps simulate upstream starvation and downstream demand shortfalls.
7. **Decision Engine & Multi-Agent Deliberation**:
   Candidate interventions are generated from standard operating procedures (SOPs), tested against physical constraints, simulated in the sandbox, reviewed by the 5-role agentic AI ensemble, and broadcast to the dashboard.
