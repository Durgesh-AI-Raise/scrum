### User Story 0.1: Review Abuse Detection (Pattern)

**Sprint Goal Alignment:** This user story directly contributes to establishing foundational review abuse detection capabilities by automatically flagging reviews that exhibit unusual patterns.

---

#### **ARIS Sprint 1: Task 0.1.1 - Research initial pattern detection algorithms.** (Estimate: 8 hours)

*   **Implementation Plan:**
    *   Explore common anomaly detection algorithms suitable for time-series and categorical data (e.g., sudden high volume, repetitive ratings).
    *   Focus on methods like statistical thresholds (e.g., Z-score, IQR for volume), frequency analysis, and simple rule-based systems for `newly created accounts`.
    *   Evaluate their applicability concerning data availability, computational complexity, and ease of integration for near real-time processing.
    *   Document findings, outlining pros and cons, and recommend a primary algorithm strategy for the MVP, along with potential enhancements for future sprints.
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** For MVP, simple, interpretable, and performant algorithms are preferred over complex machine learning models to establish a baseline quickly.
    *   **Technical Decision:** Initially, prioritize rule-based detection for "sudden high volume" (thresholds) and "reviews from newly created accounts" (account age check) due to their direct mapping to business rules and ease of implementation.
    *   **Technical Decision:** Defer more complex "highly repetitive ratings" detection that might require sequence analysis to a later sprint, focusing on basic frequency checks for MVP.
*   **Code Snippets/Pseudocode:** N/A for a research task.

---

#### **ARIS Sprint 1: Task 0.1.2 - Develop data ingestion pipeline for review patterns.** (Estimate: 16 hours)

*   **Implementation Plan:**
    *   Design and implement a data ingestion pipeline to consume raw review data.
    *   The pipeline will perform data cleaning, normalization, and enrichment. Enrichment will involve fetching additional context such as `accountCreationDate` for the reviewer and calculating real-time aggregates like `reviewerReviewCountLast24h` and `productReviewCountLast24h`.
    *   Store the raw and processed review data in suitable storage for downstream processing and historical analysis.
*   **Data Models and Architecture:**
    *   **Data Models:**
        *   `RawReview`:
            *   `reviewId: string` (PK)
            *   `reviewerId: string`
            *   `productId: string`
            *   `sellerId: string`
            *   `rating: int` (1-5)
            *   `reviewText: string`
            *   `reviewDate: datetime`
            *   `ipAddress: string`
        *   `ProcessedReview`:
            *   `reviewId: string` (PK)
            *   `reviewerId: string` (FK)
            *   `productId: string` (FK)
            *   `rating: int`
            *   `reviewDate: datetime`
            *   `ipAddress: string`
            *   `accountCreationDate: datetime` (Enriched from Reviewer Service)
            *   `isNewAccount: boolean` (Derived: e.g., account created < 30 days ago)
            *   `reviewerReviewCountLast24h: int` (Derived: total reviews by reviewer in last 24h)
            *   `productReviewCountLast24h: int` (Derived: total reviews for product in last 24h)
    *   **Architecture:**
        *   Amazon Review Stream (e.g., Kinesis) -> Ingestion Service (e.g., AWS Lambda/Fargate with Python) -> Data Lake (S3 for raw/processed data) -> NoSQL Database (e.g., DynamoDB) for quick access to `ProcessedReview`.
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** A real-time or near real-time stream of raw review data is available from Amazon's core systems.
    *   **Assumption:** Access to a Reviewer/Account Service is available to retrieve `accountCreationDate`.
    *   **Technical Decision:** Use Python with Boto3 for AWS services (Lambda, Kinesis, S3, DynamoDB) due to developer familiarity and ecosystem.
    *   **Technical Decision:** Employ a serverless architecture (AWS Lambda) for the ingestion service to handle varying loads efficiently.
*   **Code Snippets/Pseudocode:**
    ```python
    # Pseudocode for data ingestion and enrichment function
    def ingest_and_process_review(raw_review_data):
        review = parse_raw_review(raw_review_data)

        # Fetch reviewer details (e.g., from an external service or database)
        reviewer_details = get_reviewer_details(review.reviewerId)
        review.accountCreationDate = reviewer_details.get('creationDate')

        # Derive isNewAccount (e.g., within 30 days of creation)
        if review.accountCreationDate:
            review.isNewAccount = (datetime.now() - review.accountCreationDate).days < 30
        else:
            review.isNewAccount = False # Default if creation date not available

        # Calculate review counts for patterns (simplified, would query a time-series store)
        # In a real scenario, this might involve querying a fast data store (e.g., Redis, or a time-series DB)
        review.reviewerReviewCountLast24h = query_recent_reviewer_reviews(review.reviewerId, hours=24) + 1 # Include current review
        review.productReviewCountLast24h = query_recent_product_reviews(review.productId, hours=24) + 1 # Include current review

        # Store the processed review in DynamoDB
        save_processed_review_to_db(review)
        return review
    ```

---

#### **ARIS Sprint 1: Task 0.1.3 - Implement pattern detection service for reviews.** (Estimate: 24 hours)

*   **Implementation Plan:**
    *   Develop a microservice (e.g., another Lambda function) that is triggered by new `ProcessedReview` entries.
    *   Implement the core pattern detection logic based on predefined thresholds and rules.
    *   The service will evaluate each `ProcessedReview` against the defined patterns (high volume, new account) and generate a `DetectionResult` if a pattern is matched.
*   **Data Models and Architecture:**
    *   **Data Models:**
        *   `DetectionResult`:
            *   `reviewId: string`
            *   `detectionType: string` (e.g., "HighVolumeReviewer", "HighVolumeProduct", "NewAccountReview")
            *   `severity: string` (e.g., "High", "Medium", "Low")
            *   `detectionTimestamp: datetime`
            *   `details: dict` (e.g., `{'threshold': 10, 'actual_count': 15, 'accountAgeDays': 5}`)
    *   **Architecture:**
        *   Processed Review Data (DynamoDB Stream or Kinesis) -> Pattern Detection Service (e.g., AWS Lambda) -> Detection Results Storage (e.g., Kafka/Kinesis for further processing, or directly to `FlaggedReview` table).
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** Thresholds for "high volume" and criteria for "new account" will be configurable, even if hardcoded initially for MVP.
    *   **Technical Decision:** Use Python for the detection logic, making it easily extendable for new patterns.
    *   **Technical Decision:** Leverage a serverless function (AWS Lambda) for event-driven, scalable pattern detection.
*   **Code Snippets/Pseudocode:**
    ```python
    # Pseudocode for pattern detection logic
    HIGH_VOLUME_REVIEWER_THRESHOLD = 5  # Example: 5 reviews in 24 hours
    HIGH_VOLUME_PRODUCT_THRESHOLD = 20  # Example: 20 reviews for product in 24 hours
    NEW_ACCOUNT_AGE_DAYS_THRESHOLD = 30 # Example: Account less than 30 days old

    def detect_patterns(processed_review):
        flags = []

        # Pattern 1: Sudden high volume by reviewer
        if processed_review.reviewerReviewCountLast24h > HIGH_VOLUME_REVIEWER_THRESHOLD:
            flags.append({
                'type': 'HighVolumeReviewer',
                'severity': 'High',
                'details': {
                    'threshold': HIGH_VOLUME_REVIEWER_THRESHOLD,
                    'actual_count': processed_review.reviewerReviewCountLast24h
                }
            })

        # Pattern 2: Sudden high volume for a product
        if processed_review.productReviewCountLast24h > HIGH_VOLUME_PRODUCT_THRESHOLD:
            flags.append({
                'type': 'HighVolumeProduct',
                'severity': 'Medium',
                'details': {
                    'threshold': HIGH_VOLUME_PRODUCT_THRESHOLD,
                    'actual_count': processed_review.productReviewCountLast24h
                }
            })

        # Pattern 3: Reviews from newly created accounts
        if processed_review.isNewAccount:
            flags.append({
                'type': 'NewAccountReview',
                'severity': 'Medium',
                'details': {
                    'accountAgeThresholdDays': NEW_ACCOUNT_AGE_DAYS_THRESHOLD,
                    'accountAgeDays': (datetime.now() - processed_review.accountCreationDate).days if processed_review.accountCreationDate else None
                }
            })

        return flags
    ```

---

#### **ARIS Sprint 1: Task 0.1.4 - Store detection results and metadata.** (Estimate: 12 hours)

*   **Implementation Plan:**
    *   Create a dedicated database table (`FlaggedReviews`) to store the results of the pattern detection.
    *   Each record will link back to the original review and include the specific abuse type detected, severity, and any relevant metadata for investigation.
    *   Ensure appropriate indexing for efficient querying by the Investigator Dashboard.
*   **Data Models and Architecture:**
    *   **Data Models:**
        *   `FlaggedReview`:
            *   `flagId: string` (PK, UUID)
            *   `reviewId: string` (FK to `RawReview` and `ProcessedReview`)
            *   `reviewerId: string`
            *   `productId: string`
            *   `flaggedDate: datetime` (Timestamp of detection)
            *   `abuseType: string` (e.g., "Pattern: High Volume Reviewer", "Pattern: New Account")
            *   `severity: string` (e.g., "High", "Medium", "Low")
            *   `status: string` (Initial: "Pending", can be updated: "Investigating", "False Positive", "Confirmed Abuse")
            *   `detectionDetails: json` (Stored as a JSON object, containing details from `DetectionResult`)
    *   **Architecture:**
        *   Pattern Detection Service -> Flagged Reviews Database (e.g., DynamoDB/PostgreSQL).
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** The `FlaggedReview` table will be the primary source for the Investigator Dashboard.
    *   **Technical Decision:** Use DynamoDB for its schemaless nature, scalability, and integration with AWS Lambda if a serverless approach is chosen for the detection service. If more complex querying or relations are needed, PostgreSQL could be considered. For MVP, DynamoDB is suitable.
    *   **Technical Decision:** Index `reviewId`, `abuseType`, `severity`, and `flaggedDate` to support common dashboard queries.
*   **Code Snippets/Pseudocode:**
    ```python
    import uuid
    from datetime import datetime

    # Pseudocode for storing detection results
    def store_flagged_review(review_id, reviewer_id, product_id, detection_flags):
        for flag in detection_flags:
            flagged_review_record = {
                'flagId': str(uuid.uuid4()),  # Generate a unique ID for each flag instance
                'reviewId': review_id,
                'reviewerId': reviewer_id,
                'productId': product_id,
                'flaggedDate': datetime.utcnow().isoformat(),
                'abuseType': f"Pattern: {flag['type']}",
                'severity': flag['severity'],
                'status': 'Pending',  # Initial status for investigation
                'detectionDetails': flag['details'] # Store as JSON
            }
            # Save this record to your FlaggedReviews database (e.g., DynamoDB)
            save_to_flagged_reviews_db(flagged_review_record)
            print(f"Stored flag for review {review_id}: {flagged_review_record['abuseType']}")

    # Example usage:
    # flags_detected = detect_patterns(example_processed_review)
    # store_flagged_review(example_processed_review.reviewId, example_processed_review.reviewerId, example_processed_review.productId, flags_detected)
    ```