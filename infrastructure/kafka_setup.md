## Kafka Streaming Service Setup

**Purpose:** To handle real-time ingestion of Amazon product reviews and associated reviewer data.

**Chosen Technology:** Apache Kafka

**Architecture:**

```
[Mock Amazon Review Source] --> (Produces JSON) --> [Kafka Topic: amazon-reviews-raw] <-- (Consumes JSON) <-- [Review Data Persistence Service]
                                                                                                              <-- [Review Pattern Analysis Service]
```

**Kafka Topic Details:**

*   **Topic Name:** `amazon-reviews-raw`
*   **Purpose:** Ingests raw Amazon product review data and associated reviewer metadata as JSON messages.
*   **Configuration (Example - adjust for production needs):**
    *   `partitions`: 3 (Determined based on expected throughput and consumer parallelism)
    *   `replication-factor`: 2 (Ensures data redundancy and fault tolerance)

**Assumptions & Technical Decisions:**

*   Apache Kafka is the chosen streaming platform.
*   For development, a local Dockerized Kafka instance will be used.
*   For production, a managed Kafka service (e.g., AWS MSK, Confluent Cloud) is recommended.
*   All raw review and reviewer data will initially flow through this single topic.
*   Messages will be in JSON format, adhering to the data models defined in `data_models/review_reviewer_schema.md`.

**Pseudocode / CLI Commands for Topic Creation (Example):**

```bash
# To create the topic:
bin/kafka-topics.sh --create --topic amazon-reviews-raw --bootstrap-server <kafka_broker_address>:9092 --partitions 3 --replication-factor 2

# To describe and verify the topic:
bin/kafka-topics.sh --describe --topic amazon-reviews-raw --bootstrap-server <kafka_broker_address>:9092
```

**Security (Considerations for Production):**

*   **Authentication:** SASL/SSL for client-broker communication.
*   **Authorization:** ACLs (Access Control Lists) to restrict producer/consumer access to topics.
*   **Encryption:** SSL/TLS for data in transit.
