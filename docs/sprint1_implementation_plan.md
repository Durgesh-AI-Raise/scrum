### Sprint 1 Implementation Plan: Real-time Review Data Ingestion & Keyword Detection

**Sprint Goal:** "Establish the foundational real-time review data ingestion pipeline and implement a basic keyword-based detection mechanism, ensuring the system continuously receives and initially processes Amazon product reviews."

### Overall Architecture and Data Models for Sprint 1

**Architecture Overview:**
For Sprint 1, a stream-processing architecture will be adopted to handle real-time Amazon product reviews.

1.  **Review Ingestion Service:** Connects to Amazon's review data source (API/feed), fetches reviews, and publishes them to a message broker.
2.  **Message Broker (Apache Kafka):** Acts as a central nervous system for real-time data, enabling decoupling between ingestion and processing.
3.  **Review Processing Service:** Consumes reviews from the message broker, parses them, applies keyword detection, and enriches the data.
4.  **Database (PostgreSQL):** Stores the processed and flagged review data and the list of suspicious keywords.

```mermaid
graph LR
    A[Amazon Review Data Feed (Mock)] --> B(Review Ingestion Service);
    B --> C(Message Broker - Kafka);
    C --> D(Review Processing Service);
    D -- Stores & Flags --> E[Database - PostgreSQL];
    D -- Loads Keywords From --> E;
```

**Data Models:**

**1. `Review` Data Model (Stored in Database):**

```python
class Review:
    review_id: str  # Unique identifier for the review (e.g., from Amazon)
    product_id: str # Identifier for the product
    user_id: str    # Identifier for the user
    review_text: str
    rating: int     # 1-5 stars
    review_date: datetime # Original date of the review
    ingestion_timestamp: datetime # Timestamp when the system ingested the review
    is_flagged: bool = False # True if any suspicious keyword/phrase is found
    flagging_reasons: list[str] = [] # List of keywords/phrases that triggered the flag
```

**2. `SuspiciousKeyword` Data Model (Stored in Database):**

```python
class SuspiciousKeyword:
    keyword_id: str # Unique identifier for the keyword (auto-generated)
    phrase: str     # The actual keyword or phrase (e.g., "free product", "discount code")
    category: str   # Categorization (e.g., "incentive", "fraud")
    is_active: bool = True # Flag to enable/disable keywords without deleting
```

---

### User Story: P1.1 - Data Ingestion

#### Task 1.1.1: Research and select real-time data ingestion framework

*   **Implementation Plan:**
    1.  **Identify Key Requirements:** Real-time processing, scalability, fault tolerance, message durability, ease of integration with Python services, and cost-effectiveness.
    2.  **Evaluation:** Apache Kafka, AWS Kinesis, and Google Cloud Pub/Sub were considered.
    3.  **Decision & Justification:** **Apache Kafka** is selected due to its high throughput, low latency capabilities, robust ecosystem, and flexibility for potential future deployments (on-premise or managed cloud services). This provides a solid, industry-standard foundation for real-time data streams.
*   **Architecture Impact:** Kafka will serve as the central message broker between the Ingestion Service and Processing Service.
*   **Assumptions & Technical Decisions:**
    *   **Decision:** Apache Kafka will be used as the message broker.
    *   **Assumption:** A basic Kafka setup (broker, topics: `amazon_raw_reviews`) will be available and accessible.
    *   **Assumption:** Initial data volume will be manageable by a single Kafka broker for development, with scalability considerations for future.
*   **Code Snippets/Pseudocode:** N/A for research task.

#### Task 1.1.2: Implement basic API integration for Amazon review data feed

*   **Implementation Plan:**
    1.  **Develop Ingestion Service:** Create a Python service (`review_ingestion_service.py`) responsible for fetching reviews.
    2.  **Mock Data Source:** For Sprint 1, actual Amazon API integration will be abstracted. A mock function will generate synthetic Amazon-like review data to simulate the feed.
    3.  **Publish to Kafka:** The service will use the `kafka-python` library to publish these mock raw review data (as JSON strings) to the `amazon_raw_reviews` Kafka topic.
*   **Architecture Impact:** Introduces the "Review Ingestion Service" component.
*   **Assumptions & Technical Decisions:**
    *   **Decision:** A **mock Amazon review data feed** will be used for development to simulate real-time data flow.
    *   **Decision:** The Ingestion Service will be a Python application.
*   **Code Snippets/Pseudocode (See `review_ingestion_service.py` below):** A Python script that generates mock review data and sends it to a Kafka topic.

#### Task 1.1.3: Develop data parsing and initial storage mechanism

*   **Implementation Plan:**
    1.  **Develop Processing Service:** Create a Python service (`review_processing_service.py`) that acts as a consumer for the `amazon_raw_reviews` Kafka topic.
    2.  **Parse Raw Data:** Deserialize incoming JSON messages into a structured format (matching the `Review` data model). Basic validation (e.g., checking for required fields) will be performed.
    3.  **Initial Storage:** Store the parsed review data into the PostgreSQL database. This involves creating a `reviews` table and performing insert/update operations.
*   **Architecture Impact:** The "Review Processing Service" consumes from Kafka and writes to the Database.
*   **Assumptions & Technical Decisions:**
    *   **Decision:** **PostgreSQL** is chosen as the primary database for its robust ACID properties, strong support for structured data, and `JSONB` type for flexible fields like `flagging_reasons`.
    *   **Decision:** The Processing Service will use `kafka-python` for consumption and `psycopg2` for database interaction.
    *   **Assumption:** The raw review data format is consistently JSON.
*   **Code Snippets/Pseudocode (See `review_processing_service.py` and `db_schema.sql` below):** A Python script that consumes from Kafka, parses data, and stores it in PostgreSQL. SQL DDL for the `reviews` table.

---

### User Story: P1.2 - Keyword & Phrase Detection

#### Task 1.2.1: Define initial list of suspicious keywords/phrases in collaboration with Trust & Safety analysts

*   **Implementation Plan:**
    1.  **Collaboration:** Work with Trust & Safety to identify initial high-priority suspicious keywords/phrases (e.g., "free product", "discount code").
    2.  **Categorization:** Assign categories (e.g., "incentive", "spam") to these keywords.
    3.  **Storage:** Store this list in a dedicated `suspicious_keywords` table in the PostgreSQL database, allowing for easy updates and management in future sprints.
*   **Data Models Impact:** Introduces the `SuspiciousKeyword` data model.
*   **Assumptions & Technical Decisions:**
    *   **Decision:** The `suspicious_keywords` table will be created in the same PostgreSQL database.
    *   **Assumption:** The initial list of keywords will be small and can be populated via SQL scripts or an initial setup function.
*   **Code Snippets/Pseudocode (See `db_schema.sql` below):** SQL DDL for `suspicious_keywords` table and initial data insertion.

#### Task 1.2.2: Implement keyword matching logic in review processing

*   **Implementation Plan:**
    1.  **Enhance Processing Service:** Modify the `review_processing_service.py` to incorporate keyword detection logic.
    2.  **Load Keywords:** On startup, the service will load all active suspicious keywords from the `suspicious_keywords` table into an in-memory list for efficient lookup.
    3.  **Matching:** For each incoming review, the `review_text` will be checked (case-insensitively) against the loaded list of suspicious phrases using simple string containment.
*   **Architecture Impact:** The Review Processing Service now has an additional responsibility.
*   **Assumptions & Technical Decisions:**
    *   **Decision:** Simple string containment (`phrase in review_text.lower()`) will be used for initial matching.
    *   **Decision:** Keyword loading will happen at service startup to minimize database calls.
    *   **Assumption:** The initial list of keywords is small enough for efficient in-memory lookup.
*   **Code Snippets/Pseudocode (See `review_processing_service.py` below):** Includes `load_suspicious_keywords` and `detect_keywords` functions integrated into the main processing loop.

#### Task 1.2.3: Store detected flags (including reason) with review data in the database

*   **Implementation Plan:**
    1.  **Database Schema:** The `reviews` table will include `is_flagged` (BOOLEAN) and `flagging_reasons` (JSONB array of strings) columns.
    2.  **Update Logic:** The `store_review_with_detection` function in `review_processing_service.py` will update these fields based on the results of the keyword detection. If any suspicious keyword is found, `is_flagged` will be set to `True`, and the matching keywords will be stored in `flagging_reasons`.
*   **Data Models Impact:** Confirms and implements the `is_flagged` and `flagging_reasons` fields in the `Review` data model.
*   **Assumptions & Technical Decisions:**
    *   **Decision:** PostgreSQL's `JSONB` data type is used for `flagging_reasons` to store a flexible array of strings.
*   **Code Snippets/Pseudocode (Already integrated into Task 1.2.2 `review_processing_service.py` and `db_schema.sql` DDL):** The database interaction logic will handle saving these new fields.
