# NEXUS API Specification

NEXUS exposes clean, versioned REST endpoints and real-time WebSocket interfaces.

---

## 1. Secure Telemetry Gateway API (Port 8443)

### `POST /api/v1/telemetry`
- **Description**: Ingests a single telemetry reading from an authorized cyber-physical device.
- **Request Body**: `TelemetryPayload` JSON.
- **Response**: `202 Accepted` with `IngestionStatus` JSON:
  ```json
  {
    "status": "ACCEPTED",
    "device_id": "pump_01",
    "trace_id": "4b6e8284-90aa-4340-a19f-b77138374d75",
    "received_at": "2026-09-21T22:15:00Z",
    "message": "Event ingested successfully [redis_id: 1726938920123-0]"
  }
  ```
- **Error Codes**:
  - `400 Bad Request`: Replay attack, duplicate trace ID, or extreme clock drift.
  - `401 Unauthorized`: Missing or invalid client certificate.
  - `403 Forbidden`: Unregistered or revoked device.
  - `422 Unprocessable Entity`: Schema boundary violation.
  - `429 Too Many Requests`: Device rate limit exceeded.

### `POST /api/v1/telemetry/batch`
- **Description**: Ingests a batch of telemetry readings.
- **Response**: `202 Accepted` with a list of `IngestionStatus`.

### `GET /health`
- **Description**: Service health check returning gateway and Redis connection status.

### `GET /metrics`
- **Description**: Prometheus observability metrics (ingestion rates, latencies, rejections).

---

## 2. Digital Twin & Decision API (Port 8000)

### `GET /api/v1/topology`
- **Description**: Returns the complete cyber-physical dependency graph (nodes, edges, live physical parameters, and states).

### `GET /api/v1/state/reconstruction`
- **Description**: Evaluates current state reconstruction across all nodes, returning stream completeness, observability score, and Bayesian confidence values.

### `GET /api/v1/dark-processes`
- **Description**: Returns missing state transitions and unlogged process deviations detected by the finite state machine tracker.

### `POST /api/v1/simulations/cascade`
- **Description**: Executes a discrete-event cascading failure simulation in an isolated sandbox.
- **Request Body**:
  ```json
  {
    "node_id": "pump_01",
    "disruption_type": "NODE_FAILURE",
    "max_steps": 10
  }
  ```
- **Response**: Simulation timeline, blast radius, affected nodes, and unserved demand.

### `POST /api/v1/interventions/evaluate`
- **Description**: Evaluates candidate recovery actions using the deterministic decision engine and the 5-role agentic AI ensemble.
- **Request Body**:
  ```json
  {
    "incident_id": "inc_001",
    "root_cause_node": "pump_01",
    "severity": "HIGH",
    "use_agentic_ai": true
  }
  ```

### `POST /api/v1/simulator/control`
- **Description**: Dynamically updates the in-process sensor fleet degradation parameters (packet loss 0–40%, delay ms, noise level).

### `WebSocket /ws/telemetry`
- **Description**: Real-time bidirectional streaming WebSocket pushing live telemetry updates and twin state events directly to the frontend command center.
