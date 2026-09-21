# NEXUS Event Lifecycle & Exception Handling

This document details how the NEXUS architecture handles every class of telemetry event, including normal flow, duplicates, out-of-order arrivals, timestamp drift, and corrupted payloads.

---

## Event Lifecycle Matrix

| Event Condition | Gateway Behavior | Stream / Queue Behavior | Database / Persistence | Digital Twin Reaction |
| :--- | :--- | :--- | :--- | :--- |
| **Valid Nominal Event** | Returns `202 Accepted` | Appended via `XADD` to stream | Persisted to TimescaleDB hypertable | Node marked `OBSERVED`, confidence = 1.0, physical gauges updated |
| **Missing / Dropped Event** | Never reaches gateway | Skipped in stream | No row inserted for missing timestamp | After 5s gap, node transitions to `INFERRED`, values estimated via conservation laws, confidence decays |
| **Duplicate Event** | `ReplayDetector` detects seen `trace_id`; returns `400 Bad Request` | Not published to stream | Rejected | No twin state modification; duplicate counter incremented |
| **Out-of-Order Event** | Marked `DEGRADED`; returns `202 Accepted` | Appended to stream with out-of-order flag | Persisted with original timestamp | Ingestion logged; sequence tracking updated |
| **Timestamp Drift (> 300s past or > 60s future)** | Rejected with `400 Bad Request` | Not published | Rejected | No twin modification; security rejection counter incremented |
| **Malformed / Invalid Schema (e.g. negative pressure)** | Pydantic validation error; returns `422 Unprocessable Entity` | Not published | Rejected | No twin modification; validation error logged |
| **Unauthorized / Rogue Cert** | mTLS handshake or registry check fails; returns `401 Unauthorized` | Not published | Rejected | No twin modification; security alert triggered |
| **Poison / Deserialization Failure in Consumer** | N/A (Already passed gateway) | Consumer catches error, forwards to Dead Letter Queue (`nexus:telemetry:dlq`), ACKs original message | Error details written to DLQ | Twin state unaffected; consumer pipeline continues running |

---

## Detailed Handling Paths

### 1. The Normal Path
1. Physical asset generates packet with monotonic sequence number and UUID4 trace ID.
2. Gateway verifies client certificate against Root CA.
3. Gateway validates schema bounds and checks rate limits.
4. Gateway appends to Redis Stream and returns `202 Accepted`.
5. Consumer worker pulls batch, writes to TimescaleDB, and notifies Digital Twin sync manager.
6. Digital twin updates node attributes and emits update to active WebSocket connections.

### 2. The Degraded / Missing Telemetry Path
1. Fault injector or network outage drops packet.
2. Gateway never receives reading.
3. In the digital twin, elapsed time since last direct telemetry exceeds observation threshold ($\tau_{obs} = 5.0\text{s}$).
4. `StateReconstructor` flags node as `INFERRED`.
5. Reconstructor queries topological graph:
   - Evaluates upstream predecessors to compute incoming flow rate $\sum Q_{in}$.
   - Evaluates upstream pressure minus friction head-loss to estimate junction pressure.
   - Computes Bayesian confidence decay: $C(t) = e^{-\lambda \Delta t}$.
6. If telemetry resumes, node immediately transitions back to `OBSERVED` with confidence 1.0.

### 3. The Poison Message / DLQ Path
If a message in Redis Streams encounters an unexpected exception during consumer processing:
1. The consumer worker catches the exception.
2. The payload, error stack trace, and original Redis message ID are forwarded to the Dead Letter Queue (`nexus:telemetry:dlq`).
3. The message is acknowledged (`XACK`) in the primary stream so worker processing does not deadlock or loop indefinitely.
4. A warning is logged and Prometheus rejection counters are incremented.
