# Amazon.com Review Data Ingestion Pipeline Architecture

## 1. Overview

This document outlines the architectural design for ingesting Amazon.com review data in real-time or near real-time, enabling initial abuse detection capabilities. The primary goal is to provide Trust & Safety Analysts with the most up-to-date information for identifying and mitigating abuse.

## 2. Architecture Components

The pipeline consists of the following key components:

*   **Review Data Source:** The origin of Amazon.com review data.
*   **Ingestion Layer (Apache Kafka):** A distributed streaming platform for high-throughput, fault-tolerant ingestion.
*   **Processing Layer (Apache Flink):** A stream processing framework for real-time data validation, cleansing, transformation, and initial abuse detection logic.
*   **Storage Layer:**
    *   **Data Lake (AWS S3):** For storing raw, immutable review data for historical analysis, reprocessing, and auditing.
    *   **NoSQL Database (AWS DynamoDB):** For storing processed, query-optimized review data, facilitating fast lookups for abuse detection and analytical queries.
*   **Monitoring & Alerting:** Tools for observing pipeline health, performance, and data quality.

## 3. Data Flow

```mermaid
graph TD
    A[Amazon.com Review Source] --> B(Kafka Producer);
    B --> C{Kafka Topic: amazon_reviews_raw};
    C --> D[Flink Processing Job];
    D -- Validated/Cleansed Data --> E{Kafka Topic: amazon_reviews_processed};
    D -- Raw Data Archiving --> F[AWS S3 Data Lake (Raw)];
    E --> G[Flink/Kafka Consumer];
    G --> H[AWS DynamoDB (Processed)];
    H -- Abuse Detection & Analytics --> I[Trust & Safety Analysts];
    D -- Invalid Data --> J{Kafka Topic: amazon_reviews_dead_letter_queue};
```

**Flow Description:**

1.  **Amazon.com Review Source:** New review data is generated (initially simulated, later integrated with actual Amazon.com APIs/feeds).
2.  **Kafka Producer:** A Python application (or similar) fetches review data from the source and publishes it to the `amazon_reviews_raw` Kafka topic.
3.  **Kafka Topic: `amazon_reviews_raw`:** Stores raw, unvalidated review messages.
4.  **Flink Processing Job:**
    *   Consumes messages from `amazon_reviews_raw`.
    *   Performs data validation (e.g., schema checks, data type validation, range checks).
    *   Performs data cleansing (e.g., trimming whitespace, normalizing country codes, handling missing values).
    *   Applies initial transformation (e.g., converting timestamps, renaming fields).
    *   **Raw Data Archiving:** Persists the original raw messages to an AWS S3 Data Lake for long-term storage.
    *   **Invalid Data Handling:** Messages that fail critical validation are sent to `amazon_reviews_dead_letter_queue` for manual inspection and reprocessing.
    *   **Processed Data Output:** Publishes validated and cleansed messages to the `amazon_reviews_processed` Kafka topic.
5.  **Kafka Topic: `amazon_reviews_processed`:** Stores processed, high-quality review messages.
6.  **Flink/Kafka Consumer:** A dedicated consumer (could be another Flink job or a lightweight Kafka consumer) reads from `amazon_reviews_processed`.
7.  **AWS DynamoDB (Processed):** Stores the final processed review data, optimized for low-latency queries by Trust & Safety Analysts.
8.  **Trust & Safety Analysts:** Utilize the data in DynamoDB for real-time abuse detection, investigations, and reporting.

## 4. Data Models

### 4.1. Raw Review Data (JSON/Avro)

This schema represents the data as it's initially ingested from the source.

```json
{
  "review_id": "string",         // Unique identifier for the review
  "product_id": "string",        // Identifier of the product being reviewed
  "user_id": "string",           // Identifier of the user who wrote the review
  "stars": "integer",            // Star rating (e.g., 1 to 5)
  "headline": "string",          // Short summary/title of the review
  "body": "string",              // Full text content of the review
  "timestamp": "long",           // Unix timestamp in milliseconds when the review was posted
  "country": "string",           // Country of the reviewer (e.g., "US", "GB")
  "source": "string"             // Source platform, always "amazon.com" for this sprint
}
```

### 4.2. Processed Review Data (JSON/Avro)

This schema represents the data after validation, cleansing, and initial processing. It's optimized for storage and querying in DynamoDB.

```json
{
  "review_id": "string",                 // Unique identifier for the review (same as raw)
  "product_id": "string",                // Identifier of the product
  "user_id": "string",                   // Identifier of the user
  "rating": "integer",                   // Star rating (1-5), renamed for consistency
  "review_summary": "string",            // Cleaned and validated headline
  "review_text": "string",               // Cleaned and validated body
  "review_timestamp_utc": "string",      // Review timestamp in ISO 8601 UTC format (e.g., "2023-10-26T14:30:00Z")
  "country_code": "string",              // Standardized country code (ISO 3166-1 alpha-2, e.g., "US")
  "source_platform": "string",           // Source platform (e.g., "amazon.com")
  "sentiment_score": "float",            // Calculated sentiment score (e.g., -1.0 to 1.0) - Placeholder for future ML integration
  "abuse_potential_score": "float",      // Score indicating potential for abuse (e.g., 0.0 to 1.0) - Placeholder for future ML integration
  "is_abusive": "boolean",               // Flag indicating if the review is classified as abusive - Placeholder
  "processing_timestamp": "long"         // Unix timestamp in milliseconds when the review was processed by Flink
}
```

## 5. Assumptions and Technical Decisions

*   **Real-time Definition:** "Real-time" is defined as near real-time, with data latency typically within seconds from source to processed storage.
*   **Data Volume:** The architecture is designed to handle high volumes of review data, leveraging the scalability of Kafka and Flink.
*   **Source System Integration:** Initial development uses a simulated Amazon.com review generator. Future work will involve integrating with actual Amazon.com APIs or data feeds.
*   **Data Format & Schema:** JSON is used for initial data transfer due to its flexibility. For future robustness and schema evolution, Avro with a Schema Registry (e.g., Confluent Schema Registry) will be considered.
*   **Cloud Provider:** AWS is chosen for cloud infrastructure (S3, DynamoDB, potentially EC2/EKS for Kafka/Flink).
*   **Idempotency:** Processing components will be designed to handle duplicate messages gracefully, ensuring that reprocessing an event does not lead to incorrect data.
*   **Error Handling (DLQ):** A Dead-Letter Queue (DLQ) Kafka topic (`amazon_reviews_dead_letter_queue`) will be used to capture messages that fail validation or processing, allowing for manual inspection and re-ingestion.
*   **Security:** Data in transit will be encrypted (e.g., SSL/TLS for Kafka). Data at rest will be encrypted (e.g., S3 server-side encryption, DynamoDB encryption at rest). IAM roles and policies will be used for access control.
*   **Monitoring:** Pipeline health, data flow, and processing metrics will be monitored using tools like Prometheus/Grafana or AWS CloudWatch. Alerts will be configured for anomalies.

## 6. Future Considerations

*   **Advanced Abuse Detection:** Integration with machine learning models for more sophisticated sentiment analysis, spam detection, and anomaly detection.
*   **Dynamic Schema Evolution:** Implement Avro and Schema Registry for robust schema management.
*   **Backfilling/Historical Ingestion:** Mechanism to ingest large volumes of historical review data.
*   **Data Quality Reporting:** Automated reports on data quality metrics.
*   **Visualization:** Dashboards for Trust & Safety Analysts to visualize review trends and abuse patterns.
*   **Alerting Integration:** Connect abuse detection findings to alert systems for immediate analyst attention.
