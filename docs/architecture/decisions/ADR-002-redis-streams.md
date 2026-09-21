# ADR-002: Selection of Redis Streams for Ingestion Decoupling

## Context
The gateway accepts thousands of sensor readings per second. Directly writing each event synchronously to PostgreSQL/TimescaleDB introduces connection pool contention and write latency spikes under burst conditions. We need an asynchronous log-based event streaming broker.

## Alternatives Considered
1. **Apache Kafka**: Industrial grade event streaming platform.
2. **RabbitMQ**: AMQP message broker with queue semantics.
3. **Redis Streams**: In-memory log data structure with consumer groups.

## Decision
We selected **Redis Streams**.

## Rationale
- **Sub-millisecond Ingestion Latency**: Append operations (`XADD`) execute in microseconds, allowing the gateway to accept traffic at wire speed.
- **Consumer Group Semantics**: Provides offset management, explicit acknowledgments (`XACK`), pending message reclamation (`XPENDING`), and dead-letter queues.
- **Lightweight Footprint**: Unlike Kafka (which requires ZooKeeper/KRaft and heavy JVM memory), Redis runs with minimal RAM and starts instantaneously in Docker Compose or local setups.

## Trade-Offs
- In-memory data requires periodic disk persistence (`appendonly yes`).
- Bounded memory requires capping stream length via approximate trimming (`MAXLEN ~ 100000`).
