
# User Story 1 (US1): Ingest new Amazon reviews in near real-time.

### Implementation Plan

The ingestion pipeline will leverage a streaming architecture. A dedicated **Ingestion Service** (microservice) will be responsible for:
1.  **Polling/Subscribing:** Periodically fetching or subscribing to new review data from the Amazon review feed.
2.  **Parsing & Validation:** Cleaning, structuring, and validating the raw review data against a predefined schema.
3.  **Publishing:** Pushing the validated review data to a message queue for real-time streaming to downstream services (e.g., storage, detection).

### Data Models

1.  **RawReviewData:** The exact structure of the data as received directly from the Amazon API or feed.
    *   *Example fields:* `review_id`, `reviewer_uuid`, `product_id`, `review_date`, `user_ip`, `review_body`, `stars`, `title`.
2.  **ValidatedReviewData (ReviewData Model):** A standardized, cleaned, and validated version of the review data, used internally across services.

    ```json
    {
        "reviewId": "string",         // Unique identifier for the review
        "reviewerId": "string",       // Identifier for the reviewer
        "productASIN": "string",      // Amazon Standard Identification Number for the product
        "timestamp": "datetime",      // Timestamp of the review
        "ipAddress": "string",        // IP address of the reviewer (anonymized/hashed if required)
        "reviewText": "string",       // Full text content of the review
        "rating": "integer",          // Star rating (e.g., 1-5)
        "reviewTitle": "string",      // Title of the review (optional)
        "source": "string"            // Source of the review, e.g., "amazon"
    }
    ```

### Architecture

```
[Amazon Review Feed]
        |
        V
[Ingestion Service] -- (API Integration, Parsing, Validation)
        |
        V
[Message Queue] (e.g., Kafka / Amazon Kinesis)
        |
        V
(To Storage Service, Detection Service)
```

**Components:**
*   **Amazon Review Feed:** External source of review data.
*   **Ingestion Service:** A microservice responsible for orchestrating the data pull, transformation, and push.
*   **Message Queue:** A highly scalable, fault-tolerant message broker to enable real-time streaming and decouple services.

### Assumptions and Technical Decisions

*   **Assumption:** A reliable API or data feed for Amazon reviews exists and is accessible. The data format is consistent.
*   **Assumption:** The volume of reviews necessitates a streaming solution for near real-time processing.
*   **Technical Decision (T1.1, T1.4):** Utilize a message queue (e.g., Apache Kafka or Amazon Kinesis) for high-throughput, low-latency data streaming, providing buffering and enabling multiple consumers.
*   **Technical Decision (T1.2):** Implement a polling mechanism for the API integration if a push-based webhook is not available. Utilize an HTTP client library (e.g., `requests` in Python).
*   **Technical Decision (T1.3):** Implement robust data validation including schema checks, data type conversions, and handling of missing/malformed fields. Logging of validation failures is crucial.
*   **Technical Decision (T1.5):** Implement unit tests for individual functions (API calls, parsing, validation) and integration tests for the full pipeline flow, including message queue interaction.

### Code Snippets / Pseudocode

#### T1.2: Implement API integration for new review data feed (Python Pseudocode)

```python
import requests
import time
from datetime import datetime, timezone

class AmazonReviewAPI:
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint

    def fetch_reviews(self, last_fetched_timestamp: datetime = None) -> list:
        """
        Fetches new reviews from the Amazon API since a given timestamp.
        Returns a list of raw review data dictionaries.
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {}
        if last_fetched_timestamp:
            # API expects ISO format timestamp, e.g., "2023-10-27T10:00:00Z"
            params["since"] = last_fetched_timestamp.isoformat(timespec='seconds') + 'Z'
        
        try:
            response = requests.get(f"{self.endpoint}/reviews", headers=headers, params=params, timeout=30)
            response.raise_for_status() # Raise an exception for HTTP errors
            return response.json().get("reviews", []) # Assuming API returns {"reviews": [...]}
        except requests.exceptions.RequestException as e:
            print(f"Error fetching reviews from Amazon API: {e}")
            return []

def get_latest_timestamp(raw_reviews: list) -> datetime:
    """Helper to find the latest timestamp in a list of raw reviews."""
    if not raw_reviews:
        return None
    latest = datetime.min.replace(tzinfo=timezone.utc) # Initialize with earliest possible UTC datetime
    for review in raw_reviews:
        try:
            review_time = datetime.fromisoformat(review.get("review_timestamp").replace('Z', '+00:00'))
            if review_time > latest:
                latest = review_time
        except (ValueError, TypeError):
            continue # Ignore reviews with invalid timestamps
    return latest if latest != datetime.min.replace(tzinfo=timezone.utc) else None

# Example Ingestion Service main loop (conceptual)
def run_ingestion_loop():
    api = AmazonReviewAPI(api_key="YOUR_AMAZON_API_KEY", endpoint="https://api.amazon.com/reviews/v1")
    last_processed_timestamp = None # Or load from a persistent store
    
    while True:
        print(f"Fetching reviews since: {last_processed_timestamp}")
        raw_reviews = api.fetch_reviews(last_processed_timestamp)
        
        if raw_reviews:
            for raw_review in raw_reviews:
                # This is where T1.3 (parsing/validation) and T1.4 (streaming) would be called
                # validated_data = parse_and_validate(raw_review)
                # if validated_data:
                #    publish_to_message_queue("review_stream", validated_data)
                pass # Placeholder for actual logic
            
            # Update last_processed_timestamp after successfully processing a batch
            new_latest_timestamp = get_latest_timestamp(raw_reviews)
            if new_latest_timestamp:
                last_processed_timestamp = new_latest_timestamp
            
        time.sleep(60) # Poll every 60 seconds
```

#### T1.3: Develop data parsing and validation logic (Python Pseudocode)

```python
from datetime import datetime, timezone

def parse_and_validate_review(raw_review_data: dict) -> dict | None:
    """
    Parses raw review data dictionary and validates its structure and content.
    Returns a dictionary conforming to the ValidatedReviewData model or None if invalid.
    """
    try:
        # Extract and validate mandatory fields
        review_id = raw_review_data.get("review_id")
        reviewer_id = raw_review_data.get("reviewer_uuid") # Assuming 'reviewer_uuid' from raw
        product_asin = raw_review_data.get("product_id") # Assuming 'product_id' from raw
        timestamp_str = raw_review_data.get("review_date") # Assuming 'review_date' from raw
        ip_address = raw_review_data.get("user_ip")
        review_text = raw_review_data.get("review_body")

        if not all([review_id, reviewer_id, product_asin, timestamp_str, ip_address, review_text]):
            print(f"Validation Error: Missing one or more required fields in review: {raw_review_data.get('review_id', 'N/A')}")
            return None

        # Timestamp parsing and timezone handling
        try:
            # Assuming ISO 8601 format, potentially without timezone info (then assume UTC)
            if timestamp_str.endswith('Z'): # Already UTC
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else: # Assume it's UTC if no timezone is specified
                timestamp = datetime.fromisoformat(timestamp_str).replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Validation Error: Invalid timestamp format '{timestamp_str}' for review {review_id}")
            return None

        # Validate rating if present
        rating = raw_review_data.get("stars")
        if rating is not None:
            try:
                rating = int(rating)
                if not (1 <= rating <= 5): # Assuming 1-5 star rating
                    print(f"Validation Warning: Rating out of range for review {review_id}. Value: {rating}")
                    rating = None # Or set to default/null
            except ValueError:
                print(f"Validation Warning: Invalid rating type for review {review_id}. Value: {rating}")
                rating = None

        # Sanitize text fields (e.g., remove leading/trailing whitespace, limit length)
        review_text = review_text.strip()
        review_title = raw_review_data.get("title", "").strip()

        # Construct the ValidatedReviewData model
        return {
            "reviewId": review_id,
            "reviewerId": reviewer_id,
            "productASIN": product_asin,
            "timestamp": timestamp, # datetime object
            "ipAddress": ip_address,
            "reviewText": review_text,
            "rating": rating,
            "reviewTitle": review_title if review_title else None,
            "source": "amazon"
        }
    except Exception as e:
        print(f"Unhandled error during parsing/validation: {e} for review: {raw_review_data.get('review_id', 'N/A')}")
        return None

# Example usage within the ingestion loop:
# validated_review = parse_and_validate_review(raw_review)
# if validated_review:
#    # Proceed to T1.4
# else:
#    # Log the invalid review, possibly move to a dead-letter queue
```

#### T1.4: Implement real-time data streaming to processing layer (Python Pseudocode for Kafka)

```python
from kafka import KafkaProducer
import json
from datetime import datetime, timezone

# Custom JSON serializer for datetime objects
def json_serial(obj):
    if isinstance(obj, (datetime)):
        # Convert datetime objects to ISO 8601 string with UTC timezone
        return obj.isoformat(timespec='seconds') + 'Z' if obj.tzinfo is not None else obj.astimezone(timezone.utc).isoformat(timespec='seconds') + 'Z'
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

# Initialize Kafka Producer (should be done once per service instance)
# Replace 'localhost:9092' with your Kafka broker list
try:
    kafka_producer = KafkaProducer(
        bootstrap_servers=['kafka-broker-1:9092', 'kafka-broker-2:9092'],
        value_serializer=lambda v: json.dumps(v, default=json_serial).encode('utf-8'),
        acks='all', # Ensure messages are replicated
        retries=5    # Number of times to retry sending a message
    )
    print("Kafka Producer initialized successfully.")
except Exception as e:
    print(f"Error initializing Kafka Producer: {e}. Exiting.")
    # In a real application, you might want to log this and try to reinitialize or exit gracefully.
    kafka_producer = None # Set to None if initialization fails

def publish_validated_review_to_stream(topic: str, validated_review_data: dict) -> bool:
    """
    Publishes validated review data to a Kafka topic.
    Returns True on success, False on failure.
    """
    if not kafka_producer:
        print("Kafka Producer is not initialized. Cannot publish message.")
        return False

    try:
        # Asynchronous send
        future = kafka_producer.send(topic, value=validated_review_data)
        record_metadata = future.get(timeout=60) # Block until a single message is sent (optional, for confirmation)
        print(f"Successfully published review '{validated_review_data.get('reviewId', 'N/A')}' to topic '{record_metadata.topic}', partition {record_metadata.partition}, offset {record_metadata.offset}")
        return True
    except Exception as e:
        print(f"Error publishing review '{validated_review_data.get('reviewId', 'N/A')}' to Kafka topic '{topic}': {e}")
        return False

# Example usage:
# if validated_data:
#    publish_validated_review_to_stream("review-ingestion-stream", validated_data)
```

#### T1.5: Unit and integration tests for ingestion pipeline (Conceptual)

*   **Unit Tests:**
    *   Test `AmazonReviewAPI.fetch_reviews` with mock API responses (success, empty, error).
    *   Test `parse_and_validate_review` with valid, invalid, and edge-case review data.
    *   Test `get_latest_timestamp` with various lists of reviews.
    *   Test `json_serial` for correct `datetime` serialization.
*   **Integration Tests:**
    *   Set up a test Kafka instance (e.g., using `testcontainers-python` or a local Docker compose).
    *   Run a simplified ingestion loop, publishing messages to the test Kafka topic.
    *   Verify that messages are correctly published and can be consumed from the topic, matching the expected `ValidatedReviewData` format.
    *   Test error handling when the API is down or Kafka is unreachable.
