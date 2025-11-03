# Amazon Product Review Abuse Detection System

## Sprint 1: Foundational Data Ingestion, Storage & Initial Abuse Detection

### Sprint Goal
"Establish the foundational data ingestion and storage for Amazon product reviews, and implement initial high-confidence abuse detection with a basic dashboard to provide immediate visibility into clear abuse cases."

---

## 1. Real-time Data Ingestion Pipeline (Data Engineer Tasks)

### 1.1. Architecture Design

The real-time data ingestion pipeline is designed for scalability, fault-tolerance, and immediate access to Amazon product review data.

**Components:**
1.  **Review Source (Simulated):** A Python script (`producer.py`) simulates the stream of new Amazon product reviews.
2.  **Ingestion Service (Kafka Producer):** The `producer.py` script acts as a Kafka producer, publishing raw review data to a Kafka topic.
3.  **Message Queue (Apache Kafka):** Serves as a central nervous system for real-time data streams.
    *   `amazon_reviews_raw`: Topic for unprocessed, incoming review data.
    *   `amazon_reviews_processed`: Topic for reviews that have been successfully parsed and validated.
    *   `amazon_reviews_dlq`: Dead-Letter Queue for reviews that failed parsing or validation.
4.  **Processing Service (Kafka Consumer - Parser & Validator):** A Python script (`consumer_parser.py`) consumes from `amazon_reviews_raw`, performs parsing and schema validation. Valid reviews are forwarded to `amazon_reviews_processed`, invalid ones to `amazon_reviews_dlq`.

**Data Model (Review):**
```json
{
    "reviewId": "string",          // Unique ID for the review
    "productId": "string",         // ID of the product being reviewed
    "userId": "string",            // ID of the user who wrote the review
    "rating": "integer (1-5)",     // Star rating given by the user
    "title": "string",             // Title of the review
    "text": "string",              // Full text content of the review
    "reviewDate": "timestamp",     // Date and time when the review was posted (ISO 8601 format)
    "verifiedPurchase": "boolean", // Indicates if the purchase was verified
    "productCategory": "string",   // Category of the product
    "reviewerAccountAgeDays": "integer" // Age of the reviewer's account in days
}
```

### 1.2. Kafka Setup (Local Development)

To run the ingestion pipeline locally, you will need a running Kafka instance. We recommend using Docker Compose.

1.  **Install Docker & Docker Compose:** If you don't have them, follow the official Docker installation guides.

2.  **Create `docker-compose.yml`:**
    ```yaml
    version: '3'
    services:
      zookeeper:
        image: 'bitnami/zookeeper:latest'
        ports:
          - '2181:2181'
        environment:
          - ALLOW_ANONYMOUS_LOGIN=yes
      kafka:
        image: 'bitnami/kafka:latest'
        ports:
          - '9092:9092'
        environment:
          - KAFKA_BROKER_ID=1
          - KAFKA_LISTENERS=PLAINTEXT://:9092
          - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092
          - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
          - ALLOW_PLAINTEXT_LISTENER=yes
        depends_on:
          - zookeeper
    ```

3.  **Start Kafka and Zookeeper:**
    ```bash
    docker-compose up -d
    ```

4.  **Verify Kafka is running:**
    ```bash
    docker-compose ps
    ```

5.  **Create Kafka Topics:** Once Kafka is running, create the necessary topics. You can exec into the Kafka container to run these commands, or use a tool like `kafka-topics.sh` from your local Kafka installation.

    Assuming you have `kafka-topics.sh` available (e.g., from a local Kafka download in `bin` directory):
    ```bash
    # Create raw reviews topic
    bin/kafka-topics.sh --create --topic amazon_reviews_raw --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

    # Create processed reviews topic
    bin/kafka-topics.sh --create --topic amazon_reviews_processed --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

    # Create dead-letter queue topic
    bin/kafka-topics.sh --create --topic amazon_reviews_dlq --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

    # Describe topics to verify creation
    bin/kafka-topics.sh --describe --topic amazon_reviews_raw --bootstrap-server localhost:9092
    bin/kafka-topics.sh --describe --topic amazon_reviews_processed --bootstrap-server localhost:9092
    bin/kafka-topics.sh --describe --topic amazon_reviews_dlq --bootstrap-server localhost:9092
    ```
