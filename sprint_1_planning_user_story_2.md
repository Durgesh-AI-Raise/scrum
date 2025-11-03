# Sprint 1 Planning: User Story 2 - Secure Data Storage for Essential Review Metadata

**Sprint Goal:** To establish the foundational components of the Amazon Review Abuse Tracking System by implementing secure data storage for essential review metadata.

## User Story 2: As a system, I want to store essential review metadata (reviewer ID, product ASIN, timestamp, review text, rating, helpfulness votes), so that comprehensive analysis can be performed.

---

### Task 2.1: Design database schema for review metadata

*   **Implementation Plan:**
    1.  **Identify Core Entities:** The core entity is `Review`. Other potential entities might include `Product` and `Reviewer` (though initially, we might denormalize to simplify).
    2.  **Define Attributes:** For `Review`, include `review_id`, `product_asin`, `reviewer_id`, `review_timestamp`, `review_text`, `rating`, `helpfulness_votes`, and add fields for system metadata like `ingestion_timestamp`.
    3.  **Choose Database Type:** Given the need for comprehensive analysis, potential for complex queries, and ACID properties, a relational database (like PostgreSQL) is a strong candidate. For very high volume or unstructured data, NoSQL might be considered, but relational offers better immediate query capabilities for structured metadata.
    4.  **Draft Schema (SQL):** Create `CREATE TABLE` statements for the chosen database, defining data types, primary keys, and indices.
    5.  **Consider Normalization/Denormalization:** Initially, a somewhat denormalized schema might be simpler, but consider if `Product` or `Reviewer` should become separate tables later for scalability or data integrity.

*   **Data Models and Architecture:**
    *   **Architecture:** The database will be a central persistent store, consumed by downstream analytical and moderation services.
    *   **Data Model (SQL Schema - conceptual):**
        ```sql
        -- Table: reviews
        CREATE TABLE reviews (
            review_id VARCHAR(255) PRIMARY KEY, -- Unique identifier for the review
            product_asin VARCHAR(10) NOT NULL, -- Amazon Standard Identification Number
            reviewer_id VARCHAR(255) NOT NULL, -- Unique identifier for the reviewer
            review_timestamp TIMESTAMP WITH TIME ZONE NOT NULL, -- When the review was published by the user
            ingestion_timestamp TIMESTAMP WITH TIME ZONE NOT NULL, -- When the review was ingested by our system
            review_text TEXT, -- Full text of the review
            review_title VARCHAR(500), -- Title of the review (if available)
            rating NUMERIC(2,1) NOT NULL, -- Rating given (e.g., 4.5)
            helpfulness_votes INTEGER DEFAULT 0, -- Number of helpfulness votes
            is_flagged BOOLEAN DEFAULT FALSE, -- To indicate if it's flagged by detection rules
            flagging_reason JSONB, -- Stores an array of reasons/rules that flagged it
            moderation_status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, ABUSIVE, LEGITIMATE
            is_public BOOLEAN DEFAULT TRUE, -- Can be set to FALSE to remove from public view
            CONSTRAINT chk_rating CHECK (rating >= 1.0 AND rating <= 5.0)
        );

        -- Indexes for performance
        CREATE INDEX idx_reviews_product_asin ON reviews (product_asin);
        CREATE INDEX idx_reviews_reviewer_id ON reviews (reviewer_id);
        CREATE INDEX idx_reviews_review_timestamp ON reviews (review_timestamp);
        CREATE INDEX idx_reviews_is_flagged_status ON reviews (is_flagged, moderation_status);
        ```
    *   **Data Model (Python Representation - for ORM/application layer):**
        ```python
        from datetime import datetime
        from typing import List, Optional, Dict

        class ReviewMetadata:
            review_id: str
            product_asin: str
            reviewer_id: str
            review_timestamp: datetime
            ingestion_timestamp: datetime
            review_text: Optional[str]
            review_title: Optional[str]
            rating: float
            helpfulness_votes: int = 0
            is_flagged: bool = False
            flagging_reason: Optional[List[Dict]] = None # Example: [{'rule_id': 'DUP_TEXT', 'severity': 'HIGH'}]
            moderation_status: str = 'PENDING' # ENUM: PENDING, ABUSIVE, LEGITIMATE
            is_public: bool = True
        ```

*   **Assumptions and Technical Decisions:**
    *   **Assumption:** PostgreSQL is chosen as the relational database for its robustness, open-source nature, and extensive feature set.
    *   **Technical Decision:** Use a single `reviews` table initially for simplicity, with fields for `product_asin` and `reviewer_id` directly within it. Further normalization (separate `products` or `reviewers` tables) can be done in future sprints if needed for complex entities or large-scale master data management.
    *   **Technical Decision:** Store `flagging_reason` as `JSONB` to allow for flexible storage of multiple rule-triggered reasons without needing a separate table initially.
    *   **Technical Decision:** `review_timestamp` stores the original review publication time, while `ingestion_timestamp` stores when our system first captured it.

*   **Code Snippets/Pseudocode:**
    *   SQL `CREATE TABLE` and `CREATE INDEX` statements as shown above.

---

### Task 2.2: Implement data storage mechanism

*   **Implementation Plan:**
    1.  **Database Setup:** Provision a PostgreSQL instance (local, cloud, or managed service).
    2.  **Schema Application:** Execute the `CREATE TABLE` and `CREATE INDEX` SQL scripts designed in Task 2.1 to set up the database schema.
    3.  **ORM/Database Client Setup:** In the data processing service (consumer of the message queue), set up a database connection and an Object-Relational Mapper (ORM) like SQLAlchemy (Python) or a direct database client library.
    4.  **Data Persistence Logic:** Develop functions to insert new `ReviewMetadata` objects into the database. Handle potential duplicates based on `review_id` (e.g., UPSERT or ignore if exists).

*   **Data Models and Architecture:**
    *   **Architecture:** The `Processing Service` (consumer from Task 1.2) will now contain the data persistence logic, connecting to the PostgreSQL database.
    *   No new specific data models beyond those from Task 2.1. The `ReviewMetadata` class will be mapped to the `reviews` table.

*   **Assumptions and Technical Decisions:**
    *   **Assumption:** PostgreSQL database instance is accessible from the ingestion/processing services.
    *   **Technical Decision:** Use SQLAlchemy Core for direct SQL execution or SQLAlchemy ORM for more abstract object-relational mapping in Python, as it provides a robust and flexible way to interact with the database.
    *   **Technical Decision:** Implement an UPSERT (Update or Insert) strategy to handle cases where a review with the same `review_id` might be ingested again due to retries or eventual consistency, ensuring data idempotency.

*   **Code Snippets/Pseudocode:**
    ```python
    from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, Integer, Boolean, JSON, inspect
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.orm import sessionmaker, declarative_base
    from datetime import datetime
    import os

    # Database connection string (replace with actual credentials/environment variables)
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host:5432/dbname")

    Base = declarative_base()

    class Review(Base):
        __tablename__ = 'reviews'
        review_id = Column(String(255), primary_key=True)
        product_asin = Column(String(10), nullable=False, index=True)
        reviewer_id = Column(String(255), nullable=False, index=True)
        review_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
        ingestion_timestamp = Column(DateTime(timezone=True), nullable=False)
        review_text = Column(Text)
        review_title = Column(String(500))
        rating = Column(Float, nullable=False)
        helpfulness_votes = Column(Integer, default=0)
        is_flagged = Column(Boolean, default=False)
        flagging_reason = Column(JSONB) # Stores as JSONB in PostgreSQL
        moderation_status = Column(String(50), default='PENDING') # ENUM: PENDING, ABUSIVE, LEGITIMATE
        is_public = Column(Boolean, default=True)

        def __repr__(self):
            return f"<Review(review_id='{self.review_id}', product_asin='{self.product_asin}')>"

    # Database engine and session setup
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)

    def setup_database():
        # Create tables if they don't exist (DANGER: In production, use migrations)
        Base.metadata.create_all(engine)
        print("Database tables checked/created.")

    def insert_or_update_review(review_data: dict):
        session = Session()
        try:
            # Check if review already exists
            existing_review = session.query(Review).filter_by(review_id=review_data['review_id']).first()

            if existing_review:
                # Update existing review (e.g., if new fields are available or for idempotency)
                print(f"Updating existing review: {review_data['review_id']}")
                for key, value in review_data.items():
                    setattr(existing_review, key, value)
            else:
                # Insert new review
                new_review = Review(**review_data)
                session.add(new_review)
                print(f"Inserted new review: {review_data['review_id']}")

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error inserting/updating review {review_data.get('review_id')}: {e}")
            raise
        finally:
            session.close()

    # Pseudocode for consumer integration (from Task 1.2/1.3)
    def process_raw_reviews_and_store(raw_review_message: str):
        try:
            raw_review = json.loads(raw_review_message)
            
            # Map raw data to Review model fields, handling type conversions
            review_data_for_db = {
                'review_id': raw_review['review_id'],
                'product_asin': raw_review['product_asin'],
                'reviewer_id': raw_review['reviewer_id'],
                'review_timestamp': datetime.fromisoformat(raw_review['review_date'].replace('Z', '+00:00')),
                'ingestion_timestamp': datetime.fromisoformat(raw_review['ingestion_timestamp'].replace('Z', '+00:00')),
                'review_text': raw_review.get('review_text'),
                'review_title': raw_review.get('review_title'),
                'rating': float(raw_review['rating']),
                'helpfulness_votes': int(raw_review.get('helpfulness_votes', 0)),
                # Default values for is_flagged, moderation_status, is_public are handled by schema
            }

            insert_or_update_review(review_data_for_db)
        except Exception as e:
            print(f"Failed to process and store raw review: {raw_review_message}. Error: {e}")
            # Re-publish to DLQ or log for manual inspection

    # Example usage (would be part of the Kafka consumer loop)
    # if __name__ == '__main__':
    #     setup_database()
    #     sample_raw_review_msg = json.dumps({
    #         "review_id": "RTEST123",
    #         "product_asin": "B00TEST001",
    #         "reviewer_id": "ATestUser",
    #         "review_text": "This is a test review.",
    #         "review_title": "Test",
    #         "rating": 4.0,
    #         "review_date": "2023-01-01T12:00:00Z",
    #         "helpfulness_votes": 5,
    #         "ingestion_timestamp": datetime.utcnow().isoformat() + 'Z'
    #     })
    #     process_raw_reviews_and_store(sample_raw_review_msg)
    ```

---

### Task 2.3: Develop data mapping and transformation logic

*   **Implementation Plan:**
    1.  **Identify Discrepancies:** Compare the `RawReview` data model (from ingestion) with the `ReviewMetadata` database schema. Note differences in naming, data types, and required fields.
    2.  **Define Mapping Rules:** Create explicit rules for mapping each field from the raw ingested data to its corresponding database column. This includes type conversions (e.g., string date to `datetime` object, string rating to `float`).
    3.  **Implement Transformation Function:** Develop a function that takes raw review data (e.g., a dictionary from the message queue) and transforms it into the format suitable for database insertion (e.g., a dictionary matching the SQLAlchemy `Review` model attributes).
    4.  **Handle Missing/Invalid Data:** Implement robust error handling for cases where raw data might be missing expected fields or contain invalid formats. Define default values or strategies for handling such scenarios (e.g., skip, log error, place in DLQ).

*   **Data Models and Architecture:**
    *   **Architecture:** The transformation logic will reside within the `Processing Service`, acting as an intermediary between the message queue consumer and the database persistence layer.
    *   **Input Data Model (from Kafka):** `RawReview` (as defined in Task 1.2).
    *   **Output Data Model (for DB):** `ReviewMetadata` (as defined in Task 2.1), or a dictionary conforming to its structure.

*   **Assumptions and Technical Decisions:**
    *   **Assumption:** Raw review data from the message queue is generally well-formed JSON, but specific fields might occasionally be missing or malformed.
    *   **Technical Decision:** Use explicit type conversions and validation during mapping to ensure data quality before insertion. Leverage Python's `datetime` for timestamp conversions.
    *   **Technical Decision:** Any transformation failures (e.g., due to unparseable data) should lead to logging and potentially routing the original raw message to a DLQ for investigation, preventing data loss.

*   **Code Snippets/Pseudocode:**
    ```python
    import json
    from datetime import datetime
    from typing import Dict, Any, Optional
    import logging

    logger = logging.getLogger(__name__)

    def transform_raw_review_to_db_format(raw_review_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Transforms raw review data from the ingestion pipeline into a format suitable for database insertion.
        Returns a dictionary or None if transformation fails critically.
        """
        transformed_data = {}
        try:
            transformed_data['review_id'] = raw_review_data['review_id']
            transformed_data['product_asin'] = raw_review_data['product_asin']
            transformed_data['reviewer_id'] = raw_review_data['reviewer_id']

            # Type conversion for timestamps
            transformed_data['review_timestamp'] = datetime.fromisoformat(raw_review_data['review_date'].replace('Z', '+00:00'))
            transformed_data['ingestion_timestamp'] = datetime.fromisoformat(raw_review_data['ingestion_timestamp'].replace('Z', '+00:00'))

            # Optional fields and type conversions
            transformed_data['review_text'] = raw_review_data.get('review_text')
            transformed_data['review_title'] = raw_review_data.get('review_title')
            transformed_data['rating'] = float(raw_review_data['rating']) # Assume rating is always present and convertible
            transformed_data['helpfulness_votes'] = int(raw_review_data.get('helpfulness_votes', 0))

            # Default values for new fields in DB schema, not present in raw ingestion initially
            transformed_data['is_flagged'] = False
            transformed_data['flagging_reason'] = None
            transformed_data['moderation_status'] = 'PENDING'
            transformed_data['is_public'] = True

            return transformed_data

        except KeyError as e:
            logger.error(f"Missing critical field in raw review data: {e}. Data: {raw_review_data}")
            return None # Indicate critical failure, perhaps send to DLQ
        except ValueError as e:
            logger.error(f"Type conversion error in raw review data: {e}. Data: {raw_review_data}")
            return None # Indicate critical failure, perhaps send to DLQ
        except Exception as e:
            logger.error(f"Unexpected error during transformation: {e}. Data: {raw_review_data}")
            return None

    # Integrated into the consumer logic:
    # def process_raw_reviews_and_store(raw_review_message: str):
    #     raw_review_dict = json.loads(raw_review_message)
    #     transformed_data = transform_raw_review_to_db_format(raw_review_dict)
    #     if transformed_data:
    #         insert_or_update_review(transformed_data) # From Task 2.2
    #     else:
    #         # Handle transformation failure: log, alert, or send original message to DLQ
    #         logger.warning(f"Skipping storage for malformed review: {raw_review_dict.get('review_id', 'N/A')}")
    ```

---

### Task 2.4: Testing data integrity and retrieval

*   **Implementation Plan:**
    1.  **Unit Tests for Transformation:** Write unit tests for the `transform_raw_review_to_db_format` function to cover various scenarios: happy path, missing optional fields, invalid data types, edge cases.
    2.  **Integration Tests for Persistence:** Use an in-memory database (e.g., SQLite with SQLAlchemy) or a dedicated test database (e.g., Dockerized PostgreSQL) to test the `insert_or_update_review` function. Verify that data is correctly inserted, updated, and that constraints (e.g., rating range) are enforced.
    3.  **Data Retrieval Tests:** Develop test cases to query the database for stored reviews based on various criteria (e.g., `product_asin`, `reviewer_id`, `review_timestamp` range, `is_flagged`). Assert that retrieved data matches the expected values and formats.
    4.  **Performance Testing (Basic Retrieval):** Perform basic load tests on common retrieval queries to ensure acceptable response times with a reasonable amount of test data.
    5.  **Schema Validation:** Write a script or test to programmatically check if the deployed database schema matches the expected schema, including column names, types, and indexes.

*   **Data Models and Architecture:**
    *   No new data models or architectural components are introduced. The focus is on verifying the correctness and performance of the existing database and interaction logic.

*   **Assumptions and Technical Decisions:**
    *   **Assumption:** A testing framework (`pytest` or `unittest`) and mocking library (`unittest.mock`) are available.
    *   **Technical Decision:** For database integration tests, use a temporary, isolated database instance to ensure tests are repeatable and don't interfere with each other. PostgreSQL in Docker is preferred for mimicking the production environment.
    *   **Technical Decision:** Define a comprehensive set of assertion checks for retrieved data, including data types, values, and the absence of unexpected data.

*   **Code Snippets/Pseudocode:**
    ```python
    import unittest
    from unittest.mock import patch, MagicMock
    from datetime import datetime, timezone
    import json

    # Import the functions and classes from Task 2.2 and 2.3 (assuming they are in 'data_storage_module')
    # from your_project.data_storage import Review, setup_database, insert_or_update_review
    # from your_project.data_processing import transform_raw_review_to_db_format

    # Mock the SQLAlchemy engine and session for unit tests if necessary, or use an in-memory SQLite
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # For testing, we'll redefine a simplified Review model and in-memory DB setup
    from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, JSON
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()

    class TestReview(Base):
        __tablename__ = 'reviews'
        review_id = Column(String(255), primary_key=True)
        product_asin = Column(String(10), nullable=False, index=True)
        reviewer_id = Column(String(255), nullable=False, index=True)
        review_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
        ingestion_timestamp = Column(DateTime(timezone=True), nullable=False)
        review_text = Column(Text)
        review_title = Column(String(500))
        rating = Column(Float, nullable=False)
        helpfulness_votes = Column(Integer, default=0)
        is_flagged = Column(Boolean, default=False)
        flagging_reason = Column(JSONB) # Stores as JSONB in PostgreSQL
        moderation_status = Column(String(50), default='PENDING') # ENUM: PENDING, ABUSIVE, LEGITIMATE
        is_public = Column(Boolean, default=True)

    # In-memory SQLite for isolated testing
    test_engine = create_engine('sqlite:///:memory:')
    TestSession = sessionmaker(bind=test_engine)
    Base.metadata.create_all(test_engine) # Create tables for in-memory DB

    # Re-implement insert_or_update_review for testing with TestSession
    def test_insert_or_update_review(review_data: dict):
        session = TestSession()
        try:
            existing_review = session.query(TestReview).filter_by(review_id=review_data['review_id']).first()

            if existing_review:
                for key, value in review_data.items():
                    setattr(existing_review, key, value)
            else:
                new_review = TestReview(**review_data)
                session.add(new_review)

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Simplified transform_raw_review_to_db_format for testing purposes here
    # In a real setup, this would be imported from the actual module.
    def test_transform_raw_review_to_db_format(raw_review_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        transformed_data = {}
        try:
            transformed_data['review_id'] = raw_review_data['review_id']
            transformed_data['product_asin'] = raw_review_data['product_asin']
            transformed_data['reviewer_id'] = raw_review_data['reviewer_id']

            transformed_data['review_timestamp'] = datetime.fromisoformat(raw_review_data['review_date'].replace('Z', '+00:00'))
            transformed_data['ingestion_timestamp'] = datetime.fromisoformat(raw_review_data['ingestion_timestamp'].replace('Z', '+00:00'))

            transformed_data['review_text'] = raw_review_data.get('review_text')
            transformed_data['review_title'] = raw_review_data.get('review_title')
            transformed_data['rating'] = float(raw_review_data['rating'])
            transformed_data['helpfulness_votes'] = int(raw_review_data.get('helpfulness_votes', 0))

            transformed_data['is_flagged'] = False
            transformed_data['flagging_reason'] = None
            transformed_data['moderation_status'] = 'PENDING'
            transformed_data['is_public'] = True

            return transformed_data
        except Exception:
            return None


    class TestDataStorage(unittest.TestCase):

        def setUp(self):
            # Clear the in-memory database before each test
            Base.metadata.drop_all(test_engine)
            Base.metadata.create_all(test_engine)

        def test_transformation_happy_path(self):
            raw_data = {
                "review_id": "R123",
                "product_asin": "B001",
                "reviewer_id": "U1",
                "review_date": "2023-10-26T10:00:00Z",
                "ingestion_timestamp": "2023-10-26T10:05:00Z",
                "review_text": "Great product!",
                "review_title": "Excellent",
                "rating": 5.0,
                "helpfulness_votes": 10
            }
            transformed = test_transform_raw_review_to_db_format(raw_data)
            self.assertIsNotNone(transformed)
            self.assertEqual(transformed['review_id'], "R123")
            self.assertIsInstance(transformed['review_timestamp'], datetime)
            self.assertEqual(transformed['rating'], 5.0)
            self.assertEqual(transformed['moderation_status'], 'PENDING')

        def test_transformation_missing_required_field(self):
            raw_data = {
                "product_asin": "B001", # Missing review_id
                "reviewer_id": "U1",
                "review_date": "2023-10-26T10:00:00Z",
                "ingestion_timestamp": "2023-10-26T10:05:00Z",
                "rating": 5.0
            }
            transformed = test_transform_raw_review_to_db_format(raw_data)
            self.assertIsNone(transformed)

        def test_insert_new_review(self):
            review_data = {
                'review_id': 'R456',
                'product_asin': 'B002',
                'reviewer_id': 'U2',
                'review_timestamp': datetime(2023, 10, 27, 11, 0, 0, tzinfo=timezone.utc),
                'ingestion_timestamp': datetime(2023, 10, 27, 11, 5, 0, tzinfo=timezone.utc),
                'review_text': 'Good value.',
                'review_title': 'Okay',
                'rating': 4.0,
                'helpfulness_votes': 7
            }
            test_insert_or_update_review(review_data)

            session = TestSession()
            retrieved_review = session.query(TestReview).filter_by(review_id='R456').first()
            session.close()

            self.assertIsNotNone(retrieved_review)
            self.assertEqual(retrieved_review.rating, 4.0)
            self.assertEqual(retrieved_review.moderation_status, 'PENDING')

        def test_update_existing_review(self):
            # Insert initial review
            initial_data = {
                'review_id': 'R789',
                'product_asin': 'B003',
                'reviewer_id': 'U3',
                'review_timestamp': datetime(2023, 10, 28, 12, 0, 0, tzinfo=timezone.utc),
                'ingestion_timestamp': datetime(2023, 10, 28, 12, 5, 0, tzinfo=timezone.utc),
                'review_text': 'Original text.',
                'review_title': 'Old',
                'rating': 3.0,
                'helpfulness_votes': 2
            }
            test_insert_or_update_review(initial_data)

            # Update some fields
            updated_data = initial_data.copy()
            updated_data['review_text'] = 'Updated text now!'
            updated_data['rating'] = 4.5
            test_insert_or_update_review(updated_data)

            session = TestSession()
            retrieved_review = session.query(TestReview).filter_by(review_id='R789').first()
            session.close()

            self.assertIsNotNone(retrieved_review)
            self.assertEqual(retrieved_review.review_text, 'Updated text now!')
            self.assertEqual(retrieved_review.rating, 4.5)
            self.assertEqual(retrieved_review.helpfulness_votes, 2) # Should remain the same

        def test_retrieve_by_product_asin(self):
            review_data_1 = {
                'review_id': 'R_P1_1',
                'product_asin': 'B00XYZ',
                'reviewer_id': 'U_A',
                'review_timestamp': datetime(2023, 9, 1, 0, 0, 0, tzinfo=timezone.utc),
                'ingestion_timestamp': datetime(2023, 9, 1, 0, 0, 0, tzinfo=timezone.utc),
                'review_text': 'text1', 'rating': 5.0
            }
            review_data_2 = {
                'review_id': 'R_P1_2',
                'product_asin': 'B00XYZ',
                'reviewer_id': 'U_B',
                'review_timestamp': datetime(2023, 9, 2, 0, 0, 0, tzinfo=timezone.utc),
                'ingestion_timestamp': datetime(2023, 9, 2, 0, 0, 0, tzinfo=timezone.utc),
                'review_text': 'text2', 'rating': 4.0
            }
            review_data_3 = {
                'review_id': 'R_P2_1',
                'product_asin': 'B00ABC',
                'reviewer_id': 'U_C',
                'review_timestamp': datetime(2023, 9, 3, 0, 0, 0, tzinfo=timezone.utc),
                'ingestion_timestamp': datetime(2023, 9, 3, 0, 0, 0, tzinfo=timezone.utc),
                'review_text': 'text3', 'rating': 3.0
            }
            test_insert_or_update_review(review_data_1)
            test_insert_or_update_review(review_data_2)
            test_insert_or_update_review(review_data_3)

            session = TestSession()
            reviews_for_product_xyz = session.query(TestReview).filter_by(product_asin='B00XYZ').all()
            session.close()

            self.assertEqual(len(reviews_for_product_xyz), 2)
            self.assertIn('R_P1_1', [r.review_id for r in reviews_for_product_xyz])
            self.assertIn('R_P1_2', [r.review_id for r in reviews_for_product_xyz])

        # Pseudocode for a basic schema validation check
        def test_database_schema_integrity(self):
            # In a real scenario, this would connect to the actual DB and compare
            # its schema with a predefined expected schema.
            print("\n--- Conceptual Schema Validation ---")
            inspector = inspect(test_engine)
            table_names = inspector.get_table_names()
            self.assertIn('reviews', table_names)

            columns = inspector.get_columns('reviews')
            column_names = {col['name'] for col in columns}
            expected_columns = {
                'review_id', 'product_asin', 'reviewer_id', 'review_timestamp',
                'ingestion_timestamp', 'review_text', 'review_title', 'rating',
                'helpfulness_votes', 'is_flagged', 'flagging_reason', 'moderation_status', 'is_public'
            }
            self.assertEqual(column_names, expected_columns)
            print("Schema check passed for 'reviews' table (column names).")
            # Further checks for types, primary keys, indexes etc. would go here.


    # Example of running unit tests
    # if __name__ == '__main__':
    #     unittest.main(argv=['first-arg-is-ignored'], exit=False)
    ```
