# Data Ingestion Pipeline Architecture (Sprint 1)

## Overview

This document outlines the architecture for ingesting product review data into the Abuse Tracking System for Sprint 1. The focus is on establishing a foundational, real-time (simulated) data flow into persistent storage.

## Architecture Diagram (Conceptual)

```mermaid
graph TD
    A[Simulated Data Source (Python Script)] --> B(Kafka Topic: raw_reviews)
    B --> C{Data Consumer (Python)}
    C --> D[AWS S3 (Raw Data Lake)]
    C --> E[MongoDB (Processed Reviews DB)]
    E --> F[Kafka Topic: processed_reviews] # For downstream rules engine
```

## Components

1.  **Simulated Data Source (Python Script):**
    *   **Purpose:** Emulates real-time review generation by reading from a local JSON file (e.g., a subset of a public Amazon review dataset) or programmatically generating mock review data.
    *   **Technology:** Python script.

2.  **Apache Kafka:**
    *   **Purpose:** A distributed streaming platform used as the central nervous system for real-time data ingestion. It decouples data producers from consumers, provides fault tolerance, and enables high-throughput data streams.
    *   **Topics:**
        *   `raw_reviews`: Stores raw, unvalidated JSON review records directly from the data source.
    *   **Decision:** Chosen for its industry-standard capabilities, scalability, and robust ecosystem.

3.  **Data Consumer (Python):**
    *   **Purpose:** A Python application that subscribes to the `raw_reviews` Kafka topic.
    *   **Functionality:**
        *   Reads raw JSON messages from Kafka.
        *   Performs basic validation (e.g., ensuring required fields are present).
        *   Stores the original raw JSON payload into AWS S3.
        *   Parses the JSON into a structured format and stores it into MongoDB.
        *   (Future: Publishes a cleaned/enriched version to `processed_reviews` Kafka topic for the rules engine).
    *   **Technology:** Python with `confluent-kafka-python`, `boto3` (for S3), `pymongo` (for MongoDB).

4.  **AWS S3 (Raw Data Lake):**
    *   **Purpose:** Object storage for storing raw, immutable review data as a data lake. This serves as a source of truth for all ingested data, enabling re-processing if needed.
    *   **Data Format:** Raw JSON files.
    *   **Partitioning (Example):** `s3://review-abuse-tracking/raw-reviews/YYYY/MM/DD/review_id.json`
    *   **Decision:** Highly scalable, durable, and cost-effective for large volumes of unstructured data.

5.  **MongoDB (Processed Reviews Database):**
    *   **Purpose:** A NoSQL document database used to store processed, structured review data that is easily queryable by the rules engine and the dashboard.
    *   **Collections:**
        *   `reviews`: Stores the structured review data, potentially with added metadata like `ingestion_timestamp`.
    *   **Decision:** Chosen for its flexible schema (ideal for semi-structured review data) and ability to handle high read/write throughput.

## Data Flow (Sprint 1)

1.  A Python script generates or replays review records in JSON format.
2.  These JSON records are pushed to the `raw_reviews` Kafka topic.
3.  A Python consumer application reads from `raw_reviews`.
4.  The consumer saves the raw JSON to S3 and also inserts the structured review data into the `reviews` collection in MongoDB.
5.  (Implicit for future steps) The rules engine will then consume from a `processed_reviews` Kafka topic (which could be the output of a slightly modified consumer in future sprints, or directly from MongoDB for Sprint 1 MVP of rules engine).