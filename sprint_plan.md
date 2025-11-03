# Sprint Plan: Review Abuse Detection & Tracking System

This document outlines the implementation plan, data models, architecture, assumptions, technical decisions, and key code snippets for the current sprint, focusing on establishing the foundational Review Abuse Detection & Tracking System.

## Overall Architecture

The system is designed with a microservices approach, leveraging AWS managed services for scalability, reliability, and reduced operational overhead.

-   **Ingestion Layer:** AWS Kinesis Data Stream (`review_ingestion_stream`) as the entry point, processed by an AWS Lambda function (`review_ingestor_lambda`).
-   **Processing Layer:** AWS Kinesis Data Stream (`abuse_detection_stream`) for events, processed by an AWS Lambda function (`rule_engine_lambda`).
-   **Storage Layer:** AWS DynamoDB tables for `Reviews` (raw ingested data) and `FlaggedReviews` (reviews identified as suspicious).
-   **API Layer:** AWS API Gateway + AWS Lambda functions (`dashboard_api_lambda`, `detailed_review_api_lambda`, `update_status_api_lambda`) to expose data and functionality to the UI.
-   **UI Layer:** A React.js single-page application (SPA) providing the Trust & Safety Analyst dashboard.

## Core Data Models

Defined in `src/data_models.py`:
-   `Review`: Represents an ingested Amazon product review.
-   `FlaggedReview`: Represents a review that has been flagged as suspicious.

## Technical Decisions & Assumptions

-   **Cloud Provider:** AWS for all infrastructure.
-   **Serverless First:** Prioritize AWS Lambda and managed services.
-   **Event-Driven:** Kinesis streams for real-time data flow.
-   **Database:** DynamoDB for high-throughput and low-latency access.
-   **Frontend:** React.js.
-   **Rules Engine:** Initial rules are static and evaluated per review (using Python expressions for this sprint's pseudocode, which would be replaced by a safer approach in production).
-   **API Security:** Handled via AWS API Gateway.
-   **Analyst ID:** Placeholder used for notes in this sprint, to be integrated with actual authentication in future.

## Sprint Tasks Summary & Implementation Details

### User Story 1: Ingest all new Amazon product reviews

-   **Task 1.1: Design & Implement Review Ingestion Pipeline**
    -   Kinesis (`review_ingestion_stream`) -> Lambda (`review_ingestor_lambda`) -> DynamoDB (`Reviews`) & Kinesis (`abuse_detection_stream`).
-   **Task 1.2: Define & Implement Review Data Model**
    -   Python `Review` class and DynamoDB schema.
-   **Task 1.3: Set Up Real-time Review Processing & Storage**
    -   AWS resource configuration for Kinesis streams and DynamoDB tables.

### User Story 2: Flag reviews that meet predefined suspicious criteria

-   **Task 2.1: Define Initial Suspicious Criteria/Rules**
    -   JSON configuration for rules with Python expressions.
-   **Task 2.2: Implement Rule Engine for Suspicious Criteria**
    -   Kinesis (`abuse_detection_stream`) -> Lambda (`rule_engine_lambda`) evaluates rules.
-   **Task 2.3: Develop Suspicion Scoring & Flagging Mechanism**
    -   `rule_engine_lambda` creates and stores `FlaggedReview` objects in DynamoDB (`FlaggedReviews`).

### User Story 3: View a dashboard of all flagged reviews

-   **Task 3.1: Design Flagged Reviews Dashboard UI**
    -   Wireframes for a tabular dashboard with sorting.
-   **Task 3.2: Develop API for Flagged Reviews Dashboard**
    -   API Gateway (`GET /flagged-reviews`) -> Lambda (`dashboard_api_lambda`) queries `FlaggedReviews` table.
-   **Task 3.3: Implement Flagged Reviews Dashboard Frontend**
    -   React component fetching and displaying data.

### User Story 4: Access a detailed view of a flagged review

-   **Task 4.1: Design Detailed Review View UI**
    -   Wireframes for a dedicated page showing all `FlaggedReview` details, including `reviewSnapshot`.
-   **Task 4.2: Develop API for Detailed Review View**
    -   API Gateway (`GET /flagged-reviews/{flaggedReviewId}`) -> Lambda (`detailed_review_api_lambda`) fetches single `FlaggedReview`.
-   **Task 4.3: Implement Detailed Review View Frontend**
    -   React component fetching and displaying detailed review data.

### User Story 5: Mark a flagged review as legitimate, abusive, or requiring further investigation

-   **Task 5.1: Design UI for Review Status & Notes**
    -   Integration of status selector and notes textarea into the Detailed View UI.
-   **Task 5.2: Implement API for Review Status Update**
    -   API Gateway (`PUT /flagged-reviews/{flaggedReviewId}/status`) -> Lambda (`update_status_api_lambda`) updates `status` and `analystNotes`.
-   **Task 5.3: Integrate Status Update into Detailed View**
    -   React component handles status updates and re-fetches data.
