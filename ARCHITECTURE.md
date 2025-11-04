# ARIS MVP: Architecture and Data Models

**System Overview:**
The Amazon Review Integrity System (ARIS) MVP will use a serverless, event-driven architecture on AWS. Real-time review data will be ingested via Kinesis, processed by multiple Lambda functions for abuse detection, stored in DynamoDB, and surfaced on a web-based analyst dashboard.

**Architecture Diagram (Conceptual):**

```
[Review Source System]
      | (Real-time Review Events)
      v
[AWS Kinesis Data Stream: aris-raw-reviews]
      |
      v
[AWS Lambda: ReviewIngestionService]
      |   (1. Validate & Enrich)
      |   (2. Write to DynamoDB)
      |   (3. Publish to next Kinesis)
      v
[AWS Kinesis Data Stream: aris-processed-reviews]
      |
      +-----> [AWS Lambda: TextAnalysisModule]
      |               ^ (Reads `suspicious_patterns` config)
      |               | (Updates `aris-all-reviews` with flags & score)
      |               v
      |         [DynamoDB: aris-all-reviews] (Stores all reviews with flags)
      |
      +-----> [AWS Lambda: AccountActivityModule]
                      ^ (Reads `account_activity_rules` config)
                      | (Fetches/Updates `aris-reviewer-activity` state)
                      | (Updates `aris-all-reviews` with flags & score)
                      v
                [DynamoDB: aris-reviewer-activity] (Stores reviewer activity state)

[Analyst Dashboard (Browser)]
      ^
      | (Fetches Flagged Reviews)
      v
[AWS API Gateway]
      |
      v
[AWS Lambda: DashboardApiService]
      |
      v
[DynamoDB: aris-all-reviews] (Queries GSI: FlaggedReviewsByScoreIndex)
```

**Data Models:**

*   **Kinesis Stream: `aris-raw-reviews`**
    *   **Purpose:** Initial ingestion of raw review events.
    *   **Data Format:** Raw JSON payload as received from the source.
    *   **Example Payload:**
        ```json
        {
            "reviewId": "r12345",
            "productId": "p67890",
            "reviewerId": "u11223",
            "reviewText": "This product is absolutely amazing and I love it so much!",
            "rating": 5,
            "reviewDate": "2023-10-27T10:00:00Z",
            "marketplace": "US",
            "sourceIp": "192.168.1.1"
        }
        ```

*   **Kinesis Stream: `aris-processed-reviews`**
    *   **Purpose:** Standardized review events after initial validation and enrichment.
    *   **Data Format:** Structured JSON.
    *   **Example Payload:**
        ```json
        {
            "reviewId": "r12345",
            "productId": "p67890",
            "reviewerId": "u11223",
            "reviewText": "This product is absolutely amazing and I love it so much!",
            "rating": 5,
            "reviewDate": "2023-10-27T10:00:00Z",
            "marketplace": "US",
            "productCategory": "Electronics", // Enriched data
            "processedTimestamp": "2023-10-27T10:05:00Z"
        }
        ```

*   **DynamoDB Table: `aris-all-reviews`**
    *   **Purpose:** Persistent storage for all ingested reviews, including detection flags and scores.
    *   **Primary Key:** `reviewId` (Partition Key - String)
    *   **Attributes:**
        *   `reviewId` (String): Unique identifier for the review.
        *   `productId` (String): Identifier of the product reviewed.
        *   `reviewerId` (String): Identifier of the reviewer.
        *   `reviewText` (String): The full text of the review.
        *   `rating` (Number): Star rating (e.g., 1-5).
        *   `reviewDate` (String ISO 8601): Date and time the review was submitted.
        *   `marketplace` (String): The Amazon marketplace (e.g., "US", "UK").
        *   `productCategory` (String): Category of the product (e.g., "Electronics", "Books").
        *   `processedTimestamp` (String ISO 8601): Timestamp when the review was processed by the ingestion service.
        *   `isFlagged` (Boolean): `true` if any abuse detection module flagged the review, `false` otherwise (default).
        *   `abuseScore` (Number): Aggregated confidence score indicating likelihood of abuse (sum of all triggered flag scores, default `0.0`).
        *   `flagDetails` (List of Map): Details of each triggered detection rule.
            ```json
            [
                {
                    "type": "String",      // e.g., "text_pattern", "account_activity"
                    "ruleId": "String",    // e.g., "GENERIC_PRAISE", "HIGH_VELOCITY_NEW_ACCOUNT"
                    "description": "String", // Human-readable description of the rule
                    "score": "Number",     // Confidence score for this specific flag
                    "timestamp": "String ISO 8601" // When this flag was added
                }
            ]
            ```
    *   **Global Secondary Index (GSI): `FlaggedReviewsByScoreIndex`**
        *   **Partition Key:** `isFlagged` (Boolean)
        *   **Sort Key:** `abuseScore` (Number)
        *   **Purpose:** Efficiently query for all flagged reviews and sort them by their abuse score for the dashboard.

*   **DynamoDB Table: `aris-reviewer-activity`**
    *   **Purpose:** Stores historical activity data for each reviewer to enable unusual activity pattern detection.
    *   **Primary Key:** `reviewerId` (Partition Key - String)
    *   **Attributes:**
        *   `reviewerId` (String): Unique identifier for the reviewer.
        *   `accountCreationDate` (String ISO 8601): Date when the reviewer account was created (for MVP, this is the date of their first review observed by ARIS).
        *   `lastReviewDate` (String ISO 8601): Date of the reviewer's most recent review.
        *   `totalReviews` (Number): Total number of reviews submitted by this reviewer.
        *   `recentReviews` (List of Map): A time-windowed list of recent review summaries.
            ```json
            [
                {
                    "reviewId": "String",
                    "reviewDate": "String ISO 8601",
                    "productId": "String",
                    "productCategory": "String"
                }
            ]
            ```
            (This list will be actively managed to only keep reviews within a specific timeframe, e.g., last 24-72 hours, to optimize storage and query performance for activity analysis).
