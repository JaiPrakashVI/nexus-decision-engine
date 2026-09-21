# NEXUS Terminology Guide

This guide defines the foundational systems, digital-twin, data-engineering, and AI concepts used throughout NEXUS.

---

### 1. Core Systems & Ingestion
- **Telemetry**: Automated transmission of physical measurements (pressure, flow rate, vibration, temperature, power, battery) captured by remote sensor instruments to a central receiving system.
- **Sensor Node / Cyber-Physical Asset**: An edge instrument or physical machine (pump, pipe, valve, reservoir, power substation) monitored by the system.
- **Trace ID**: A globally unique UUID4 attached to each telemetry event at generation and preserved across the Gateway, Redis Streams, database, twin state, and decision engine for distributed end-to-end tracing.
- **Sequence Number**: A monotonically increasing integer per device used to detect duplicate transmissions, packet loss gaps, and out-of-order event arrivals.
- **Replay Protection**: Cryptographic and temporal validation ensuring old or intercepted packets cannot be re-injected into the gateway to spoof operational states.
- **mTLS (Mutual TLS)**: Two-way cryptographic authentication where the client authenticates the server's certificate AND the server validates the client's X.509 certificate against a trusted Root CA.
- **Token Bucket Rate Limiter**: An algorithm that maintains a bucket of tokens refilled at a constant rate; each incoming request consumes a token, shedding excess load when empty.

### 2. Streaming & Time-Series Persistence
- **Redis Stream**: An append-only log data structure in Redis supporting high-throughput `XADD` event publishing, consumer groups, message acknowledgments (`XACK`), and pending message inspection.
- **Consumer Group**: A pool of cooperating worker processes that partition the processing of a stream; each message in the stream is delivered to only one worker in the group.
- **Dead Letter Queue (DLQ)**: A dedicated secondary stream or queue where malformed, unparseable, or repeatedly failing messages are routed to prevent consumer pipeline stalling.
- **TimescaleDB**: An open-source time-series database built on top of PostgreSQL that automatically partitions time-series tables into time-based chunks called hypertables.
- **Hypertable**: An abstraction in TimescaleDB that presents time-partitioned tables as a single unified PostgreSQL table while optimizing time-series query performance and storage compression.

### 3. Digital Twin & Graph Modeling
- **Digital Twin**: A dynamic software representation of a physical system that mirrors operational conditions, tracks physical dependencies, estimates unobserved states, and simulates what-if intervention outcomes.
- **Dependency Graph**: A directed graph (implemented in NEXUS with NetworkX) where nodes represent physical assets and directed edges represent fluid flow or electrical power dependencies ($u \to v$ indicates $v$ depends on $u$).
- **Blast Radius**: The complete set of downstream nodes reachable via directed paths from a failed node that will experience starvation, pressure drops, or electrical disconnection.
- **Root-Cause Ancestors**: The set of predecessor nodes reachable upstream from an affected node used to identify the initiating point of failure.

### 4. State Reconstruction & Incomplete Information
- **Tripartite Operational State**: The explicit distinction maintained by NEXUS:
  - `OBSERVED`: Direct, fresh telemetry received within the observation window ($\Delta t \le 5\text{s}$), confidence $= 1.0$.
  - `INFERRED`: Telemetry is missing, but state is reconstructed from neighboring graph nodes using physical conservation laws, with exponential confidence decay $C(t) = e^{-\lambda \Delta t}$.
  - `UNKNOWN`: Telemetry missing beyond maximum inference threshold ($\Delta t > 60\text{s}$); confidence drops to baseline ($\le 0.2$).
- **Completeness Score**: The ratio of nodes currently receiving direct fresh telemetry: $Comp = \frac{N_{observed}}{N_{total}}$.
- **Observability Score**: Effective operational visibility accounting for reconstructed nodes: $Obs = \frac{N_{observed} + 0.6 \times N_{inferred}}{N_{total}}$.
- **MARE (Mean Absolute Reconstruction Error)**: The quantitative error between the inferred physical measurement and the true ground-truth value: $\text{MARE} = \frac{1}{N} \sum \frac{|y_{true} - y_{inferred}|}{|y_{true}| + \epsilon}$.

### 5. Anomaly Detection & Dark Processes
- **Z-Score Detector**: An interpretable statistical test measuring how many standard deviations an incoming measurement drifts from the rolling mean: $Z = \frac{|x - \mu|}{\sigma}$.
- **Sensor Flatline / Freeze**: An anomaly where a sensor repeatedly transmits the exact same float value over many consecutive cycles, indicating a stuck transmitter or locked transducer.
- **Multivariate Isolation Forest**: An unsupervised machine learning algorithm that isolates anomalous multi-dimensional vectors (e.g. high pump power draw with zero volumetric flow rate).
- **Dark Process / Missing Event**: An unobserved state transition (e.g. a node jumping directly from `OPERATIONAL` to `EMERGENCY_SHUTDOWN` without an intermediate `ALERT` event) caused by packet loss, sensor failure, or unlogged external actions.

### 6. Simulation & Decision Engine
- **Cascading Failure**: A failure sequence where the disruption of an upstream node triggers secondary trips or overloads in downstream dependent nodes.
- **What-If Simulation Sandbox**: An isolated deep copy of the digital twin topology where candidate interventions can be executed without impacting the live system.
- **Deterministic Decision Engine**: Rule- and constraint-based optimization engine that generates candidate recovery actions from standard operating procedures (SOPs), verifies hard physical constraints, and ranks plans by Recovery Time Objective (RTO) and blast radius reduction.
- **Local Agentic AI (Ollama)**: Locally hosted LLM ensemble providing natural language explanation, risk analysis, and candidate review. Operates strictly in advisory mode; cannot directly actuate infrastructure.

### 7. Performance & Benchmarking
- **Throughput (req/s)**: The number of telemetry packets successfully ingested, validated, and processed per second.
- **p50 Latency (Median)**: The latency threshold below which 50% of requests complete.
- **p95 Latency**: The latency threshold below which 95% of requests complete.
- **p99 Latency (Tail Latency)**: The latency threshold below which 99% of requests complete; measures worst-case responsiveness under load.
