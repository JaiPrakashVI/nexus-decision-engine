# Troubleshooting Guide

This guide documents common issues, their root causes, and diagnostic resolution steps.

---

## 1. Database Connection Refused (`[WinError 1225]` or `Connection Refused`)
- **Symptom**: Logs show `Could not connect to primary database ([WinError 1225]). Initializing SQLite fallback...`
- **Cause**: PostgreSQL / TimescaleDB is not running on port 5432.
- **Resolution**: This is normal in standalone mode; NEXUS automatically activates its `aiosqlite` engine and initializes `nexus_local.db`. If you intended to run full TimescaleDB, start it via `docker compose up timescaledb -d`.

## 2. Port Already in Use (8000, 8443, or 3000)
- **Symptom**: `ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)`
- **Cause**: A previous uvicorn or node process is still holding the port.
- **Resolution**:
  - Windows: `Get-Process python, node | Stop-Process -Force` or check `netstat -ano | findstr :8000`.
  - Linux/Mac: `lsof -ti:8000 | xargs kill -9`.

## 3. Gateway Returns `401 Unauthorized` or `403 Forbidden`
- **Symptom**: Telemetry ingestion fails with HTTP 401 or 403.
- **Cause**:
  - 401: Client certificate presented was not signed by the NEXUS Root CA (`certs/ca.crt`).
  - 403: The `device_id` is not registered or was revoked in `DeviceRegistry`.
- **Resolution**: Run `python scripts/generate_certs.py` to regenerate valid test certificates, and ensure the sending device ID is registered in `gateway/authentication/device_registry.py`.

## 4. Ollama LLM Warning (`Using deterministic research agent fallback`)
- **Symptom**: Logs show `Ollama unavailable. Using deterministic research agent fallback.`
- **Cause**: The local Ollama daemon is not running or model `llama3.2` is not pulled.
- **Resolution**: This is designed behavior; NEXUS falls back to an offline deterministic research agent with zero downtime. If you wish to use live Ollama, run:
  ```bash
  ollama serve
  ollama pull llama3.2
  ```

## 5. WebSocket Disconnected in Dashboard
- **Symptom**: Top-right status in dashboard displays `OFFLINE` or reconnecting.
- **Cause**: Backend Twin API (`digital_twin.api`) is not running on port 8000.
- **Resolution**: Ensure `python -m digital_twin.api` is running in a terminal.
