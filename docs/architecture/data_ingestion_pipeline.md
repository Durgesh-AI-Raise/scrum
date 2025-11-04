# ARIS Sprint 1: Data Ingestion Pipeline Architecture Design

## User Story 1: As a Data Engineer, I want the system to continuously ingest all new Amazon reviews in near real-time, along with associated reviewer and product metadata, so that abuse detection can be performed comprehensively and promptly.

### Task: Design the high-level and detailed architecture for the data ingestion pipeline.
*   **GitHub Issue:** `ARIS Sprint 1: Design data ingestion pipeline architecture` (Issue #8445)

---

### 1. Implementation Plan:

*   **High-Level Design:** Identify key components such as data sources (Amazon MWS, internal streams), ingestion mechanisms (streaming services), processing engines (for transformations and enrichments), and storage solutions (data lake, operational databases).
*   **Detailed Design:**
    *   **Source Integration:** Define how to connect to and consume review data from a designated Amazon review stream (e.g., Kafka/Kinesis topic).
    *   **Ingestion Service:** Develop a dedicated microservice or application responsible for consuming data from the streaming source.
    *   **Data Processing:** Outline the steps for parsing raw events, extracting core review data, enriching with reviewer/product metadata (from internal services or pre-existing datasets), and transforming data into a standardized format.
    *   **Storage Strategy:** Determine storage for both raw (e.g., S3 for historical/re-processing) and processed (e.g., PostgreSQL for structured querying, DynamoDB for metadata) data.
    *   **Error Handling & Monitoring:** Integrate with centralized logging and monitoring solutions.

---

### 2. Data Models and Architecture:

*   **Architecture Diagram (Conceptual):**
    ```
    Amazon Review Source (Kafka/Kinesis)
            ↓
    Ingestion Service (Consumer Application)
            ↓ (Raw Review Events)
    Data Transformation & Enrichment Layer
            ↓ (Processed Review + Metadata)
    Data Lake (S3) -- (Raw Data Storage)
            ↓
    Operational Database (PostgreSQL) -- (Structured Reviews)
    NoSQL Database (DynamoDB) -- (Reviewer/Product Metadata)
    ```
*   **Data Models (Proposed Schemas):**
    *   `RawReviewEvent`: The direct JSON/Protobuf payload received from the source.
    *   `ProcessedReview` (PostgreSQL `reviews` table):
        ```sql
        CREATE TABLE reviews (
            review_id VARCHAR(255) PRIMARY KEY,
            review_text TEXT,
            rating INT,
            review_date TIMESTAMP,
            product_id VARCHAR(255) NOT NULL,
            reviewer_id VARCHAR(255) NOT NULL,
            marketplace VARCHAR(50),
            ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processing_status VARCHAR(50) DEFAULT 'processed'
        );
        ```
    *   `ReviewerMetadata` (DynamoDB `reviewer_metadata` table / PostgreSQL `reviewers` table):
        ```sql
        CREATE TABLE reviewers (
            reviewer_id VARCHAR(255) PRIMARY KEY,
            reviewer_name VARCHAR(255),
            reviewer_join_date TIMESTAMP,
            total_reviews INT DEFAULT 0,
            average_rating_given NUMERIC(3, 2),
            -- Add other relevant reviewer history fields
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ```
    *   `ProductMetadata` (DynamoDB `product_metadata` table / PostgreSQL `products` table):
        ```sql
        CREATE TABLE products (
            product_id VARCHAR(255) PRIMARY KEY,
            product_name VARCHAR(255),
            product_category VARCHAR(100),
            brand VARCHAR(100),
            average_rating NUMERIC(3, 2),
            total_reviews INT DEFAULT 0,
            -- Add other relevant product details
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ```

---

### 3. Assumptions and Technical Decisions:

*   **Assumption**: A Kafka or Kinesis topic is the primary source of real-time Amazon review data, already populated with new reviews and basic metadata.
*   **Assumption**: Separate internal services or pre-existing databases are available to provide rich reviewer and product metadata, retrievable via IDs.
*   **Technical Decision**: Utilize cloud-native managed streaming services (e.g., AWS Kinesis, GCP Pub/Sub) for scalability, reliability, and reduced operational overhead.
*   **Technical Decision**: Employ a robust stream processing framework (e.g., Apache Flink, Spark Streaming, or AWS Kinesis Data Analytics) for real-time data transformation and enrichment.
*   **Technical Decision**: PostgreSQL is chosen for the primary structured storage of processed reviews due to its strong ACID properties and flexibility for complex queries, while DynamoDB (or similar NoSQL) can be used for high-throughput metadata lookups if required by scale.
*   **Technical Decision**: Implement a schema validation mechanism at the ingestion point to ensure data quality.

---

### 4. Code Snippets/Pseudocode for Key Components (Conceptual):

```python
# Pseudocode for a generic Review Ingestion Service
class ReviewIngestionService:
    def __init__(self, stream_client, db_client, reviewer_api, product_api):
        self.stream_consumer = stream_client  # e.g., KinesisConsumer, KafkaConsumer
        self.database = db_client            # e.g., PostgreSQLClient
        self.reviewer_service = reviewer_api # API client for reviewer data
        self.product_service = product_api   # API client for product data
        self.logger = get_logger("ReviewIngestionService")

    def run(self):
        self.logger.info("Starting review ingestion service...")
        for record in self.stream_consumer.consume_records():
            try:
                # 1. Parse raw event
                raw_event_data = self._parse_record(record)
                review_data = self._extract_review_core(raw_event_data)

                # 2. Enrich with metadata
                reviewer_metadata = self.reviewer_service.get_reviewer_by_id(review_data['reviewer_id'])
                product_metadata = self.product_service.get_product_by_id(review_data['product_id'])

                # 3. Store processed review and metadata
                self.database.save_review(review_data)
                self.database.save_reviewer_metadata(reviewer_metadata)
                self.database.save_product_metadata(product_metadata)

                self.logger.info(f"Successfully processed review: {review_data['review_id']}")
                self.stream_consumer.commit_offset(record) # Acknowledge processing
            except Exception as e:
                self.logger.error(f"Error processing record: {record}. Details: {e}")
                # Potentially send to a Dead Letter Queue (DLQ) for re-processing or investigation

    def _parse_record(self, record):
        # Logic to deserialize record (e.g., JSON.parse, Protobuf decode)
        print(f"Parsing record: {record.id}")
        return {"id": record.id, "content": record.data} # Placeholder

    def _extract_review_core(self, parsed_data):
        # Logic to extract essential review fields
        print(f"Extracting core review data from: {parsed_data['id']}")
        return {
            "review_id": parsed_data["id"],
            "review_text": "placeholder text",
            "rating": 5,
            "review_date": "2023-10-27T10:00:00Z",
            "product_id": "PROD123",
            "reviewer_id": "REV456"
        }
```