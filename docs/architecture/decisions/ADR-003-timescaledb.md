# ADR-003: Selection of PostgreSQL + TimescaleDB for Time-Series Storage

## Context
NEXUS must store both relational metadata (devices, incident logs, intervention records, experiments) and high-volume, timestamped physical sensor readings (hundreds of thousands of rows).

## Alternatives Considered
1. **InfluxDB / Prometheus**: Purpose-built time-series databases, but poor support for complex relational joins, foreign key integrity, and ACID transactions.
2. **Standard PostgreSQL**: Excellent relational consistency, but performance degrades on multi-million row time-series tables without manual partitioning.
3. **TimescaleDB on PostgreSQL**: Relational PostgreSQL with automatic time-based hypertable chunk partitioning.

## Decision
We selected **PostgreSQL with TimescaleDB**.

## Rationale
- Unified database: Relational foreign key integrity for devices, incidents, and interventions alongside high-performance time-series hypertables for sensor telemetry.
- Standard SQL interface and full SQLAlchemy 2.0 / `asyncpg` async driver compatibility.
- Seamless fallback: In lightweight local developer environments where Docker is not yet running, the system transparently falls back to `aiosqlite`.

## Trade-Offs
- Requires loading the TimescaleDB extension in PostgreSQL container.
