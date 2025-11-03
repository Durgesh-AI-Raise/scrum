# User Story 2 (US2): Store historical review data securely.

### Implementation Plan

The system will include a dedicated **Storage Service** (microservice) responsible for securely persisting all ingested review data and associated metadata. This service will:
1.  **Consume:** Subscribe to the `review-ingestion-stream` from the message queue to receive validated review data in real-time.
2.  **Persist:** Store the review data in a chosen secure database or data lake solution, ensuring data integrity and durability.
3.  **Index:** Create appropriate indexes to facilitate efficient retrieval of reviews for analysis and dashboard display.
4.  **Manage:** Implement data retention and access control policies to comply with security and regulatory requirements.

### Data Models

1.  **ReviewData (Persistent Model):** This will be the schema for the data stored in the database, closely mirroring the `ValidatedReviewData` from US1, with added internal fields for tracking and management.

    ```json
    {
        "id": "UUID",                   // Internal unique identifier (auto-generated)
        "reviewId": "string",           // Unique identifier for the review from Amazon
        "reviewerId": "string",         // Identifier for the reviewer
        "productASIN": "string",        // Amazon Standard Identification Number
        "timestamp": "datetime",        // Timestamp of the review (UTC)
        "ipAddress": "string",          // IP address of the reviewer (hashed/anonymized)
        "reviewText": "string",         // Full text content of the review
        "rating": "integer",            // Star rating (1-5)
        "reviewTitle": "string/null",   // Title of the review (optional)
        "source": "string",             // Source of the review, e.g., "amazon"
        "ingestionTimestamp": "datetime", // When the review was ingested into the system
        "status": "string",             // e.g., "pending", "abusive", "legitimate", "needs_info" (default: "pending")
        "flaggingReasons": "array<string>", // Reasons for being flagged (from US3)
        "lastUpdated": "datetime"       // Timestamp of the last update to this record
    }
    ```

### Architecture

```
[Message Queue] (e.g., Kafka / Amazon Kinesis)
        |\
        | \
        |  V
        | [Storage Service] -- (Data Persistence, Indexing, Policy Enforcement)
        |    |\
        |    | \
        |    |  V
        |    | [Secure Database / Data Lake] (e.g., PostgreSQL, MongoDB, Amazon S3 + Redshift/Athena)
        |    V
        | (To Detection Service, Dashboard API)
```

**Components:**
*   **Message Queue:** Continues to serve as the real-time data conduit.
*   **Storage Service:** A microservice responsible for consuming messages from the queue and writing them to the chosen storage solution.
*   **Secure Database / Data Lake:** The chosen persistence layer.

### Assumptions and Technical Decisions

*   **Assumption (T2.1):** The volume of historical data will be substantial, requiring a scalable and cost-effective storage solution suitable for both transactional updates and analytical queries. For this sprint, a SQL database (e.g., PostgreSQL) will be used for simpler transactional access and a data lake (e.g., S3 + Athena/Redshift) will be considered for long-term archival and complex analytical queries if needed. Starting with PostgreSQL for MVP.
*   **Assumption (T2.2):** The data schema will evolve over time, necessitating a flexible design or robust migration strategy.
*   **Technical Decision (T2.1):** For MVP, **PostgreSQL** will be used as the primary secure database. It offers robust ACID properties, strong data integrity, and good support for JSONB (for flexible metadata storage) if needed. This allows for straightforward relational querying. For long-term archiving and analytics, an S3-based data lake with a querying engine like AWS Athena or Redshift Spectrum could be integrated in future sprints.
*   **Technical Decision (T2.3):** The data persistence layer will use an ORM (e.g., SQLAlchemy for Python) to interact with PostgreSQL, providing an abstraction over raw SQL and simplifying database operations. Bulk insertion mechanisms will be employed for high throughput.
*   **Technical Decision (T2.4):** Data retention policies will initially be configured at the database level (e.g., `pg_partman` for partitioning and archiving) and through application-level logic for soft deletes or data aging. Access control will be handled via database roles and IAM policies for cloud-hosted solutions.
*   **Technical Decision (T2.5):** Essential indexes will be created on `reviewId`, `reviewerId`, `productASIN`, and `timestamp` to optimize query performance for common access patterns (e.g., retrieving reviews by reviewer, product, or time range).
*   **Technical Decision (T2.6):** Unit tests will cover ORM models, repository methods (CRUD operations), and data transformation logic. Integration tests will verify end-to-end data flow from message consumption to successful database persistence and retrieval.

### Code Snippets / Pseudocode

#### T2.2: Design data schema for historical reviews and metadata (PostgreSQL DDL)

```sql
-- Schema for storing historical review data
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Internal unique identifier
    review_id VARCHAR(255) NOT NULL UNIQUE,       -- Unique identifier from Amazon
    reviewer_id VARCHAR(255) NOT NULL,            -- Reviewer identifier
    product_asin VARCHAR(255) NOT NULL,           -- Product ASIN
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,  -- Review timestamp
    ip_address VARCHAR(255) NOT NULL,             -- Hashed/Anonymized IP address
    review_text TEXT NOT NULL,                    -- Full review text
    rating INTEGER,                               -- Star rating (1-5)
    review_title VARCHAR(512),
    source VARCHAR(50) NOT NULL DEFAULT 'amazon', -- Source platform
    ingestion_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(), -- When it entered our system
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- Current status (e.g., pending, abusive)
    flagging_reasons JSONB DEFAULT '[]'::jsonb,   -- Array of flagging reasons from US3
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW() -- Last update timestamp
);

-- Indexes for efficient retrieval
CREATE INDEX idx_reviews_reviewer_id ON reviews (reviewer_id);
CREATE INDEX idx_reviews_product_asin ON reviews (product_asin);
CREATE INDEX idx_reviews_timestamp ON reviews (timestamp DESC);
CREATE INDEX idx_reviews_status ON reviews (status);
```

#### T2.3: Implement data persistence layer for ingested reviews (Python Pseudocode with SQLAlchemy)

```python
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, UUID, func, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timezone
import uuid
import json

# Define the Base for declarative models
Base = declarative_base()

# Define the Review model
class Review(Base):
    __tablename__ = 'reviews'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(String(255), unique=True, nullable=False)
    reviewer_id = Column(String(255), nullable=False)
    product_asin = Column(String(255), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(255), nullable=False)
    review_text = Column(Text, nullable=False)
    rating = Column(Integer)
    review_title = Column(String(512))
    source = Column(String(50), nullable=False, default='amazon')
    ingestion_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    status = Column(String(50), nullable=False, default='pending')
    flagging_reasons = Column(JSON, default=[]) # Use JSON for PostgreSQL JSONB type
    last_updated = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Review(review_id='{self.review_id}', reviewer_id='{self.reviewer_id}')>"

# Database connection setup (replace with your actual DB connection string)
DATABASE_URL = "postgresql+psycopg2://user:password@host:port/dbname"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Function to create tables (run once, or use migrations)
def create_db_tables():
    Base.metadata.create_all(engine)
    print("Database tables created or already exist.")

# Function to persist a single validated review
def persist_review(validated_review_data: dict) -> Review | None:
    session = Session()
    try:
        # Check if review_id already exists to prevent duplicates (though UNIQUE constraint handles this)
        existing_review = session.query(Review).filter_by(review_id=validated_review_data["reviewId"]).first()
        if existing_review:
            print(f"Review with ID {validated_review_data['reviewId']} already exists. Skipping.")
            return existing_review

        new_review = Review(
            review_id=validated_review_data["reviewId"],
            reviewer_id=validated_review_data["reviewerId"],
            product_asin=validated_review_data["productASIN"],
            timestamp=validated_review_data["timestamp"],
            ip_address=validated_review_data["ipAddress"],
            review_text=validated_review_data["reviewText"],
            rating=validated_review_data.get("rating"),
            review_title=validated_review_data.get("reviewTitle"),
            source=validated_review_data.get("source", "amazon"),
            # status and flagging_reasons will be default for initial ingestion
        )
        session.add(new_review)
        session.commit()
        print(f"Successfully persisted review: {new_review.review_id}")
        return new_review
    except Exception as e:
        session.rollback()
        print(f"Error persisting review {validated_review_data.get('reviewId', 'N/A')}: {e}")
        return None
    finally:
        session.close()

# Example: Consume from Kafka and persist
# from kafka import KafkaConsumer
#
# def run_storage_service():
#     create_db_tables() # Ensure tables exist
#     consumer = KafkaConsumer(
#         'review-ingestion-stream',
#         bootstrap_servers=['kafka-broker-1:9092'],
#         auto_offset_reset='earliest',
#         enable_auto_commit=True,
#         group_id='storage-service-group',
#         value_deserializer=lambda x: json.loads(x.decode('utf-8'))
#     )
#
#     for message in consumer:
#         validated_review = message.value
#         # Ensure datetime objects are correctly parsed if they were serialized as strings
#         if isinstance(validated_review.get('timestamp'), str):
#             validated_review['timestamp'] = datetime.fromisoformat(validated_review['timestamp'].replace('Z', '+00:00'))
#         
#         persist_review(validated_review)
#         print(f"Consumed and processed message: {validated_review.get('reviewId')}")

# if __name__ == '__main__':
#     # For local testing of table creation/persistence
#     # create_db_tables()
#     # sample_data = {
#     #     "reviewId": "R12345", "reviewerId": "U67890", "productASIN": "B012345678",
#     #     "timestamp": datetime.now(timezone.utc), "ipAddress": "192.168.1.1",
#     #     "reviewText": "This is a great product!", "rating": 5, "reviewTitle": "Excellent", "source": "amazon"
#     # }
#     # persist_review(sample_data)
#     # run_storage_service()
```

#### T2.4: Configure data retention and access control policies (Conceptual)

*   **Data Retention:**
    *   **PostgreSQL:**
        *   Implement **table partitioning** by `ingestion_timestamp` to manage large datasets. Older partitions can be archived or deleted periodically.
        *   Utilize a tool like `pg_partman` for automated partitioning, archiving, and retention management.
        *   Define application-level logic for "soft deletes" (marking records as inactive instead of immediate deletion) if legal/compliance requires a longer retention period before physical deletion.
    *   **Cloud (e.g., AWS):**
        *   For S3 data lakes: Configure **S3 Lifecycle policies** to transition old data to Glacier or Deep Archive, or automatically delete after a specified period.
        *   For RDS (PostgreSQL): Configure **automated backups** and define backup retention periods.
*   **Access Control:**
    *   **PostgreSQL:**
        *   Create specific database **roles** (e.g., `storage_service_role`, `dashboard_read_role`, `analyst_write_role`).
        *   Grant **least privilege** to each role (e.g., `storage_service_role` has `INSERT` and `UPDATE` on `reviews`, `dashboard_read_role` has `SELECT`).
        *   Implement **row-level security (RLS)** if different analysts should only see specific subsets of data.
    *   **Cloud (e.g., AWS):**
        *   Use **IAM roles and policies** for services accessing the database (e.g., EC2 instances running Storage Service, Lambda functions, Fargate tasks).
        *   Implement **network security** (VPC, security groups, NACLs) to restrict database access to authorized services/IPs only.
        *   Encrypt data at rest (e.g., RDS encryption, S3 encryption) and in transit (SSL/TLS for database connections).

#### T2.5: Develop data indexing for efficient retrieval (PostgreSQL DDL - included in T2.2)

The `CREATE INDEX` statements provided in T2.2 cover the initial indexing strategy.

*   `CREATE INDEX idx_reviews_reviewer_id ON reviews (reviewer_id);`
*   `CREATE INDEX idx_reviews_product_asin ON reviews (product_asin);`
*   `CREATE INDEX idx_reviews_timestamp ON reviews (timestamp DESC);`
*   `CREATE INDEX idx_reviews_status ON reviews (status);`

These indexes will primarily support:
*   Fetching all reviews by a specific reviewer.
*   Fetching all reviews for a specific product.
*   Retrieving reviews within a date range or ordered by recency.
*   Querying reviews based on their abuse `status`.

Further indexes might be considered based on query patterns identified during dashboard development (US4, US5).

#### T2.6: Unit and integration tests for data storage (Conceptual)

*   **Unit Tests:**
    *   Test `Review` model definition (e.g., column types, nullable constraints).
    *   Test `persist_review` function:
        *   Happy path: Successfully saving a new review.
        *   Edge cases: Handling duplicate `review_id` (expecting the function to skip or handle gracefully if UNIQUE constraint is present).
        *   Error cases: Database connection issues (mock database engine errors).
    *   Test any utility functions related to database interaction.
*   **Integration Tests:**
    *   Set up a temporary, isolated PostgreSQL database (e.g., using `testcontainers-python` or an in-memory database if schema allows).
    *   Run `create_db_tables()` against the test database.
    *   Simulate `ValidatedReviewData` coming from the message queue.
    *   Call `persist_review` with test data.
    *   Verify that data is correctly stored in the database by querying directly.
    *   Test basic retrieval queries to ensure indexes are working as expected.
    *   Test for data integrity and constraints (e.g., `UNIQUE` constraint on `review_id`).
    *   Verify that `ingestion_timestamp` and `last_updated` are correctly set.
*   **End-to-End Tests (Future consideration with US1 integration):**
    *   Run the full ingestion pipeline (T1.1-T1.4) and the storage service (T2.1-T2.3) together.
    *   Publish messages to Kafka.
    *   Verify that the Storage Service consumes and correctly persists the messages in the database.
