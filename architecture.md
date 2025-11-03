# Amazon Review Guardian - Sprint 1 Architecture & Data Models

## Architecture Overview

The "Amazon Review Guardian" system adopts a **microservices architecture** deployed on AWS, emphasizing scalability, resilience, and independent service management.

```mermaid
graph TD
    A[Amazon.com Review Feed] -->|Push/Stream JSON| B(Ingestion Service - FastAPI/Lambda)
    B --> C(Raw/Processed Review Storage - DynamoDB: AmazonReviewGuardianReviews)
    C -->|New Review Event (SQS: review_ingested_queue)| D(Detection Service - AWS Lambda)
    D --> E(Update Review in DynamoDB)
    F[Trust & Safety Analyst/Manager] --> G(Frontend Application - React via CloudFront/S3)
    G --> H(API Gateway)
    H --> I(Dashboard Service - FastAPI/Lambda)
    H --> J(Action Service - FastAPI/Lambda)
    I --> E
    J --> E
    E -->|Scheduled Query (Daily)| K(Reporting Service - AWS Lambda)
    K --> L(Daily Reports Storage - DynamoDB: AmazonReviewGuardianReports)
    H --> M(Reporting Service API - FastAPI/Lambda)
    M --> L
    J -->|Review Action Event (SQS: review_action_events_queue)| N(External Amazon.com System - Placeholder for Review Removal)
```

**Key Components:**
*   **Ingestion Service:** A Python FastAPI application (deployed as Lambda/container) that receives new review data via a REST endpoint. It performs initial validation, stores the review, and publishes a "review ingested" event to SQS.
*   **Detection Service:** An AWS Lambda function triggered by messages from the `review_ingested_queue`. It fetches the review, applies rule-based detection logic, calculates a suspicion score, generates flagging reasons, and updates the review record in DynamoDB.
*   **Dashboard Service:** A Python FastAPI application (deployed as Lambda/container) providing API endpoints for the frontend dashboard. It queries `AmazonReviewGuardianReviews` for flagged reviews, supporting filtering and sorting.
*   **Action Service:** A Python FastAPI application (deployed as Lambda/container) that exposes API endpoints for analysts to take actions (e.g., remove a review, mark as not abusive). It updates the review status in DynamoDB and publishes "review action" events to SQS.
*   **Reporting Service (Lambda):** A scheduled AWS Lambda function (triggered daily by CloudWatch Events/EventBridge) that aggregates daily statistics (flagged, removed, not abusive reviews) by querying `AmazonReviewGuardianReviews` and stores them in `AmazonReviewGuardianReports`.
*   **Reporting Service API:** A Python FastAPI application (deployed as Lambda/container) that provides API endpoints for the frontend to retrieve aggregated daily reports.
*   **Frontend Application:** A React.js single-page application hosted on AWS S3/CloudFront, providing the user interface for analysts and managers.
*   **Amazon DynamoDB:** NoSQL database used for persistent storage of review data (`AmazonReviewGuardianReviews`) and aggregated reports (`AmazonReviewGuardianReports`). Chosen for its scalability, performance, and flexible schema.
*   **Amazon SQS (Simple Queue Service):** Used for asynchronous, decoupled communication between services (e.g., Ingestion to Detection, Action to External Systems). Ensures reliability and allows services to operate independently.
*   **AWS Lambda:** Serverless compute service used for event-driven processing (Detection, Reporting) and potentially backing API Gateway endpoints for other services.
*   **Amazon API Gateway:** Provides a secure, scalable entry point for all frontend-to-backend API calls.

## Core Data Models

### 1. `Review` (DynamoDB Table: `AmazonReviewGuardianReviews`)

This is the primary data model, capturing the review itself and all related metadata from detection and analyst actions.

```json
{
  "reviewId": "string (PK)",         // Primary Key: Unique identifier for the review (e.g., "R123ABCDEF")
  "productId": "string",             // ID of the product reviewed (e.g., "B07XXXXXXX")
  "userId": "string",                // ID of the user who wrote the review (e.g., "A1B2C3D4E5")
  "reviewText": "string",            // Full text content of the review
  "rating": "integer",               // Star rating given by the user (1-5)
  "reviewDate": "timestamp",         // Original date/time the review was published on Amazon (ISO 8601)
  "source": "string",                // Source system of the review (e.g., "Amazon.com")
  "ingestionTimestamp": "timestamp", // When the review was first ingested into the Guardian system (ISO 8601)

  // --- Detection-related Fields ---
  "isFlagged": "boolean",            // True if the review has been flagged as suspicious by the system
  "suspicionScore": "float",         // A cumulative score (0.0 to 1.0) indicating the level of suspicion.
                                     // Derived from `scoreContribution` of all flagging reasons.
  "flaggingReasons": [               // An array of objects, each detailing a specific reason for flagging
    {
      "reasonCode": "string",        // A short, programmatic code for the reason (e.g., "KEYWORD_MATCH", "SHORT_REVIEW_LENGTH")
      "description": "string",       // A human-readable explanation of the flagging reason
      "evidenceDetails": "json",     // A dynamic JSON object containing specific evidence for the reason.
                                     // E.g., `{"keywords_found": ["fake", "scam"]}` or `{"word_count": 5}`.
      "scoreContribution": "float"   // The individual score contributed by this specific reason to the total `suspicionScore`.
    }
  ],
  "detectionTimestamp": "timestamp", // When the detection process was completed for this review (ISO 8601)
  "detectionDate": "string",         // YYYY-MM-DD extracted from detectionTimestamp, for GSI partitioning.

  // --- Action-related Fields ---
  "status": "string",                // Current status of the review within the Guardian system:
                                     // - "NOT_FLAGGED": Review was processed but not flagged.
                                     // - "PENDING_REVIEW": Review was flagged and awaits analyst action.
                                     // - "ABUSIVE_REMOVED": Analyst confirmed abusive and removed (via external system).
                                     // - "NOT_ABUSIVE": Analyst confirmed not abusive.
  "analystId": "string (optional)",  // ID of the Trust & Safety Analyst who performed the last action.
  "actionDate": "timestamp (optional)", // When the last analyst action was taken (ISO 8601)
  "reasonForRemoval": "string (optional)", // Analyst's specific reason for marking as 'ABUSIVE_REMOVED'.
  "reasonForMarkingNotAbusive": "string (optional)" // Analyst's specific reason for marking as 'NOT_ABUSIVE'.
}
```
**DynamoDB Global Secondary Indexes (GSIs) for `AmazonReviewGuardianReviews`:**
*   **`status-index`**: Partition Key: `status` (String), Sort Key: `suspicionScore` (Number, descending).
    *   **Purpose:** Efficiently query all reviews by their current status (e.g., `PENDING_REVIEW`) and easily sort them by suspicion level for the dashboard.
*   **`detectionDate-index`**: Partition Key: `detectionDate` (String - YYYY-MM-DD), Sort Key: `reviewId` (String).
    *   **Purpose:** Enable daily aggregation for reporting total processed and flagged reviews.
*   **`actionDate-index`**: Partition Key: `actionDate` (String - YYYY-MM-DD), Sort Key: `reviewId` (String).
    *   **Purpose:** Enable daily aggregation for reporting removed and not-abusive reviews.

### 2. `DailyReport` (DynamoDB Table: `AmazonReviewGuardianReports`)

This table stores aggregated daily metrics for monitoring system performance and team activity.

```json
{
  "reportDate": "date (PK - YYYY-MM-DD)", // Primary Key: The specific date for which the report data is aggregated.
  "flaggedReviewsCount": "integer",      // Total number of reviews that were flagged as suspicious on this `reportDate`.
  "removedReviewsCount": "integer",      // Total number of reviews marked as 'ABUSIVE_REMOVED' on this `reportDate`.
  "notAbusiveReviewsCount": "integer",   // Total number of reviews marked as 'NOT_ABUSIVE' on this `reportDate`.
  "totalReviewsProcessed": "integer",    // Total number of reviews that underwent the detection process on this `reportDate`.
  "generationTimestamp": "timestamp"     // The timestamp when this daily report record was generated (ISO 8601).
}
```
**DynamoDB Indexes for `AmazonReviewGuardianReports`:**
*   **Primary Key:** `reportDate` (String). Allows direct lookup of a report for a specific day and range queries over time.