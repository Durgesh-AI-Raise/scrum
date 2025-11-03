# Review Ingestion Architecture

## Overview
The Review Ingestion Pipeline is designed to automatically ingest new product reviews, ensuring a comprehensive dataset for abuse detection. It leverages an event-driven, serverless architecture on AWS for scalability, reliability, and cost-efficiency.

## Architecture Diagram (Conceptual)

```mermaid
graph TD
    A[Review Source (Simulated/Scraper)] --> B[Kinesis Data Stream: Raw Reviews];
    B --> C[AWS S3: Raw Data Landing Zone (s3://review-data-lake/raw/)]
    B --> D[AWS Lambda: Review Parser & Validator];
    D --> E[Kinesis Data Stream: Validated Reviews];
    E --> F[AWS S3: Curated Data (s3://review-data-lake/curated/)]
    E --> G[AWS Redshift/Snowflake (Future)];
    F --> H[AWS Athena/Glue Catalog];
```

## Components

1.  **Review Source (Simulated/Scraper):**
    *   **Purpose:** Originates the raw review data. For the MVP, this will be a simulated producer or a simple scraper.
    *   **Technology:** Python script generating mock data or polling a public review source (for simulation purposes).

2.  **Kinesis Data Stream: Raw Reviews:**
    *   **Purpose:** Acts as the primary ingestion point, capturing all raw review events in real-time.
    *   **Technology:** AWS Kinesis Data Streams.
    *   **Data Format:** Raw JSON.

3.  **AWS S3: Raw Data Landing Zone:**
    *   **Purpose:** Durable storage for all raw, unprocessed review data. Serves as a reliable backup and source for reprocessing if needed.
    *   **Technology:** AWS S3.
    *   **Path Structure:** `s3://review-data-lake/raw/year=YYYY/month=MM/day=DD/hour=HH/reviews_UUID.json`

4.  **AWS Lambda: Review Parser & Validator:**
    *   **Purpose:** Consumes messages from the 'Raw Reviews' Kinesis stream, performs basic data validation (e.g., checking for required fields, data types) and parsing (e.g., extracting key fields).
    *   **Technology:** AWS Lambda (Python runtime).
    *   **Trigger:** Kinesis 'Raw Reviews' stream.

5.  **Kinesis Data Stream: Validated Reviews:**
    *   **Purpose:** Streams validated and parsed review data, ready for further processing or storage in a more structured format.
    *   **Technology:** AWS Kinesis Data Streams.
    *   **Data Format:** JSON (validated and parsed structure).

6.  **AWS S3: Curated Data:**
    *   **Purpose:** Stores validated and parsed reviews in an optimized format (e.g., Parquet) for analytical queries, directly usable by services like Athena.
    *   **Technology:** AWS S3.
    *   **Path Structure:** `s3://review-data-lake/curated/year=YYYY/month=MM/day=DD/reviews_UUID.parquet`

7.  **AWS Redshift/Snowflake (Future Consideration):**
    *   **Purpose:** Potential future integration for a dedicated data warehouse for more complex analytics and reporting.

8.  **AWS Athena/Glue Catalog:**
    *   **Purpose:** Enables ad-hoc querying of data stored in S3 (both raw and curated zones) using standard SQL, leveraging Glue Catalog for metadata.

## Data Models

### Raw Review Data Model (JSON)
This is the initial schema expected from the review source.
```json
{
  "review_id": "STRING",         // Unique identifier for the review
  "product_id": "STRING",        // Identifier for the product reviewed
  "reviewer_id": "STRING",       // Identifier for the reviewer
  ""stars": "INTEGER",          // Star rating (e.g., 1-5)
  "review_title": "STRING",      // Title of the review
  "review_text": "STRING",       // Full text of the review
  "review_date": "ISO_DATE_STRING", // Date of the review (e.g., "YYYY-MM-DD")
  "country": "STRING",           // Country where the review was posted
  "language": "STRING",          // Language of the review (e.g., "en")
  "source_url": "STRING",        // URL where the review was found
  ""extracted_at": "ISO_DATE_STRING_TIMESTAMP" // Timestamp of when the review was ingested
}
```

### Validated/Parsed Review Data Model (JSON/Parquet Schema)
This schema represents the data after passing through the parsing and validation Lambda. Additional fields for validation status can be added.
```json
{
  "review_id": "STRING",
  "product_id": "STRING",
  "reviewer_id": "STRING",
  "stars": "INTEGER",
  "review_title": "STRING",
  "review_text": "STRING",
  "review_date": "DATE",         // Converted to proper date type
  "country": "STRING",
  "language": "STRING",
  "source_url": "STRING",
  "extracted_at": "TIMESTAMP",   // Converted to proper timestamp type
  "is_valid": "BOOLEAN",         // Flag indicating if basic validation passed
  "validation_errors": "ARRAY<STRING>" // List of validation errors, if any
}
```
