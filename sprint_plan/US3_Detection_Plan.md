# User Story 3 (US3): Apply basic rule-based detection.

### Implementation Plan

The system will incorporate a dedicated **Detection Service** (microservice) responsible for applying rule-based logic to identify potentially abusive reviews. This service will:
1.  **Consume:** Subscribe to the `review-ingestion-stream` from the message queue to receive validated review data in real-time.
2.  **Evaluate:** Apply a predefined set of detection rules to each incoming review and its associated historical context (fetched from the Storage Service).
3.  **Flag:** Mark reviews that trigger any detection rule as "potentially abusive" and record the specific reasons for flagging.
4.  **Update:** Update the status of the review in the Storage Service with the flagged status and reasons.

### Data Models

1.  **ReviewData (from Storage Service):** The Detection Service will primarily operate on the `ReviewData` model stored in the database, fetching historical context as needed.
2.  **DetectionRule Model:** A simple model to define and manage the detection rules.

    ```json
    {
        "ruleId": "string",          // Unique identifier for the rule
        "name": "string",            // Human-readable name of the rule
        "description": "string",     // Detailed description of what the rule detects
        "criteria": "JSON/string",   // The actual logic or parameters for the rule (e.g., "ip_threshold": 5, "time_window_hours": 24)
        "severity": "string",        // e.g., "HIGH", "MEDIUM", "LOW"
        "enabled": "boolean"         // Whether the rule is currently active
    }
    ```
3.  **FlaggedReviewData (Update Model):** The structure used to update a review in the Storage Service after detection.

    ```json
    {
        "reviewId": "string",            // The ID of the review being flagged
        "status": "string",              // New status, e.g., "flagged_abuse"
        "flaggingReasons": "array<string>", // List of rule names that triggered the flagging
        "lastUpdated": "datetime"        // Timestamp of this update
    }
    ```

### Architecture

```
[Message Queue] (e.g., Kafka / Amazon Kinesis)
        |\\\
        | \\\n        |  V
        | [Detection Service] -- (Rule Engine, Evaluation Logic)
        |    |
        |    V
        | [Storage Service] <--(Fetch historical data, Update review status & flagging reasons)
        |
        V
(To Dashboard API for displaying flagged reviews)
```

**Components:**
*   **Message Queue:** Provides the stream of validated reviews.
*   **Detection Service:** A microservice hosting the rule engine and evaluation logic.
*   **Storage Service:** Accessed by the Detection Service to retrieve historical data for context-based rules and to persist flagging decisions.

### Assumptions and Technical Decisions

*   **Assumption (T3.1):** The initial set of rules will be relatively simple and well-defined, not requiring complex machine learning models in this sprint. Rules can be configured statically or loaded from a simple configuration store.
*   **Assumption (T3.2):** The rule engine will be custom-built or use a lightweight open-source rule engine (if complexity justifies it) capable of evaluating rules against incoming review data and potentially querying historical data.
*   **Assumption (T3.3):** The integration with the incoming review stream will be consumer-based (e.g., Kafka Consumer), ensuring reliable message processing and enabling horizontal scaling.
*   **Assumption (T3.4, T3.5):** The flagging mechanism will update the existing `ReviewData` record in the Storage Service by changing its `status` and adding `flaggingReasons`. This requires an update API in the Storage Service.
*   **Technical Decision (T3.1):** Rules will initially be defined in a configuration file (e.g., JSON or YAML) within the Detection Service, allowing for easy updates without redeploying the core service logic.
    *   *Example Rules:*
        *   **Rule 1: Identical Review Text:** Flag if review text is identical to another review from a different `reviewerId` within a specific `time_window` (e.g., 24 hours). Validated `reviewerId` will be checked against `ReviewData` from Storage Service.
        *   **Rule 2: Multiple Reviews from Same IP for Unrelated Products:** Flag if a single `ipAddress` submits more than `N` reviews for `productASIN`s that are not "related" (e.g., different product categories) within `time_window`. (For MVP, "unrelated" might simply mean different `productASIN`s). Validated `ipAddress` and `productASIN` will be checked against `ReviewData` from Storage Service.
*   **Technical Decision (T3.2):** A custom rule evaluation logic will be implemented in Python for simplicity and flexibility in this initial phase. It will iterate through active rules and apply their criteria. It will interact with the Storage Service to fetch historical data for context-based rules.
*   **Technical Decision (T3.3):** The Detection Service will implement a Kafka consumer group to read from the `review-ingestion-stream` topic, ensuring fault tolerance and parallel processing. Messages will be deserialized into the `ValidatedReviewData` format.
*   **Technical Decision (T3.4, T3.5):** The flagging mechanism will involve calling an API endpoint on the Storage Service (e.g., a REST endpoint) to update the review's status and add flagging reasons to the `flaggingReasons` JSONB array. This update will include the `lastUpdated` timestamp.
*   **Technical Decision (T3.6):** Unit tests will cover individual rule logic and the rule evaluation engine. Integration tests will simulate receiving a review from the message queue, applying rules, querying the Storage Service for context, and verifying the correct update to the Storage Service. Mocking will be used for external dependencies like Kafka and the Storage Service API during unit tests.

### Code Snippets / Pseudocode

#### T3.1: Define initial set of basic detection rules (JSON Configuration)

```json
[
    {
        "ruleId": "RULE-001",
        "name": "Identical Review Text Abuse",
        "description": "Flags reviews with identical text from different reviewers within a short timeframe.",
        "severity": "HIGH",
        "enabled": true,
        "criteria": {
            "type": "identical_text",
            "time_window_minutes": 1440,  // 24 hours
            "min_reviews": 2              // At least 2 identical reviews
        }
    },
    {
        "ruleId": "RULE-002",
        "name": "Excessive Reviews from Same IP",
        "description": "Flags IP addresses submitting many reviews for different products in a short period.",
        "severity": "MEDIUM",
        "enabled": true,
        "criteria": {
            "type": "ip_activity",
            "time_window_minutes": 60,   // 1 hour
            "min_unique_products": 3,    // At least 3 different products
            "max_reviews_per_ip": 5      // More than 5 reviews from same IP in time window
        }
    }
]
```

#### T3.2: Develop rule engine and evaluation logic (Python Pseudocode)

```python
import json
from datetime import datetime, timedelta, timezone

# Assume an API or ORM for Storage Service exists
class StorageServiceAPI:
    def get_historical_reviews_by_ip(self, ip_address: str, time_window_start: datetime) -> list:
        # Placeholder: Call actual Storage Service to get reviews by IP after a certain timestamp
        # Returns a list of ReviewData dictionaries
        print(f"Fetching historical reviews for IP: {ip_address} since {time_window_start}")
        # Example data structure expected from Storage Service
        return [
            # {\"reviewId\": \"RXYZ\", \"reviewerId\": \"U123\", \"productASIN\": \"B00ABCD\", \"timestamp\": ..., \"reviewText\": \"...\"}
        ]

    def get_historical_reviews_by_text(self, review_text: str, time_window_start: datetime, exclude_review_id: str) -> list:
        # Placeholder: Call actual Storage Service to find similar review texts
        print(f"Fetching historical reviews with text like: '{review_text[:50]}' since {time_window_start}")
        return []

    def update_review_status(self, review_id: str, status: str, flagging_reasons: list):
        # Placeholder: Call actual Storage Service to update review status
        print(f"Updating review {review_id} to status '{status}' with reasons: {flagging_reasons}")
        pass

class RuleEngine:
    def __init__(self, rules_config_path: str, storage_api: StorageServiceAPI):
        self.rules = self._load_rules(rules_config_path)
        self.storage_api = storage_api

    def _load_rules(self, path: str) -> list:
        try:
            with open(path, 'r') as f:
                rules = json.load(f)
                return [rule for rule in rules if rule.get("enabled", False)]
        except Exception as e:
            print(f"Error loading rules configuration: {e}")
            return []

    def evaluate_review(self, review_data: dict) -> dict:
        """
        Evaluates a single incoming review against all active rules.
        Returns the review data with updated status and flagging reasons if applicable.
        """
        flagged_reasons = []
        current_timestamp = review_data.get("timestamp", datetime.now(timezone.utc))

        for rule in self.rules:
            rule_id = rule["ruleId"]
            rule_name = rule["name"]
            criteria = rule["criteria"]

            if criteria["type"] == "identical_text":
                time_window = timedelta(minutes=criteria["time_window_minutes"])
                time_window_start = current_timestamp - time_window
                
                # Fetch reviews with identical text from other reviewers within the time window
                similar_reviews = self.storage_api.get_historical_reviews_by_text(
                    review_text=review_data["reviewText"],
                    time_window_start=time_window_start,
                    exclude_review_id=review_data["reviewId"]
                )
                
                # Filter to only include reviews from different reviewers
                distinct_reviewers_count = len(set(r.get("reviewerId") for r in similar_reviews if r.get("reviewerId") != review_data.get("reviewerId")))
                
                if distinct_reviewers_count >= criteria["min_reviews"] - 1: # -1 because the current review counts towards the min_reviews
                    flagged_reasons.append(rule_name)

            elif criteria["type"] == "ip_activity":
                time_window = timedelta(minutes=criteria["time_window_minutes"])
                time_window_start = current_timestamp - time_window

                # Fetch all reviews from this IP address within the time window
                ip_reviews = self.storage_api.get_historical_reviews_by_ip(
                    ip_address=review_data["ipAddress"],
                    time_window_start=time_window_start
                )
                
                # Add the current review to the list for evaluation
                ip_reviews.append(review_data) 

                unique_products_count = len(set(r.get("productASIN") for r in ip_reviews))
                
                if (len(ip_reviews) > criteria["max_reviews_per_ip"] and
                    unique_products_count >= criteria["min_unique_products"]):
                    flagged_reasons.append(rule_name)
            
            # Add other rule types here

        if flagged_reasons:
            review_data["status"] = "flagged_abuse"
            review_data["flaggingReasons"] = flagged_reasons
        else:
            review_data["status"] = "legitimate" # Or 'pending' if manual review is default

        return review_data

# Example usage (conceptual)
# storage_api_instance = StorageServiceAPI()
# rule_engine = RuleEngine(rules_config_path="rules.json", storage_api=storage_api_instance)
# processed_review = rule_engine.evaluate_review(incoming_validated_review_data)
# if processed_review["status"] == "flagged_abuse":
#    storage_api_instance.update_review_status(
#        processed_review["reviewId"],
#        processed_review["status"],
#        processed_review["flaggingReasons"]
#    )
```

#### T3.3: Integrate rule engine with incoming review stream (Python Pseudocode for Kafka Consumer)

```python
from kafka import KafkaConsumer
import json
from datetime import datetime, timezone

# Assuming RuleEngine and StorageServiceAPI classes from T3.2 are available
# from .rule_engine import RuleEngine, StorageServiceAPI

# Custom JSON deserializer for datetime objects
def json_deserial(x):
    data = json.loads(x.decode('utf-8'))
    if 'timestamp' in data and isinstance(data['timestamp'], str):
        try:
            # Handle 'Z' for UTC and ensure timezone awareness
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            pass # Handle invalid timestamp format gracefully
    return data

def run_detection_service():
    storage_api = StorageServiceAPI() # Initialize your StorageServiceAPI client
    rule_engine = RuleEngine(rules_config_path="rules.json", storage_api=storage_api)

    consumer = KafkaConsumer(
        'review-ingestion-stream',
        bootstrap_servers=['kafka-broker-1:9092'], # Replace with your Kafka brokers
        auto_offset_reset='latest',  # Start consuming from the latest message
        enable_auto_commit=True,
        group_id='detection-service-group',
        value_deserializer=json_deserial
    )

    print("Detection Service started, listening for new reviews...")
    for message in consumer:
        validated_review = message.value
        print(f"Received review for detection: {validated_review.get('reviewId')}")

        # Evaluate the review using the rule engine
        processed_review = rule_engine.evaluate_review(validated_review)

        # T3.4 & T3.5: Implement flagging mechanism and store reasons
        if processed_review["status"] == "flagged_abuse":
            print(f"Review {processed_review['reviewId']} flagged with reasons: {processed_review['flaggingReasons']}")
            storage_api.update_review_status(
                review_id=processed_review["reviewId"],
                status="flagged_abuse",
                flagging_reasons=processed_review["flaggingReasons"]
            )
        else:
            print(f"Review {processed_review['reviewId']} is legitimate.")
            # Optionally update status to 'legitimate' if it's the final decision point
            # storage_api.update_review_status(processed_review["reviewId"], "legitimate", [])

# if __name__ == '__main__':
#     run_detection_service()
```

#### T3.4 & T3.5: Implement flagging mechanism and store flagging reasons (Covered in T3.2 and T3.3 pseudocode)

The `RuleEngine.evaluate_review` function adds the `status` and `flaggingReasons` to the `review_data` dictionary. The `run_detection_service` function then calls `storage_api.update_review_status` to persist these changes.

The `StorageServiceAPI.update_review_status` method would typically make an HTTP PUT/PATCH request to a Storage Service API endpoint, or directly update the database if part of the same application.

**Example Storage Service API Endpoint (Conceptual)**

```http
PUT /reviews/{reviewId}/status
Content-Type: application/json

{
    "status": "flagged_abuse",
    "flaggingReasons": ["Identical Review Text Abuse", "Excessive Reviews from Same IP"]
}
```

The Storage Service (from US2) would then update the `status` and `flagging_reasons` fields in its database.

#### T3.6: Unit and integration tests for rule-based detection (Conceptual)

*   **Unit Tests:**
    *   Test `RuleEngine._load_rules` with valid, invalid, and empty rule files.
    *   Test individual rule logic within `RuleEngine.evaluate_review` for different scenarios:
        *   `identical_text` rule:
            *   When identical reviews exist from different reviewers.
            *   When identical reviews exist from the *same* reviewer (should not flag for this rule).
            *   When no identical reviews are found.
            *   Edge cases for time windows.
        *   `ip_activity` rule:
            *   When IP exceeds review threshold and unique product threshold.
            *   When only one of the thresholds is met.
            *   When thresholds are not met.
            *   Edge cases for time windows and product counting.
    *   Mock `StorageServiceAPI` responses to control historical data for testing rule evaluation.
*   **Integration Tests:**
    *   Set up a test Kafka instance (e.g., using `testcontainers-python`).
    *   Set up a mock or test Storage Service API (e.g., using `pytest-httpx` or a simple Flask/FastAPI mock server) that the `StorageServiceAPI` client can interact with.
    *   Publish `ValidatedReviewData` messages to the Kafka `review-ingestion-stream` topic.
    *   Run the `run_detection_service` with the configured rules.
    *   Verify that `StorageServiceAPI.update_review_status` is called with the correct `review_id`, `status`, and `flaggingReasons` for flagged reviews.
    *   Verify that `StorageServiceAPI.get_historical_reviews_by_ip` and `get_historical_reviews_by_text` are called with the expected parameters.
    *   Test error handling when Kafka is unavailable or the Storage Service API returns errors.
*   **End-to-End Tests (Future consideration with US1 & US2 integration):**
    *   Run the full ingestion pipeline (US1), storage service (US2), and detection service (US3) together.
    *   Inject raw review data into the ingestion pipeline.
    *   Verify that reviews are ingested, stored, detected for abuse, and their status is updated in the database.
