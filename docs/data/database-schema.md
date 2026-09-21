# Data Specification: Database Schema & TimescaleDB Strategy

NEXUS utilizes a hybrid storage model: relational schemas for assets, state snapshots, anomalies, and experiments alongside partitioned TimescaleDB hypertables for time-series telemetry.

---

## Entity-Relationship Overview

```mermaid
erDiagram
    devices ||--o{ telemetry : "generates"
    incidents ||--o{ interventions : "triggers"

    devices {
        string id PK
        string device_type
        string status
        float latitude
        float longitude
        datetime registered_at
    }

    telemetry {
        int id PK
        string device_id FK
        datetime timestamp PK
        bigint sequence_number
        string trace_id
        float pressure_psi
        float flow_rate_gpm
        float temperature_c
        float vibration_rms
        float power_kw
        float battery_pct
        boolean reconstructed
        float confidence
    }

    state_snapshots {
        int id PK
        datetime timestamp
        string node_id
        string operational_state
        string state_source
        float confidence
        float divergence_score
    }

    anomalies {
        int id PK
        datetime timestamp
        string device_id
        string anomaly_type
        string severity
        float score
        string detector
    }

    missing_events {
        int id PK
        datetime timestamp
        string device_id
        string expected_transition
        string observed_transition
        float unexplained_latency_ms
        float confidence
    }

    incidents {
        string id PK
        datetime timestamp
        string title
        string root_cause_node
        string severity
        string status
    }

    interventions {
        string id PK
        string incident_id FK
        datetime timestamp
        string proposed_by
        string action_name
        float simulated_recovery_time_sec
        boolean constraints_passed
    }

    experiments {
        string id PK
        string name
        datetime timestamp
        int random_seed
        float loss_rate
        int delay_ms
        string noise_level
    }
```

---

## Why Not Store Everything in One Table?
1. **Separation of Concerns**: Device inventory and topology metadata are rarely updated (low-velocity relational data), whereas telemetry arrives at thousands of events per second (high-velocity time-series).
2. **Hypertable Partitioning**: TimescaleDB optimizes tables partitioned strictly on `(timestamp, id)`. Placing non-time-series incident management inside the hypertable would bloat chunk index overhead.
3. **Auditability**: Isolating `state_snapshots`, `anomalies`, `missing_events`, and `interventions` allows independent historical auditing of decisions versus physical measurements.
