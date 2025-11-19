# MQ Migration Plan: Transition to Production-Grade Messaging

This document outlines the strategic plan for migrating the simulated file-based Message Queue (MQ) to a robust, production-grade messaging solution, addressing the need for enterprise-level scaling and resilience.

## 1. Current State (AT-001)

The current MQ is a file-system simulation using the directory structure: `parallel_orchestration/mq/disk_usage/{new, archive}`.

**Pros:** Simple, effective for proof-of-concept, zero external dependencies.
**Cons:** Not scalable, lacks message persistence guarantees, no true parallel consumption, high I/O overhead.

## 2. Proposed Target State: Solution Selection

The recommended production-grade solution is **Redis Pub/Sub or Redis Streams**.

| Solution | Rationale |
| :--- | :--- |
| **Redis Pub/Sub** | Excellent for simple, fire-and-forget event distribution. Low latency, high throughput. |
| **Redis Streams** | Ideal for guaranteed message delivery, consumer groups, and message history (log-based messaging). |

**Decision:** We will plan for **Redis Streams** as it provides the most robust feature set for an orchestration system requiring guaranteed delivery and consumer group management.

## 3. Migration Roadmap

The migration will be executed in three phases, minimizing disruption to the existing Data and Code Team services.

### Phase 1: Infrastructure and Configuration

1.  **Provision Redis:** Set up a managed Redis instance (or a local Docker container for testing).
2.  **Update `.env`:** Add new configuration variables for Redis connection (e.g., `REDIS_HOST`, `REDIS_PORT`, `REDIS_STREAM_NAME`).
3.  **Install Client:** Add the `redis` Python client to the `setup.py` dependencies.

### Phase 2: Code Refactoring (Parallel Implementation)

1.  **Data Team (Publisher):** Modify `dt_001_resource_reporter.py` to publish the JSON report directly to the Redis Stream instead of writing to the file system. The file-system logic will be retained as a fallback/local development mode.
2.  **Code Team (Subscriber):** Modify `ct_002_data_processor.py` to replace the file-system polling logic (`os.listdir`) with a Redis Stream consumer loop. This will allow for true, non-blocking parallel consumption.

### Phase 3: Validation and Cutover

1.  **Parallel Testing:** Run the file-based system and the Redis-based system concurrently in a staging environment.
2.  **Cutover:** Once validated, remove the file-system logic and rely solely on the Redis Stream for all inter-team communication.

This plan ensures a smooth transition to a highly scalable and resilient messaging backbone, fulfilling the final requirement for production readiness.
