# NEXUS Security Architecture & Threat Model

This document outlines the security controls, cryptographic protocols, and threat boundaries implemented in NEXUS.

---

## 1. Threat Model & Principles
In critical infrastructure (water and power distribution networks), edge telemetry lines are inherently untrusted. The threat model accounts for:
- **Rogue Transmitters**: Malicious or unauthorized sensors attempting to inject fabricated telemetry.
- **Man-in-the-Middle (MitM) & Tampering**: Modification of sensor measurements in transit.
- **Replay Attacks**: Interception and re-transmission of valid historical packets to spoof stale operational states.
- **Denial of Service (DoS)**: Flooding the ingestion gateway with telemetry packets.
- **Generative AI Hallucinations / Prompt Injections**: Compromised or corrupted LLM outputs attempting to actuate invalid or dangerous physical actions.

---

## 2. Security Controls Implemented

### Mutual TLS (mTLS) Cryptographic Device Authentication
- All edge sensor communication terminates over TLS 1.3 with mutual authentication.
- Sensors present an X.509 client certificate signed by the dedicated private NEXUS Root CA (`certs/ca.crt`).
- The Gateway extracts the Common Name (`device_id`) and verifies the device is authorized and active in `DeviceRegistry`.
- Client certificates signed by an untrusted or rogue CA are immediately rejected at the transport layer with `401 Unauthorized`.

### Replay & Timestamp Drift Protection
- Every telemetry packet requires a unique UUID4 `trace_id` and a monotonically increasing `sequence_number`.
- Ingestion enforces strict temporal drift bounds:
  - Timestamp must not be more than 300 seconds in the past.
  - Timestamp must not be more than 60 seconds in the future.
- Duplicate trace IDs are rejected with `400 Bad Request`.

### Token-Bucket Rate Limiting
- Configurable token-bucket rate limiting per device (up to 5,000 req/s) protects the ingestion gateway from volume flooding.

### Isolation of AI from Infrastructure Actuation
- The local LLM operates strictly in an advisory role.
- Generative models have zero network or execution access to physical actuators or switching relays.
- Candidate actions are formulated by the Deterministic Decision Engine and must be simulated in an isolated sandbox before presentation to human operators.

### Secrets Management
- Private keys (`*.key`), certificates (`*.crt`), and database passwords are never committed to version control.
- Configuration is loaded via `.env` and typed Pydantic Settings.
