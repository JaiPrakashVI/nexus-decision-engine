# NEXUS Deployment Guide

This document explains the production and containerized deployment architecture for NEXUS.

---

## Containerized Deployment with Docker Compose

NEXUS provides a multi-container orchestration definition in `docker-compose.yml`:

```
nexus-timescaledb    (Port 5432)  - PostgreSQL + TimescaleDB time-series storage
nexus-redis          (Port 6379)  - In-memory event stream broker
nexus-gateway        (Port 8443)  - mTLS HTTPS ingestion gateway
nexus-consumer       (Background) - Redis stream worker & TimescaleDB persistence
nexus-twin-api       (Port 8000)  - Digital twin engine & WebSocket server
nexus-dashboard      (Port 3000)  - Nginx serving React command center SPA
```

### Launching the Stack

```bash
# 1. Generate mTLS development certificates
python scripts/generate_certs.py

# 2. Build and launch all services in background
docker compose up --build -d

# 3. View live aggregated service logs
docker compose logs -f
```

### Stopping the Stack
```bash
docker compose down
```

---

## Health Checks & Startup Order
- `nexus-timescaledb`: Validated using `pg_isready -U nexus_user -d nexus_db`.
- `nexus-redis`: Validated using `redis-cli ping`.
- The Gateway, Consumer, and Twin API wait for healthy database and stream services before accepting traffic.

---

## Persistent Named Volumes
- `pgdata`: Persists PostgreSQL/TimescaleDB data files across container rebuilds.
- `redisdata`: Persists Redis append-only log files across restarts.
