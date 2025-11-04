# ARIS MVP: Implementation Plan (Sprint 1)

This section details the step-by-step plan for each task in the sprint backlog.

**PBI 2: As the system, I need to ingest new review data in real-time**

*   **Task 2.1: Research and select real-time data ingestion technology**
    *   **Plan:** Evaluated Kafka, Kinesis, Google Pub/Sub, AWS SQS/SNS. Given the Amazon Review Integrity System (ARIS) context, **AWS Kinesis Data Streams** is selected due to its native integration with other AWS services, high scalability, and real-time processing capabilities suitable for high-volume data streams.
*   **Task 2.2: Set up data ingestion pipeline infrastructure**
    *   **Plan:**
        1.  Create two AWS Kinesis Data Streams:
            *   `aris-raw-reviews`: For initial raw event ingestion.
            *   `aris-processed-reviews`: For validated and enriched events, acting as the input for detection modules.
        2.  Configure appropriate shard counts for each stream based on estimated initial throughput (e.g., 5 shards each, scalable).
        3.  Set up necessary IAM roles and policies allowing services to `PutRecord` to `aris-raw-reviews` and `GetRecords`/`PutRecord` on `aris-processed-reviews`.
*   **Task 2.3: Develop service to consume review events**
    *   **Plan:**
        1.  Develop an AWS Lambda function, `ReviewIngestionService`, configured as a consumer for the `aris-raw-reviews` Kinesis stream.
        2.  This Lambda will:
            *   Read raw review events (JSON) from `aris-raw-reviews`.
            *   Perform basic schema validation on the review data.
            *   Enrich the review data (e.g., add `productCategory` - for MVP, this could be a simple lookup from a static config or a placeholder).
            *   Add a `processedTimestamp` to the review payload.
            *   Publish the standardized and enriched review event to the `aris-processed-reviews` Kinesis stream.
*   **Task 2.4: Implement basic data storage for ingested reviews**
    *   **Plan:**
        1.  Create an AWS DynamoDB table `aris-all-reviews` with `reviewId` as the Partition Key.
        2.  Modify the `ReviewIngestionService` (from Task 2.3) to also write the processed review event to the `aris-all-reviews` DynamoDB table.
        3.  Initialize `isFlagged` to `false`, `abuseScore` to `0.0`, and `flagDetails` as an empty list for newly ingested reviews.
        4.  Create a Global Secondary Index (GSI) on `aris-all-reviews` named `FlaggedReviewsByScoreIndex` with `isFlagged` as Partition Key and `abuseScore` as Sort Key, to enable efficient querying for flagged reviews.

**PBI 3: As the system, I need to analyze review content for suspicious language patterns**

*   **Task 3.1: Define initial set of suspicious language patterns/keywords**
    *   **Plan:** Define a set of initial suspicious language patterns and keywords. For MVP, these will be embedded as a Python dictionary within the `TextAnalysisModule` Lambda code. Each pattern will include a `ruleId`, `pattern` (regex or keywords list), `type` (`regex` or `keywords_count`), `description`, and `baseScore`.
    *   **Examples:** Generic praise ("absolutely amazing"), repetitive phrases, specific spam terms ("buy now", "discount code").
*   **Task 3.2: Develop text analysis module**
    *   **Plan:**
        1.  Develop an AWS Lambda function, `TextAnalysisModule`, configured as a consumer for the `aris-processed-reviews` Kinesis stream.
        2.  This Lambda will:
            *   Load the defined suspicious language patterns.
            *   Extract `reviewText` from the incoming review event.
            *   Apply each pattern to the `reviewText`.
            *   If a pattern matches, generate a `flagDetail` object (including `type`, `ruleId`, `description`, `score`, `timestamp`).
            *   Update the corresponding review item in the `aris-all-reviews` DynamoDB table:
                *   Set `isFlagged` to `true`.
                *   Append the new `flagDetail` to the `flagDetails` list.
                *   Add the `flag.score` to the existing `abuseScore` (or initialize if first flag).
*   **Task 3.3: Integrate text analysis module with ingestion pipeline**
    *   **Plan:** This is inherently handled by configuring the `TextAnalysisModule` Lambda to subscribe to the `aris-processed-reviews` Kinesis stream. It will automatically receive review events as they are ingested and processed.
*   **Task 3.4: Implement confidence scoring for text analysis flags**
    *   **Plan:**
        1.  Each defined language pattern (Task 3.1) will have an associated `baseScore`.
        2.  When a pattern is matched by the `TextAnalysisModule` (Task 3.2), this `baseScore` will be recorded as the `score` within the `flagDetail` object.
        3.  The `TextAnalysisModule` will update the `abuseScore` in `aris-all-reviews` by adding the newly triggered flag's score to the review's current `abuseScore`. This results in an aggregated confidence score.

**PBI 4: As the system, I need to identify reviews from accounts with unusual activity patterns**

*   **Task 4.1: Define initial rules for unusual account activity**
    *   **Plan:** Define a set of initial rules for detecting unusual account activity. For MVP, these will be embedded as a Python dictionary within the `AccountActivityModule` Lambda code. Each rule will include a `ruleId`, `description`, `baseScore`, and parameters specific to the rule (e.g., `minAccountAgeDays`, `maxReviewsInTimeframe`, `minUniqueProducts`).
    *   **Examples:** High review velocity from a new account, reviewing many unrelated products in a short period.
*   **Task 4.2: Develop module to track and analyze reviewer activity**
    *   **Plan:**
        1.  Create an AWS DynamoDB table `aris-reviewer-activity` with `reviewerId` as the Partition Key.
        2.  Develop an AWS Lambda function, `AccountActivityModule`, configured as a consumer for the `aris-processed-reviews` Kinesis stream.
        3.  This Lambda will:
            *   For each incoming review event, fetch the reviewer's current activity state from `aris-reviewer-activity`. Initialize state if the reviewer is new (using the first review's date as `accountCreationDate` for MVP).
            *   Update the reviewer's activity state (e.g., `totalReviews`, `lastReviewDate`, `recentReviews` list) based on the new review.
            *   Apply the defined account activity rules to the updated state.
            *   If a rule is triggered, generate a `flagDetail` object (including `type`, `ruleId`, `description`, `score`, `timestamp`).
            *   Update the reviewer's activity state in `aris-reviewer-activity`.
            *   Update the corresponding review item in the `aris-all-reviews` DynamoDB table:
                *   Set `isFlagged` to `true`.
                *   Append the new `flagDetail` to the `flagDetails` list.
                *   Add the `flag.score` to the existing `abuseScore`.
*   **Task 4.3: Integrate activity analysis module with ingestion pipeline**
    *   **Plan:** This is inherently handled by configuring the `AccountActivityModule` Lambda to subscribe to the `aris-processed-reviews` Kinesis stream. It will automatically receive review events after they have been processed by the ingestion service.
*   **Task 4.4: Implement confidence scoring for account activity flags**
    *   **Plan:**
        1.  Each defined account activity rule (Task 4.1) will have an associated `baseScore`.
        2.  When a rule is triggered by the `AccountActivityModule` (Task 4.2), this `baseScore` will be recorded as the `score` within the `flagDetail` object.
        3.  The `AccountActivityModule` will update the `abuseScore` in `aris-all-reviews` by adding the newly triggered flag's score to the review's current `abuseScore`.

**PBI 1: As a Trust & Safety Analyst, I need a dashboard of potentially abusive reviews**

*   **Task 1.1: Design Dashboard UI/UX for flagged reviews**
    *   **Plan:** Design a simple, functional web page layout.
        *   **Key Elements:** A tabular display for flagged reviews.
        *   **Data Fields per Row:** Review ID, Product ID, Reviewer ID, Abuse Score, Review Text (truncated), Flag Reasons (list of rule IDs/descriptions), Review Date.
        *   **Interaction Flows:** Input fields for filtering by minimum `abuseScore`, dropdowns for sorting by `abuseScore` or `reviewDate`, and pagination buttons (Next/Previous).
*   **Task 1.2: Develop API endpoint to fetch flagged reviews for Dashboard**
    *   **Plan:**
        1.  Create an AWS API Gateway REST API endpoint (e.g., `/flagged-reviews`).
        2.  Develop an AWS Lambda function, `DashboardApiService`, triggered by this API Gateway endpoint.
        3.  This Lambda will:
            *   Parse query parameters from the API request (e.g., `minAbuseScore`, `sortBy`, `sortOrder`, `limit`, `lastKey` for pagination).
            *   Query the `aris-all-reviews` DynamoDB table using the `FlaggedReviewsByScoreIndex` GSI.
            *   Filter results based on `isFlagged = true` and `minAbuseScore`.
            *   Sort the results based on `abuseScore` (natively supported by GSI) or `reviewDate` (might require a secondary sort or additional GSI if not efficient).
            *   Implement pagination using DynamoDB's `LastEvaluatedKey`.
            *   Return a JSON response containing the list of flagged reviews and a `nextToken` for subsequent pagination requests.
*   **Task 1.3: Develop front-end component for Dashboard**
    *   **Plan:**
        1.  Create a static HTML file, `dashboard_frontend.html`.
        2.  Use vanilla JavaScript (or a lightweight framework if time permits) to build the client-side logic.
        3.  The HTML will define the table structure and UI controls (filters, sorting, pagination buttons).
        4.  The JavaScript will be responsible for:
            *   Making `fetch` requests to the `DashboardApiService` endpoint.
            *   Parsing the JSON response.
            *   Dynamically rendering the flagged reviews into the HTML table.
            *   Managing UI state for pagination and filtering.
*   **Task 1.4: Integrate front-end with API for Dashboard**
    *   **Plan:**
        1.  Configure the `dashboard_frontend.html` JavaScript to make `fetch` requests to the deployed API Gateway endpoint URL (from Task 1.2).
        2.  Ensure CORS (Cross-Origin Resource Sharing) is properly configured on the API Gateway to allow the front-end (hosted on a different domain, e.g., S3) to access the API.
        3.  Implement error handling and loading indicators in the front-end for a better user experience.
*   **Task 1.5: Implement basic sorting and filtering on Dashboard**
    *   **Plan:**
        1.  Add input fields (e.g., `<input type="number">` for `minAbuseScore`, `<select>` for `sortBy` and `sortOrder`) to `dashboard_frontend.html`.
        2.  Modify the front-end JavaScript to read values from these inputs and pass them as query parameters to the `DashboardApiService` API.
        3.  The `DashboardApiService` Lambda will utilize these parameters in its DynamoDB query (`KeyConditionExpression` for `minAbuseScore`, `ScanIndexForward` for `sortOrder`).
