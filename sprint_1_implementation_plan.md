# Sprint 1: Implementation Plan for Amazon Review Integrity Shield (ARIS)

## Sprint Goal

Establish the foundational real-time data ingestion pipeline and implement initial detection capabilities for fake positive amplification, fake negative sabotage, and content moderation, enabling Review Integrity Analysts to begin investigating potential review abuse.

---

## Overall Architecture, Data Models, Assumptions, and Technical Decisions

Please refer to `architecture/overall_architecture.md` for a high-level overview of the ARIS system architecture. The following details build upon that foundation.

---

## Detailed Implementation Plan for Each Task

### User Story: Real-time Data Ingestion

**SPRINT 1 - Task 1.1: Research and select real-time data streaming technology (Estimated Hours: 8)**

*   **Implementation Plan:** Based on the overall architecture, AWS Kinesis Data Streams has been selected for real-time data streaming due to its scalability, durability, and strong integration with other AWS services. No further research is required for this sprint.
*   **Data Models:** N/A.
*   **Assumptions/Technical Decisions:**
    *   **Decision:** AWS Kinesis Data Streams is the chosen technology.
    *   **Assumption:** Review data will be available as a continuous stream of events.
    *   **Assumption:** Data payload size will be within Kinesis limits (1MB per record).

**SPRINT 1 - Task 1.2: Set up and configure data streaming pipeline (Estimated Hours: 16)**

*   **Implementation Plan:**
    1.  Create a Kinesis Data Stream named `ARIS_ReviewStream` with an initial shard count (e.g., 3-5 shards), configurable based on estimated peak ingress data volume.
    2.  Configure necessary AWS IAM roles and policies for data producers (e.g., `IngestionProducerLambda`) and consumers (e.g., `FakePositiveDetectorLambda`, `ContentModerationLambda`) to interact with `ARIS_ReviewStream` with least privilege.
    3.  Set up basic AWS CloudWatch monitoring and alarms for the Kinesis stream, tracking metrics such as `IncomingBytes`, `PutRecord.Success`, and `ReadProvisionedThroughputExceeded`.
*   **Data Models:**
    *   `ARIS_ReviewStream`: Kinesis Data Stream. Each record will contain:
        *   `PartitionKey`: A string identifier (e.g., `product_id` or `user_id`) used by Kinesis to group related data and ensure ordering within a shard.
        *   `Data`: The raw review payload (JSON string, Base64 encoded).
*   **Assumptions/Technical Decisions:**
    *   **Decision:** Initial Kinesis shard count will be a reasonable starting point and scaled as needed.
    *   **Assumption:** Data producers will generate appropriate `PartitionKey` values to distribute load effectively and maintain ordering for related data.

**SPRINT 1 - Task 1.3: Develop data ingestion module (Estimated Hours: 20)**

*   **Implementation Plan:**
    1.  Develop an AWS Lambda function, `IngestionProducerLambda`, which will serve as the entry point for new review data. This Lambda will receive review data (e.g., via API Gateway, direct invocation from another service).
    2.  Implement robust input validation for incoming review data (e.g., check for mandatory fields like `review_id`, `product_id`, `user_id`, `rating`, `review_text`).
    3.  Standardize the review data format (e.g., ensure date fields are ISO 8601).
    4.  Utilize the Boto3 Kinesis client to `put_records` into the `ARIS_ReviewStream`. Implement batching for efficiency and error handling for failed record puts.
*   **Data Models:**
    *   **Incoming Review Data (Example JSON):**
        ```json
        {
            "review_id": "R1234567890",
            "product_id": "P0987654321",
            "user_id": "U1122334455",
            "rating": 5,
            "review_title": "Absolutely fantastic!",
            "review_text": "I absolutely love this product, it exceeded all my expectations. Highly recommended!",
            "review_date": "2023-10-26T10:00:00Z",
            "user_country": "US",
            "account_creation_date": "2023-09-01T00:00:00Z"
        }
        ```
    *   **Kinesis Record Data:** The JSON string above, base64 encoded, sent as the `Data` field in Kinesis records.
*   **Assumptions/Technical Decisions:**
    *   **Decision:** `IngestionProducerLambda` will be implemented in Python.
    *   **Technical Decision:** Review data is assumed to be in a JSON format.
    *   **Assumption:** The upstream source system will trigger `IngestionProducerLambda` (e.g., via an HTTP POST to an API Gateway endpoint, or by placing messages in an SQS queue that triggers the Lambda).

**SPRINT 1 - Task 1.4: Implement data storage solution for raw reviews (Estimated Hours: 12)**

*   **Implementation Plan:**
    1.  Set up an AWS Kinesis Firehose delivery stream named `ARIS_ReviewFirehose`.
    2.  Configure `ARIS_ReviewFirehose` to consume data directly from `ARIS_ReviewStream`.
    3.  Configure `ARIS_ReviewFirehose` to deliver the data to an S3 bucket named `aris-raw-reviews`.
    4.  Define S3 bucket policies, including encryption, versioning (optional), and lifecycle management rules to transition older data to Glacier or delete it based on retention policies.
    5.  Configure Firehose to use dynamic partitioning for S3 objects (e.g., `raw-reviews/yyyy/MM/dd/HH/`).
*   **Data Models:**
    *   `aris-raw-reviews` S3 Bucket: Stores raw review data, typically as JSON files (JSON Lines).
    *   S3 Object Key Format: `raw-reviews/yyyy/MM/dd/HH/review_batch-<timestamp>-<uuid>.json` (Firehose automatically names files).
*   **Assumptions/Technical Decisions:**
    *   **Decision:** Kinesis Firehose is chosen for its fully managed nature and seamless integration with Kinesis Streams and S3, simplifying the creation of a data lake for raw reviews.
    *   **Decision:** S3 is used for cost-effective, durable, and scalable long-term storage of raw reviews.
    *   **Technical Decision:** Raw data will be stored as JSON Lines or individual JSON objects within S3 files, suitable for future analytics with Athena/Glue.

**SPRINT 1 - Task 1.5: Write tests for data ingestion pipeline (Estimated Hours: 10)**

*   **Implementation Plan:**
    1.  **Unit Tests:** Develop unit tests for `IngestionProducerLambda`'s logic. Mock the Boto3 Kinesis client to verify that `put_records` is called with the correct data and `PartitionKey`. Test input validation and error handling.
    2.  **Integration Tests:**
        *   Test the end-to-end flow by sending a sample review event to the `IngestionProducerLambda` (e.g., using `lambda.invoke`).
        *   Verify that the record appears in `ARIS_ReviewStream` (e.g., by consuming from Kinesis with a test consumer, though this can be tricky for real-time).
        *   Verify that the raw review data eventually lands in the `aris-raw-reviews` S3 bucket via Kinesis Firehose. This may require waiting for Firehose's buffering interval.
*   **Assumptions/Technical Decisions:**
    *   **Tools:** `pytest` for Python unit tests, `moto` library for mocking AWS services (Kinesis, Lambda). For integration tests, a dedicated non-production AWS environment or `LocalStack` might be used.

---

### User Story: Fake Positive Amplification Detection

**SPRINT 1 - Task 2.1: Define rules for fake positive amplification detection (Estimated Hours: 8)**

*   **Implementation Plan:** Collaborate closely with Review Integrity Analysts to establish a foundational set of rule-based heuristics. These rules will be implemented directly in code for this sprint.
*   **Data Models:** Rules will be implicitly defined within the `FakePositiveDetectorLambda`'s Python code for this initial implementation. In future sprints, these could be externalized to a configuration store (e.g., AWS AppConfig, DynamoDB, S3 JSON file).
*   **Assumptions/Technical Decisions:**
    *   **Decision:** Initial detection will be entirely rule-based, focusing on immediately actionable patterns.
    *   **Example Rules (for Sprint 1):**
        *   **Rule 1: New Account, High Rating:** A review with a 5-star rating submitted by an account created less than `X` days ago (e.g., 30 days).
        *   **Rule 2: Short, Generic Positive Text:** A 5-star review with very short text (e.g., < 15 words) containing only generic positive phrases (e.g., "Great product!", "Love it!").
        *   **(Future Sophistication):** Detecting multiple such reviews for the *same product* from *different new accounts* within a *short time window* will require stateful processing (e.g., Kinesis Data Analytics or custom state management in DynamoDB), which is out of scope for Sprint 1 but will be considered in future iterations.
*   **Assumptions/Technical Decisions:**
    *   **Decision:** Rules for this sprint will focus on individual review characteristics rather than aggregated patterns across multiple reviews.

**SPRINT 1 - Task 2.2: Develop model/engine for fake positive amplification (Estimated Hours: 24)**

*   **Implementation Plan:**
    1.  Create an AWS Lambda function, `FakePositiveDetectorLambda`, configured to consume records from `ARIS_ReviewStream`.
    2.  Implement the defined rule set within this Lambda. Each incoming review will be evaluated against these rules.
    3.  If a review triggers one or more rules, a `FlaggedReview` object will be created.
    4.  This `FlaggedReview` object will then be persisted to the `ARIS_FlaggedReviews` DynamoDB table.
*   **Data Models:**
    *   **`ARIS_FlaggedReviews` DynamoDB Table (Example Item):**
        ```json
        {
            "flag_id": "FP_R1234567890_20231026_001", // Partition Key: Composite of type, review_id, date, sequence
            "review_id": "R1234567890",              // Sort Key (or part of PK): For efficient querying related to a review
            "product_id": "P0987654321",
            "user_id": "U1122334455",
            "rating": 5,
            "review_text": "I absolutely love this product...",
            "flag_type": "FakePositiveAmplification",
            "detection_rule": "Rule: New Account (<30 days) + 5-star rating",
            "flag_timestamp": "2023-10-26T10:05:00Z",
            "status": "PENDING_REVIEW",             // Initial status for analyst review
            "metadata": {                           // Additional context for analysts
                "account_creation_date": "2023-09-01T00:00:00Z",
                "review_length_words": 12
            }
        }
        ```
*   **Assumptions/Technical Decisions:**
    *   **Decision:** The detection engine will be implemented as a Python Lambda function.
    *   **Technical Decision:** DynamoDB is chosen for storing flagged reviews due to its low-latency read/write capabilities, which are crucial for analysts.
    *   **Assumption:** The incoming review data structure from Kinesis is consistent.

**SPRINT 1 - Task 2.3: Integrate fake positive amplification model with data stream (Estimated Hours: 16)**

*   **Implementation Plan:**
    1.  Configure an AWS Lambda Event Source Mapping to connect `FakePositiveDetectorLambda` to `ARIS_ReviewStream`, ensuring real-time processing of new review data.
    2.  Grant `FakePositiveDetectorLambda` the necessary IAM permissions to read from `ARIS_ReviewStream` and write to `ARIS_FlaggedReviews` DynamoDB table.
    3.  Configure Lambda batching (e.g., `BatchSize`, `BatchWindow`) for efficient consumption of Kinesis records, allowing it to process multiple reviews in a single invocation.
*   **Assumptions/Technical Decisions:**
    *   **Decision:** Direct integration via Lambda Event Source Mapping provides a scalable and serverless consumption model.

**SPRINT 1 - Task 2.4: Implement storage for flagged fake positive reviews (Estimated Hours: 12)**

*   **Implementation Plan:**
    1.  Create an AWS DynamoDB table named `ARIS_FlaggedReviews`.
    2.  Define the primary key: `flag_id` as the Partition Key and `review_id` as the Sort Key. This allows for unique identification of each flag and efficient retrieval of all flags related to a specific review.
    3.  Configure DynamoDB capacity mode (On-Demand for flexibility or Provisioned for predictable workloads and cost savings if usage patterns are well-understood).
    4.  Consider creating Global Secondary Indexes (GSIs) for common query patterns by Review Integrity Analysts (e.g., querying by `product_id`, `user_id`, or `flag_type`). For Sprint 1, this might be deferred if not immediately critical for MVP.
*   **Data Models:** Refer to the `ARIS_FlaggedReviews` DynamoDB Table example item in Task 2.2.
*   **Assumptions/Technical Decisions:**
    *   **Decision:** DynamoDB is the chosen storage for flagged reviews due to its suitability for high-throughput, low-latency key-value access patterns.
    *   **Technical Decision:** The primary key design will be optimized for the most frequent access patterns of Review Integrity Analysts.

**SPRINT 1 - Task 2.5: Write tests for fake positive amplification detection (Estimated Hours: 10)**

*   **Implementation Plan:**
    1.  **Unit Tests:** Develop unit tests for the rule evaluation logic within `FakePositiveDetectorLambda`. Mock the Kinesis event structure and the Boto3 DynamoDB client to verify correct flagging logic and `put_item` calls. Test various scenarios, including reviews that should be flagged and those that should not.
    2.  **Integration Tests:**
        *   Send a sample review specifically crafted to trigger a fake positive amplification rule to `ARIS_ReviewStream` (e.g., by invoking `IngestionProducerLambda`).
        *   Verify that `FakePositiveDetectorLambda` processes the review and successfully inserts a corresponding `FlaggedReview` item into the `ARIS_FlaggedReviews` DynamoDB table.
*   **Assumptions/Technical Decisions:**
    *   **Tools:** `pytest` and `moto` (for mocking AWS services).

---

### User Story: Fake Negative Sabotage Detection

**SPRINT 1 - Task 3.1: Define rules for fake negative sabotage detection (Estimated Hours: 8)**

*   **Implementation Plan:** Similar to fake positive, define initial rule-based heuristics in collaboration with Review Integrity Analysts.
*   **Data Models:** Rules will be embedded in `FakeNegativeDetectorLambda`'s code initially.
*   **Assumptions/Technical Decisions:**
    *   **Decision:** Initial detection is rule-based.
    *   **Example Rules (for Sprint 1):**
        *   **Rule 1: New Account, Low Rating, Competitor Product:** A review with a 1-star rating from an account created less than `X` days ago for a product identified as a competitor's product. (For this sprint, competitor products might be hardcoded or retrieved from a simple configuration).
        *   **Rule 2: Short, Generic Negative Text:** A 1-star review with very short text (e.g., < 15 words) containing only generic negative phrases (e.g., "Terrible product!", "Waste of money!").
        *   **(Future Sophistication):** Detecting coordinated attacks on competitor products will require stateful analysis beyond individual review characteristics.
*   **Assumptions/Technical Decisions:**
    *   **Assumption:** For Rule 1, a simplified mechanism for identifying competitor products will be used (e.g., a lookup against a small, pre-defined list of `product_id`s for testing purposes).

**SPRINT 1 - Task 3.2: Develop model/engine for fake negative sabotage (Estimated Hours: 24)**

*   **Implementation Plan:**
    1.  Create an AWS Lambda function, `FakeNegativeDetectorLambda`, configured to consume records from `ARIS_ReviewStream`.
    2.  Implement the defined rule set within this Lambda, evaluating each incoming review.
    3.  If a review triggers one or more fake negative sabotage rules, a `FlaggedReview` object will be created.
    4.  This `FlaggedReview` object will be persisted to the `ARIS_FlaggedReviews` DynamoDB table.
*   **Data Models:**
    *   **`ARIS_FlaggedReviews` DynamoDB Table:** Same schema as for fake positive flags, but with `flag_type: "FakeNegativeSabotage"`.
*   **Assumptions/Technical Decisions:**
    *   **Decision:** Python Lambda function for the detection engine.

**SPRINT 1 - Task 3.3: Integrate fake negative sabotage model with data stream (Estimated Hours: 16)**

*   **Implementation Plan:**
    1.  Configure an AWS Lambda Event Source Mapping to connect `FakeNegativeDetectorLambda` to `ARIS_ReviewStream`.
    2.  Grant `FakeNegativeDetectorLambda` the necessary IAM permissions to read from `ARIS_ReviewStream` and write to `ARIS_FlaggedReviews` DynamoDB table.
    3.  Configure Lambda batching for efficient Kinesis record processing.
*   **Assumptions/Technical Decisions:**
    *   **Decision:** Direct integration via Lambda Event Source Mapping.

**SPRINT 1 - Task 3.4: Write tests for fake negative sabotage detection (Estimated Hours: 10)**

*   **Implementation Plan:**
    1.  **Unit Tests:** Develop unit tests for the rule evaluation logic within `FakeNegativeDetectorLambda`, mocking Kinesis events and DynamoDB interactions.
    2.  **Integration Tests:**
        *   Send a sample review designed to trigger a fake negative sabotage rule to `ARIS_ReviewStream`.
        *   Verify that `FakeNegativeDetectorLambda` processes it and inserts a `FlaggedReview` item into `ARIS_FlaggedReviews`.
*   **Assumptions/Technical Decisions:**
    *   **Tools:** `pytest` and `moto`.

---

### User Story: Content Moderation (Spam, Irrelevant, Hate Speech)

**SPRINT 1 - Task 4.1: Research NLP libraries for content moderation (Estimated Hours: 12)**

*   **Implementation Plan:** Research will focus on immediately available and easily integratable solutions for a first sprint MVP.
    *   **Selection Criteria:** Ease of deployment within AWS Lambda, cost-effectiveness, and ability to address basic spam/hate speech/irrelevance.
    *   **Conclusion:** AWS Comprehend will be leveraged for its managed NLP capabilities (e.g., sentiment analysis, language detection, basic entity recognition) which can assist in flagging. For direct "hate speech" or "spam" classification, a combination of keyword spotting (using Python's `re` module) and Comprehend's general text analysis will be used for this initial sprint. More advanced pre-trained models (e.g., from Hugging Face) or custom Comprehend models are out of scope for Sprint 1 due to complexity.
*   **Assumptions/Technical Decisions:**
    *   **Decision:** AWS Comprehend is the primary managed NLP service for this sprint. Python's built-in string/regex capabilities will handle basic keyword spotting.
    *   **Assumption:** AWS Comprehend's free tier or initial usage will be sufficient for sprint 1's volume.

**SPRINT 1 - Task 4.2: Develop content moderation module (Estimated Hours: 28)**

*   **Implementation Plan:**
    1.  Create an AWS Lambda function, `ContentModerationLambda`, configured to consume records from `ARIS_ReviewStream`.
    2.  Implement content moderation logic using the selected tools:
        *   **Spam/Irrelevant Content:** Implement keyword spotting (using `re` for common spam phrases), review length checks (very short/long reviews), and basic character pattern analysis (e.g., excessive non-alphanumeric characters).
        *   **Hate Speech/Toxicity:** Integrate with AWS Comprehend to detect dominant language and sentiment. Combine sentiment analysis (e.g., extremely negative sentiment combined with suspicious keywords) and keyword spotting for known hate speech terms. (Note: Full, robust hate speech detection is a complex ML problem and will be a multi-sprint effort; this sprint focuses on initial, rule-based flagging).
        *   **Illegal Content:** Basic keyword spotting for terms associated with illegal activities.
    3.  Define rules for flagging based on the output of these analyses.
    4.  If a review triggers content moderation rules, create a `FlaggedReview` object (with `flag_type: "ContentModeration"`) and persist it to the `ARIS_FlaggedReviews` DynamoDB table.
*   **Data Models:**
    *   **`ARIS_FlaggedReviews` DynamoDB Table:** Same schema, with `flag_type: "ContentModeration"`. `detection_rule` will specify which content moderation criteria were met.
*   **Assumptions/Technical Decisions:**
    *   **Decision:** The content moderation logic will be implemented as a Python Lambda function.
    *   **Technical Decision:** For this sprint, hate speech detection relies on a combination of keyword matching and basic sentiment analysis from AWS Comprehend.

**SPRINT 1 - Task 4.3: Integrate content moderation module with data stream (Estimated Hours: 16)**

*   **Implementation Plan:**
    1.  Configure an AWS Lambda Event Source Mapping to connect `ContentModerationLambda` to `ARIS_ReviewStream`.
    2.  Grant `ContentModerationLambda` the necessary IAM permissions to read from `ARIS_ReviewStream`, interact with AWS Comprehend, and write to `ARIS_FlaggedReviews` DynamoDB table.
    3.  Configure Lambda batching for efficient Kinesis record processing.
*   **Assumptions/Technical Decisions:**
    *   **Decision:** Direct integration via Lambda Event Source Mapping.

**SPRINT 1 - Task 4.4: Write tests for content moderation detection (Estimated Hours: 10)**

*   **Implementation Plan:**
    1.  **Unit Tests:** Develop unit tests for the content moderation logic within `ContentModerationLambda`, mocking Kinesis events and AWS Comprehend API calls (using `moto` or explicit mock objects for Comprehend responses). Test various review texts designed to trigger spam, irrelevant content, or hate speech rules.
    2.  **Integration Tests:**
        *   Send a sample review containing spam, irrelevant content, or hate speech keywords to `ARIS_ReviewStream`.
        *   Verify that `ContentModerationLambda` processes it and inserts a `FlaggedReview` item into `ARIS_FlaggedReviews`.
*   **Assumptions/Technical Decisions:**
    *   **Tools:** `pytest` and `moto`.

---

## Code Snippets (Pseudocode for Key Components)

The following pseudocode outlines the core logic for the Lambda functions. Actual implementation will involve AWS SDK (Boto3) calls and proper error handling.

### 1. `IngestionProducerLambda` Pseudocode (`src/ingestion_producer_lambda.py`)

```python
import json
import os
import boto3
import base64
from datetime import datetime

# Environment variables for configuration
KINESIS_STREAM_NAME = os.environ.get("KINESIS_STREAM_NAME", "ARIS_ReviewStream")
kinesis_client = boto3.client("kinesis")

def lambda_handler(event, context):
    """
    Handles incoming review data, performs basic validation, and pushes to Kinesis.
    Event structure is assumed to be a dictionary with a 'reviews' key (list of review dicts)
    or a single review dictionary directly.
    """
    records_to_put = []
    
    # Adapt to various potential input event structures (e.g., single record vs batch)
    reviews_payload = event.get("reviews", []) 
    if not reviews_payload and isinstance(event, dict) and "review_id" in event:
        reviews_payload = [event] # Handle a single review directly if not in a 'reviews' list

    for review in reviews_payload:
        # Basic input validation: check for essential fields
        if not all(key in review for key in ["review_id", "product_id", "user_id", "rating", "review_text"]):
            print(f"Skipping invalid review due to missing essential fields: {review.get('review_id', 'N/A')}")
            continue
        
        # Standardize date formats if present, add current time if missing for processing
        if "review_date" not in review:
            review["review_date"] = datetime.utcnow().isoformat() + "Z"
        if "account_creation_date" not in review:
             # For new accounts without creation date, assume recent (e.g., for testing new account rules)
             review["account_creation_date"] = (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z" 
        
        # Use product_id as PartitionKey for Kinesis to ensure related reviews go to the same shard
        # This can be beneficial for future stateful processing needs.
        partition_key = review.get("product_id", "default_partition_key") 
        
        records_to_put.append({
            "Data": json.dumps(review).encode("utf-8"), # Kinesis Data must be bytes
            "PartitionKey": partition_key
        })

    if records_to_put:
        try:
            # put_records supports sending multiple records in one API call
            response = kinesis_client.put_records(
                Records=records_to_put,
                StreamName=KINESIS_STREAM_NAME
            )
            print(f"Successfully put {len(records_to_put)} records to Kinesis. Response: {response}")
            
            # Handle potential partial failures (e.g., throttling on specific shards)
            if response.get("FailedRecordCount", 0) > 0:
                print(f"Warning: {response['FailedRecordCount']} records failed to put to Kinesis.")
                # Detailed logging of failed records for debugging/retries in a real system
            
            return {
                "statusCode": 200,
                "body": json.dumps({"message": f"Processed {len(reviews_payload)} reviews. Put {len(records_to_put)} to Kinesis."}) 
            }
        except Exception as e:
            print(f"Error putting records to Kinesis: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"message": f"Error putting records to Kinesis: {str(e)}"})
            }
    else:
        print("No valid records received to put to Kinesis.")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No valid reviews received."})
        }

```

### 2. `FakePositiveDetectorLambda` Pseudocode (`src/fake_positive_detector_lambda.py`)

```python
import json
import os
import boto3
import base64
from datetime import datetime, timedelta

# Environment variables for configuration
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "ARIS_FlaggedReviews")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

ACCOUNT_CREATION_DATE_THRESHOLD_DAYS = 30 # For 'new account' rule
GENERIC_POSITIVE_KEYWORDS = ["great product", "love it", "highly recommend", "amazing", "fantastic", "best ever"]
REVIEW_TEXT_WORD_COUNT_THRESHOLD = 15 # For 'short review' rule

def is_new_account(account_creation_date_str, threshold_days):
    """Checks if an account was created within the last 'threshold_days'."""
    try:
        # Handle different ISO format variations, especially 'Z' for UTC
        creation_date = datetime.fromisoformat(account_creation_date_str.replace('Z', '+00:00'))
        # Compare with current UTC time
        return (datetime.now(creation_date.tzinfo) - creation_date).days < threshold_days
    except (ValueError, TypeError):
        print(f"Invalid account_creation_date format: {account_creation_date_str}")
        return False # Treat as not a new account if date is invalid

def contains_generic_positive_phrases(review_text, keywords):
    """Checks if review text contains generic positive phrases."""
    text_lower = review_text.lower()
    return any(keyword in text_lower for keyword in keywords)

def lambda_handler(event, context):
    """
    Processes Kinesis records to detect fake positive amplification patterns.
    """
    flagged_items = []
    
    for record in event["Records"]:
        try:
            # Kinesis data is base64 encoded
            payload = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            review = json.loads(payload)

            review_id = review.get("review_id")
            product_id = review.get("product_id")
            user_id = review.get("user_id")
            rating = review.get("rating")
            review_text = review.get("review_text", "")
            account_creation_date = review.get("account_creation_date")
            
            flagged = False
            detection_rules = []

            # --- Rule 1: New Account + High Rating (e.g., 5-star) ---
            if rating == 5 and account_creation_date and \
               is_new_account(account_creation_date, ACCOUNT_CREATION_DATE_THRESHOLD_DAYS):
                flagged = True
                detection_rules.append(f"Rule: New Account (<{ACCOUNT_CREATION_DATE_THRESHOLD_DAYS} days) + 5-star rating")

            # --- Rule 2: Short, Generic Positive Review from a New-ish Account ---
            # This rule aims to catch low-effort positive reviews often associated with manipulation.
            # We use a slightly broader window for 'new-ish' account here for potential overlap.
            if not flagged and rating == 5 and len(review_text.split()) < REVIEW_TEXT_WORD_COUNT_THRESHOLD and \
               contains_generic_positive_phrases(review_text, GENERIC_POSITIVE_KEYWORDS):
                # Add an account age check to make this more specific to amplification context
                if account_creation_date and is_new_account(account_creation_date, ACCOUNT_CREATION_DATE_THRESHOLD_DAYS * 2): # e.g., <60 days
                    flagged = True
                    detection_rules.append(f"Rule: Short, Generic 5-star review from New-ish Account (<{ACCOUNT_CREATION_DATE_THRESHOLD_DAYS * 2} days)")
            
            if flagged:
                flag_timestamp = datetime.utcnow().isoformat() + "Z"
                # Create a unique flag_id using review_id and timestamp for potential multiple flags per review
                flag_id = f"FP_{review_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}" 

                flagged_item = {
                    "flag_id": flag_id,
                    "review_id": review_id,
                    "product_id": product_id,
                    "user_id": user_id,
                    "rating": rating,
                    "review_text": review_text,
                    "flag_type": "FakePositiveAmplification",
                    "detection_rule": "; ".join(detection_rules),
                    "flag_timestamp": flag_timestamp,
                    "status": "PENDING_REVIEW", # Initial status for analyst review
                    "metadata": { # Store additional context for analysts
                        "account_creation_date": account_creation_date,
                        "review_length_words": len(review_text.split()),
                    }
                }
                flagged_items.append(flagged_item)

        except Exception as e:
            print(f"Error processing Kinesis record: {e}. Record: {record}")
    
    if flagged_items:
        # Use DynamoDB's batch_writer for efficient writing of multiple items
        with table.batch_writer() as batch:
            for item in flagged_items:
                batch.put_item(Item=item)
        print(f"Successfully flagged {len(flagged_items)} reviews for fake positive amplification.")
    
    return {
        "statusCode": 200,
        "body": json.dumps(f"Processed {len(event['Records'])} Kinesis records. Flagged {len(flagged_items)} reviews.")
    }
```

### 3. `FakeNegativeDetectorLambda` Pseudocode (`src/fake_negative_detector_lambda.py`)

```python
import json
import os
import boto3
import base64
from datetime import datetime, timedelta

# Environment variables for configuration
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "ARIS_FlaggedReviews")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

ACCOUNT_CREATION_DATE_THRESHOLD_DAYS = 30 # For 'new account' rule
# Placeholder for competitor product IDs - in a real system, this would come from a configuration store
COMPETITOR_PRODUCT_IDS = {"P_COMP_001", "P_COMP_002", "P_COMP_003"} 
GENERIC_NEGATIVE_KEYWORDS = ["terrible product", "waste of money", "horrible", "awful", "don't buy", "regret purchase"]
REVIEW_TEXT_WORD_COUNT_THRESHOLD = 15 # For 'short review' rule

def is_new_account(account_creation_date_str, threshold_days):
    """Checks if an account was created within the last 'threshold_days'."""
    try:
        creation_date = datetime.fromisoformat(account_creation_date_str.replace('Z', '+00:00'))
        return (datetime.now(creation_date.tzinfo) - creation_date).days < threshold_days
    except (ValueError, TypeError):
        return False

def contains_generic_negative_phrases(review_text, keywords):
    """Checks if review text contains generic negative phrases."""
    text_lower = review_text.lower()
    return any(keyword in text_lower for keyword in keywords)

def lambda_handler(event, context):
    """
    Processes Kinesis records to detect fake negative sabotage patterns.
    """
    flagged_items = []
    
    for record in event["Records"]:
        try:
            payload = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            review = json.loads(payload)

            review_id = review.get("review_id")
            product_id = review.get("product_id")
            user_id = review.get("user_id")
            rating = review.get("rating")
            review_text = review.get("review_text", "")
            account_creation_date = review.get("account_creation_date")
            
            flagged = False
            detection_rules = []

            # --- Rule 1: New Account + Low Rating (e.g., 1-star) + Targeting Competitor Product ---
            if rating == 1 and account_creation_date and \
               is_new_account(account_creation_date, ACCOUNT_CREATION_DATE_THRESHOLD_DAYS) and \
               product_id in COMPETITOR_PRODUCT_IDS:
                flagged = True
                detection_rules.append(f"Rule: New Account (<{ACCOUNT_CREATION_DATE_THRESHOLD_DAYS} days) + 1-star rating + Competitor Product")

            # --- Rule 2: Short, Generic Negative Review from a New-ish Account ---
            if not flagged and rating == 1 and len(review_text.split()) < REVIEW_TEXT_WORD_COUNT_THRESHOLD and \
               contains_generic_negative_phrases(review_text, GENERIC_NEGATIVE_KEYWORDS):
                # Add an account age check for context
                if account_creation_date and is_new_account(account_creation_date, ACCOUNT_CREATION_DATE_THRESHOLD_DAYS * 2):
                    flagged = True
                    detection_rules.append(f"Rule: Short, Generic 1-star review from New-ish Account (<{ACCOUNT_CREATION_DATE_THRESHOLD_DAYS * 2} days)")
            
            if flagged:
                flag_timestamp = datetime.utcnow().isoformat() + "Z"
                flag_id = f"FN_{review_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}" 

                flagged_item = {
                    "flag_id": flag_id,
                    "review_id": review_id,
                    "product_id": product_id,
                    "user_id": user_id,
                    "rating": rating,
                    "review_text": review_text,
                    "flag_type": "FakeNegativeSabotage",
                    "detection_rule": "; ".join(detection_rules),
                    "flag_timestamp": flag_timestamp,
                    "status": "PENDING_REVIEW",
                    "metadata": {
                        "account_creation_date": account_creation_date,
                        "review_length_words": len(review_text.split()),
                    }
                }
                flagged_items.append(flagged_item)

        except Exception as e:
            print(f"Error processing Kinesis record: {e}. Record: {record}")
    
    if flagged_items:
        with table.batch_writer() as batch:
            for item in flagged_items:
                batch.put_item(Item=item)
        print(f"Successfully flagged {len(flagged_items)} reviews for fake negative sabotage.")
    
    return {
        "statusCode": 200,
        "body": json.dumps(f"Processed {len(event['Records'])} Kinesis records. Flagged {len(flagged_items)} reviews.")
    }
```

### 4. `ContentModerationLambda` Pseudocode (`src/content_moderation_lambda.py`)

```python
import json
import os
import boto3
import base64
import re # For simple regex based keyword spotting
from datetime import datetime

# Environment variables for configuration
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "ARIS_FlaggedReviews")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

comprehend_client = boto3.client("comprehend")

# Keyword lists for initial content moderation rules (can be externalized to config)
SPAM_KEYWORDS = [
    r"\bfree\s+money\b", r"\bget\s+rich\s+quick\b", r"\bbuy\s+now\b", r"\bdiscount\s+code\b",
    r"\bclick\s+here\b", r"\bcoupon\s+code\b", r"\bwin\s+prize\b", r"\bdeal\s+of\s+the\s+day\b",
    r"\bloan\s+offer\b", r"\binvestment\s+opportunity\b"
]
HATE_SPEECH_KEYWORDS = [ # Highly simplified and example-based, needs careful and continuous tuning
    r"\bkiller\b", r"\bhate\b", r"\battack\b", r"\b[racial_slur]\b", r"\b[gender_slur]\b",
    r"\bidiot\b", r"\bstupid\b", r"\bdisgusting\b", r"\bfreak\b" # Context is crucial for these
]
ILLEGAL_KEYWORDS = [
    r"\bdrugs\b", r"\bweapon\b", r"\bfirearm\b", r"\billegal\b", r"\bbomb\b", r"\bexploit\b",
    r"\bchild\s+abuse\b"
]
IRRELEVANT_TEXT_THRESHOLD = 10 # Minimum word count for relevant reviews

def contains_keywords_regex(text, keywords_list):
    """Checks if text contains any of the keywords using regex."""
    text_lower = text.lower()
    for keyword_pattern in keywords_list:
        if re.search(keyword_pattern, text_lower):
            return True
    return False

def lambda_handler(event, context):
    """
    Processes Kinesis records for content moderation issues (spam, irrelevant, hate speech, illegal).
    """
    flagged_items = []
    
    for record in event["Records"]:
        try:
            payload = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            review = json.loads(payload)

            review_id = review.get("review_id")
            product_id = review.get("product_id")
            user_id = review.get("user_id")
            review_text = review.get("review_text", "")
            
            flagged = False
            detection_rules = []

            # --- Rule 1: Spam Keywords ---
            if contains_keywords_regex(review_text, SPAM_KEYWORDS):
                flagged = True
                detection_rules.append("Rule: Contains Spam Keywords")
            
            # --- Rule 2: Hate Speech / Toxicity (via Keywords & Comprehend Sentiment) ---
            # Initial approach: Combine keyword spotting with sentiment analysis for basic detection
            comprehend_language = "en" # Default to English
            try:
                # Detect dominant language for better sentiment analysis accuracy
                language_response = comprehend_client.detect_dominant_language(Text=review_text)
                if language_response and language_response["Languages"]:
                    comprehend_language = language_response["Languages"][0]["LanguageCode"]
            except Exception as e:
                print(f"Warning: Error detecting language for review {review_id}: {e}")
                # Continue with default language if language detection fails

            if contains_keywords_regex(review_text, HATE_SPEECH_KEYWORDS):
                if not flagged: # Avoid re-adding if already flagged
                    flagged = True
                detection_rules.append("Rule: Contains Hate Speech Keywords (via Keyword Spotting)")
            
            try:
                # Perform sentiment analysis
                sentiment_response = comprehend_client.detect_sentiment(Text=review_text, LanguageCode=comprehend_language)
                sentiment = sentiment_response["Sentiment"]
                sentiment_score = sentiment_response["SentimentScore"]
                
                # If sentiment is overwhelmingly negative and matches certain patterns, it could indicate abuse
                # This is a very basic heuristic; a full hate speech detector would be more sophisticated.
                if sentiment == "NEGATIVE" and sentiment_score["Negative"] > 0.9: # Very high confidence of negativity
                    if not flagged:
                        flagged = True
                    detection_rules.append(f"Rule: Extremely Negative Sentiment ({sentiment_score['Negative']:.2f} confidence)")

            except Exception as e:
                print(f"Warning: Error detecting sentiment for review {review_id}: {e}")
                
            # --- Rule 3: Illegal Content Keywords ---
            if contains_keywords_regex(review_text, ILLEGAL_KEYWORDS):
                if not flagged:
                    flagged = True
                detection_rules.append("Rule: Contains Illegal Content Keywords")
            
            # --- Rule 4: Irrelevant/Gibberish Content ---
            # Very short reviews with little to no meaningful words, or just random characters
            word_count = len(review_text.split())
            if word_count < IRRELEVANT_TEXT_THRESHOLD and not re.search(r'\w{2,}', review_text): # Less than X words and few meaningful words
                if not flagged:
                    flagged = True
                detection_rules.append("Rule: Very short and potentially irrelevant/gibberish content")
            
            if flagged:
                flag_timestamp = datetime.utcnow().isoformat() + "Z"
                flag_id = f"CM_{review_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

                flagged_item = {
                    "flag_id": flag_id,
                    "review_id": review_id,
                    "product_id": product_id,
                    "user_id": user_id,
                    "review_text": review_text,
                    "flag_type": "ContentModeration",
                    "detection_rule": "; ".join(detection_rules),
                    "flag_timestamp": flag_timestamp,
                    "status": "PENDING_REVIEW",
                    "metadata": {
                        "review_length_words": word_count,
                        "sentiment": sentiment if 'sentiment' in locals() else 'N/A',
                        "sentiment_score_negative": sentiment_score["Negative"] if 'sentiment_score' in locals() else 0.0,
                    }
                }
                flagged_items.append(flagged_item)

        except Exception as e:
            print(f"Error processing Kinesis record: {e}. Record: {record}")
    
    if flagged_items:
        with table.batch_writer() as batch:
            for item in flagged_items:
                batch.put_item(Item=item)
        print(f"Successfully flagged {len(flagged_items)} reviews for content moderation issues.")
    
    return {
        "statusCode": 200,
        "body": json.dumps(f"Processed {len(event['Records'])} Kinesis records. Flagged {len(flagged_items)} reviews.")
    }
```