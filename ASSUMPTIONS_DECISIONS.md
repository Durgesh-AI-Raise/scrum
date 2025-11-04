# ARIS MVP: Assumptions and Technical Decisions (Sprint 1)

This section lists the key assumptions and technical decisions made for this sprint.

**Assumptions:**

*   **AWS Ecosystem:** The entire ARIS system is assumed to be built within the AWS cloud environment, leveraging its services for scalability, reliability, and ease of integration.
*   **Review Event Format:** Incoming raw review events are assumed to be in a consistent JSON format from the source system.
*   **Product Category Availability:** For account activity rules related to product diversity, it is assumed that a `productCategory` can be derived or is available for each `productId` in the `aris-processed-reviews` stream. For the MVP, this might be a simple lookup or a placeholder value if not directly present in the raw event.
*   **Reviewer Account Age (MVP):** For initial account activity detection, a reviewer's `accountCreationDate` is approximated as the date of their first review observed by the ARIS system. This avoids requiring integration with a separate user management system in the MVP.
*   **Network Latency:** Internal AWS service communications (Kinesis to Lambda, Lambda to DynamoDB) are assumed to have low latency.
*   **Security:** Basic IAM roles and policies will be set up. More granular security (e.g., VPC, private endpoints) is out of scope for this MVP but would be considered in future sprints.

**Technical Decisions:**

*   **Real-time Ingestion Technology:** AWS Kinesis Data Streams has been chosen for its high throughput, real-time capabilities, and seamless integration with AWS Lambda.
*   **Compute Model:** AWS Lambda functions are used for all processing modules (ingestion, text analysis, account activity, API service) due to their serverless nature, automatic scaling, and pay-per-execution cost model, which aligns well with an event-driven architecture.
*   **Primary Data Storage:** AWS DynamoDB is selected for persistent storage of all reviews (`aris-all-reviews`) and reviewer activity state (`aris-reviewer-activity`). This decision is based on DynamoDB's high performance, scalability, and managed service benefits for NoSQL data.
*   **Detection Rule Configuration:** For the MVP, abuse detection patterns and rules (for both text and account activity) are embedded directly within their respective Lambda functions as Python dictionaries. In a production system, these would ideally be externally configurable (e.g., S3, DynamoDB configuration table, AWS Systems Manager Parameter Store) to allow for dynamic updates without code deployments.
*   **Confidence Scoring:** A simple additive model is used for `abuseScore`. When multiple detection rules are triggered for a single review, their individual `baseScore` values are summed to provide an overall `abuseScore` for the review.
*   **Dashboard API:** AWS API Gateway is used in conjunction with a Lambda function to provide a scalable and secure API endpoint for the analyst dashboard.
*   **Dashboard Front-end:** Vanilla JavaScript, HTML, and CSS are chosen for the dashboard's front-end for quick development and deployment, focusing on core functionality for the MVP. More complex frameworks can be introduced later if needed.
*   **DynamoDB Global Secondary Index (GSI):** A GSI named `FlaggedReviewsByScoreIndex` on `aris-all-reviews` (PK: `isFlagged`, SK: `abuseScore`) is a critical decision for efficient querying of flagged reviews, allowing the dashboard to quickly retrieve and sort reviews by their abuse likelihood.
*   **Pagination:** DynamoDB's `LastEvaluatedKey` will be used for efficient, token-based pagination in the dashboard API.
