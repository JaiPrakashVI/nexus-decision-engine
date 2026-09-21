# How Everything Connects — 10 Core Concepts

If you only remember ten things about how NEXUS operates, remember these:

---

### 1. Cyber-Physical Assets Generate Raw Telemetry
Sensors mounted on pumps, pipes, valves, reservoirs, and power substations periodically capture physical metrics (pressure, flow rate, temperature, vibration, power, and battery). Telemetry is packaged with sequence numbers and unique trace IDs.

### 2. The Gateway Treats All Telemetry as Untrusted
The ingestion gateway terminates connections using mutual TLS (mTLS). It validates client X.509 certificates against the Root CA, checks the device registry, validates Pydantic bounds, checks rate limits, and rejects replayed or duplicate packets.

### 3. Redis Streams Asynchronously Decouples Ingestion from Processing
Accepted telemetry is appended to Redis Streams (`XADD`). This decouples sub-millisecond edge ingestion from slower database operations and analytical twin synchronization, protecting the gateway from backpressure.

### 4. TimescaleDB Stores Historical Time-Series Data
A stream consumer worker reads telemetry from consumer groups, acknowledges messages, routes failed payloads to a Dead Letter Queue (DLQ), and persists readings into TimescaleDB hypertables partitioned by time.

### 5. The Digital Twin Represents Operational Reality, Not Cold Rows
The digital twin is an in-memory directed dependency graph built with NetworkX. It maps upstream sources to downstream distribution zones and maintains live operational status (`OPERATIONAL`, `DEGRADED`, `CRITICAL`, `FAILED`).

### 6. State Reconstruction Explicitly Models Uncertainty
When telemetry is missing (up to 40% loss), NEXUS never silently guesses or fabricates facts. It categorizes state into:
- `OBSERVED`: Direct fresh measurement (confidence = 1.0).
- `INFERRED`: Reconstructed from adjacent graph nodes using mass conservation and pressure gradients with exponential confidence decay $C(t) = e^{-\lambda \Delta t}$.
- `UNKNOWN`: Telemetry missing beyond threshold (high uncertainty).

### 7. Missing Transitions Reveal Dark Processes
Industrial nodes follow formal state machine lifecycles (`OFFLINE` &rarr; `STARTING` &rarr; `OPERATIONAL` &rarr; `ALERT` &rarr; `EMERGENCY_SHUTDOWN`). If a node jumps from `OPERATIONAL` directly to `EMERGENCY_SHUTDOWN`, the system detects an unobserved transition (Dark Process) caused by packet drops or unlogged emergency trips.

### 8. Cascading Failures Are Discrete-Event Simulations
When an asset fails, NEXUS forks the digital twin topology into an isolated sandbox and simulates failure propagation step-by-step (e.g. pump failure &rarr; upstream line trip &rarr; reservoir draining &rarr; consumer district starvation), calculating exact blast radius and unserved demand.

### 9. Deterministic Logic Rules; The LLM Advises
The Deterministic Decision Engine evaluates available candidate actions, enforces physical constraints, and simulates outcomes. Candidate plans are then submitted to a 5-role local LLM ensemble (State Analyst, Risk Analyst, Recovery Planner, Adversarial Critic, Evaluator). The LLM operates strictly in an advisory capacity and can never directly actuate hardware.

### 10. The Loop Closes in the Operations Command Center
The frontend is a high-density React + Vite + Tailwind CSS cyber-physical command center. Through WebSockets, operators monitor live telemetry, watch dependency graph states evolve, dial data degradation from 0% to 40%, simulate incidents, and review validated recovery recommendations.
