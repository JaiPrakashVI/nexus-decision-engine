# ADR-006: Mutual TLS (mTLS) Cryptographic Device Authentication

## Context
In cyber-physical infrastructure networks, edge sensor devices operate over potentially untrusted transmission channels. Ingested telemetry must be authenticated cryptographically to prevent rogue sensor injection and spoofing attacks.

## Alternatives Considered
1. **Shared Secret API Keys**: Vulnerable to credential theft, hardcoding, and lack of individual device revocation.
2. **Standard TLS with JWT Bearer Tokens**: Requires separate token refresh infrastructure, tokens can be stolen, does not authenticate the underlying transport connection.
3. **Mutual TLS (mTLS) with X.509 Certificates**: The transport layer validates both the server's certificate AND the client's device certificate signed by a dedicated Root Certificate Authority (CA).

## Decision
We implemented **mTLS using dedicated X.509 certificates generated via Python `cryptography`**:
- A private Root CA (`certs/ca.crt`) signs all valid sensor certificates.
- The Gateway validates the certificate signature, checks expiration dates, and extracts the Common Name (`device_id`).
- The device ID is verified against the `DeviceRegistry`.
- Rogue certificates signed by an untrusted CA are rejected at the transport layer with `401 Unauthorized`.
