# Architecture Learning Questions

This document contains conceptual and architectural questions categorized by difficulty level. Every question can be answered by studying the NEXUS repository and its documentation.

---

## Beginner Level

### 1. What is telemetry and why does NEXUS ingest it?
**Answer**: Telemetry is automated transmission of physical measurements (pressure, flow rate, temperature, vibration, electrical power, battery level) from remote instruments. NEXUS ingests it to maintain an accurate digital representation of the cyber-physical grid in real time.

### 2. Why does NEXUS have a separate Secure Gateway instead of letting sensors write directly to PostgreSQL?
**Answer**:
1. **Security & Authentication**: Direct database access requires exposing database credentials and ports to untrusted field devices. The gateway enforces mTLS cryptographic certificate validation and device registry checks.
2. **Backpressure & Decoupling**: Direct database inserts under high concurrency (e.g. 5,000 devices streaming at 1 Hz) create database connection pool exhaustion and transaction lock contention. The gateway validates packets and immediately appends to high-speed Redis Streams logs.
3. **Input Sanitization**: Replay detection, timestamp sanity, and schema bounds checking are performed at the network boundary before reaching storage.

### 3. What is the difference between PostgreSQL and TimescaleDB?
**Answer**: PostgreSQL is a traditional relational database. TimescaleDB is an extension for PostgreSQL that automatically partitions time-series tables into time-based chunks called hypertables, significantly improving write throughput and time-range query speeds on millions of time-stamped telemetry readings.

### 4. What is a digital twin and how is it different from a database?
**Answer**: A database is a passive storage system that stores historical rows. A digital twin is an active in-memory model (built with NetworkX) that reflects the live operational state, models physical dependency relationships (which pump feeds which pipe), estimates missing data through physics-based reconstruction, and simulates what-if failure scenarios.

---

## Intermediate Level

### 5. Why do telemetry events include sequence numbers and trace IDs?
**Answer**:
- **Sequence numbers**: Monotonically increasing per device. They allow the gateway and digital twin to detect packet drops (gaps in sequence), out-of-order packets ($seq < seq_{max}$), and duplicate transmissions ($seq == seq_{last}$).
- **Trace IDs**: Distributed UUID4 identifiers that remain with the packet through Gateway $\to$ Redis Streams $\to$ Consumer $\to$ Database $\to$ Twin $\to$ Decision Engine, allowing end-to-end tracing of any anomaly or intervention back to the originating sensor reading.

### 6. How does NEXUS distinguish between OBSERVED, INFERRED, and UNKNOWN states?
**Answer**:
- `OBSERVED`: A direct packet arrived within the observation window ($\Delta t \le 5\text{s}$); confidence $= 1.0$.
- `INFERRED`: Telemetry is missing ($5\text{s} < \Delta t \le 60\text{s}$); the state is reconstructed from neighboring nodes in the dependency graph using mass conservation and pressure gradients. Confidence decays exponentially: $C(\Delta t) = e^{-\lambda \Delta t}$.
- `UNKNOWN`: Telemetry has been missing for over 60 seconds; uncertainty is high and confidence drops to baseline ($\le 0.2$).

### 7. What is a "Dark Process" and how does NEXUS detect it?
**Answer**: A Dark Process is an unobserved operational state transition. Industrial assets have permitted transition paths (`OPERATIONAL` $\to$ `ALERT` $\to$ `EMERGENCY_SHUTDOWN`). If an asset transitions directly from `OPERATIONAL` to `EMERGENCY_SHUTDOWN`, the intermediate `ALERT` event was unlogged or dropped. NEXUS's `DarkProcessDetector` tracks the finite state machine and flags skipped transitions as candidate missing events.

### 8. Why are there two tiers of anomaly detectors (Statistical and ML)?
**Answer**:
- **Statistical (Z-score, EWMA, Flatline)**: Fast, lightweight ($< 10\mu\text{s}$ latency), and fully interpretable for single-metric spikes or frozen sensors.
- **Multivariate ML (Isolation Forest)**: Analyzes multi-dimensional correlations that univariate tests miss—such as an electric motor drawing maximum power (30 kW) while volumetric flow is zero (0 GPM), which reveals mechanical impeller seizure or cavitation.

---

## Advanced Level

### 9. What happens if the Redis broker goes down?
**Answer**: The NEXUS gateway incorporates resilient fallbacks. The `StreamProducer` catches connection errors, records Prometheus rejection counters, and can route packets to local bounded memory queues or direct offline processing, preventing process crashes during infrastructure maintenance.

### 10. Why is the Local LLM never allowed to directly execute actions on the infrastructure?
**Answer**: LLMs are probabilistic text generators susceptible to hallucinations, prompt injections, and non-deterministic variations. In cyber-physical infrastructure (water distribution, power grids), an unauthorized valve closure or over-pressurization can rupture pipelines or cause physical injury. In NEXUS:
1. Candidate actions are strictly formulated by the Deterministic Decision Engine.
2. Hard physical constraints are enforced by deterministic rules.
3. Candidate interventions are validated inside an isolated digital twin simulation sandbox before any action can be recommended to human operators.

### 11. How does NEXUS maintain physical plausibility under 40% missing telemetry?
**Answer**: NEXUS leverages the topology of the smart grid. In fluid transmission networks, mass is conserved: the flow entering a junction must equal the flow exiting ($\sum Q_{in} = \sum Q_{out}$). If a sensor on a transmission pipe is dropped, the `StateReconstructor` queries the functional upstream pumps and downstream reservoirs to interpolate the missing flow and pressure head loss, bounding the Mean Absolute Reconstruction Error (MARE) below 0.25 even under extreme 40% telemetry loss.
