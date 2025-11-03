# Real-time Review Ingestion Pipeline Design

## 1. Implementation Plan

This task focuses on designing a robust, scalable, and fault-tolerant pipeline for ingesting Amazon product reviews in real-time. The plan involves:

1.  **Component Definition:** Clearly defining the roles and responsibilities of each component in the pipeline.
2.  **Data Flow Mapping:** Illustrating how data moves through the system.
3.  **Error Handling & Monitoring:** Incorporating mechanisms for identifying and addressing issues.
4.  **Scalability & Reliability:** Designing for high availability and the ability to handle varying loads.

## 2. Data Models & Architecture

### 2.1. Architecture Diagram (Conceptual)

```mermaid
graph TD
    A[Third-Party Review API / Simulated Stream] --> B{Review Ingestion Service}
    B -- Valid Review --> C[Message Queue: raw-reviews]
    B -- Invalid Review / Error --> D[Message Queue: dead-letter-queue]
    C --> E[Raw Data Storage (NoSQL)]

    subgraph Legend
        A(External Source)
        B(Application Service)
        C(Message Queue)
        D(Message Queue)
        E(Database)
    end
```

### 2.2. Component Breakdown

*   **Review Source (External):**
    *   **Description:** The external system providing real-time Amazon review data. As per Task 1.1, this will be a specialized third-party data provider or a simulated stream for initial development.
    *   **Interaction:** The Ingestion Service will either poll this source at regular intervals or receive data via webhooks.
*   **Review Ingestion Service:**
    *   **Description:** A lightweight, dedicated microservice responsible for interacting with the Review Source. Its primary function is to fetch/receive review data, perform initial basic validation, and push the raw review data into a message queue.
    *   **Technologies:** Could be implemented using Python (FastAPI/Flask), Node.js (Express), or a similar language/framework suitable for event-driven processing.
    *   **Key Responsibilities:**
        *   Connect to the Review Source (API calls, webhook listener).
        *   Perform schema validation and basic sanitization of incoming review data.
        *   Publish validated raw review data to the `raw-reviews` message queue.
        *   Publish invalid/errored review data to a `dead-letter-queue` for analysis and reprocessing.
        *   Handle rate limiting, retries, and back-offs when interacting with the Review Source.
*   **Message Queue (`raw-reviews`):**
    *   **Description:** A high-throughput, fault-tolerant message queue system (e.g., Apache Kafka, AWS Kinesis, RabbitMQ, Google Cloud Pub/Sub).
    *   **Purpose:** Decouples the Ingestion Service from downstream consumers, provides buffering, enables asynchronous processing, and ensures data durability.
*   **Message Queue (`dead-letter-queue`):**
    *   **Description:** A separate queue for messages that failed initial processing in the Ingestion Service.
    *   **Purpose:** Allows for investigation of malformed or unprocessable messages without blocking the main pipeline.
*   **Raw Data Storage (NoSQL):**
    *   **Description:** A NoSQL database (e.g., Amazon DynamoDB, MongoDB, Apache Cassandra) optimized for high write throughput and flexible schema.
    *   **Purpose:** Stores the raw, unvalidated, and unprocessed review data exactly as it was received from the Review Source. This serves as a source of truth for all ingested data and allows for reprocessing or auditing if needed.

## 3. Assumptions & Technical Decisions

### 3.1. Assumptions

*   **Review Data Format:** The external Review Source provides review data in a consistent, structured format (e.g., JSON).
*   **Real-time Definition:** "Real-time" implies processing within seconds to a few minutes of a review being published on Amazon.
*   **Data Volume:** The system should be designed to handle a moderate to high volume of reviews (e.g., thousands to tens of thousands per minute) with potential for scaling to higher volumes.
*   **Security:** API keys or authentication tokens for the Review Source will be managed securely (e.g., environment variables, secrets manager).

### 3.2. Technical Decisions

*   **Asynchronous Processing:** Utilize a message queue to enable asynchronous processing, enhancing scalability and fault tolerance.
*   **NoSQL for Raw Storage:** Opt for a NoSQL database for raw review data due to its schema flexibility (as review data might evolve) and ability to handle high write loads.
*   **Microservice Architecture:** The Ingestion Service will be a dedicated microservice, allowing independent scaling and deployment.
*   **Minimal Ingestion-time Processing:** The Ingestion Service will perform only essential validation. Heavy processing, enrichment, or transformation will occur downstream by other services consuming from the `raw-reviews` queue.

## 4. Code Snippets / Pseudocode for Key Components

### 4.1. Review Ingestion Service (Pseudocode)

```python
import time
import json

# --- External Dependencies (Interfaces) ---

class ReviewSourceClient:
    """Interface for interacting with the external Amazon review data source."""
    def get_new_reviews(self) -> list[dict]:
        """Fetches new reviews from the source. In a real scenario, this might involve API calls or reading from a stream."""
        raise NotImplementedError

class MessageQueueProducer:
    """Interface for sending messages to a message queue."""
    def send_message(self, topic: str, message: dict):
        """Sends a dictionary message to the specified topic."""
        raise NotImplementedError

# --- Ingestion Service Implementation ---

class ReviewIngestionService:
    """Service responsible for ingesting reviews and pushing them to a message queue."""
    def __init__(self, review_source_client: ReviewSourceClient, message_queue_producer: MessageQueueProducer):
        self.review_source_client = review_source_client
        self.message_queue_producer = message_queue_producer
        self.polling_interval_seconds = 60 # Example polling interval

    def start_ingestion_loop(self):
        """Starts the continuous loop for fetching and processing reviews."""
        print("Review Ingestion Service started...")
        while True:
            try:
                print(f"Polling for new reviews... (Next poll in {self.polling_interval_seconds}s)")
                new_reviews = self.review_source_client.get_new_reviews()
                if new_reviews:
                    print(f"Found {len(new_reviews)} new reviews.")
                    for review_data in new_reviews:
                        self._process_single_review(review_data)
                else:
                    print("No new reviews found.")
            except Exception as e:
                print(f"Error during ingestion loop: {e}")
                # Implement more sophisticated error handling and alerting
            time.sleep(self.polling_interval_seconds)

    def _process_single_review(self, review_data: dict):
        """Validates and pushes a single review to the appropriate queue."""
        try:
            if self._validate_review_schema(review_data):
                # Add timestamp or other metadata if needed before sending
                self.message_queue_producer.send_message("raw-reviews", review_data)
                print(f"Successfully pushed review {review_data.get('review_id', 'N/A')} to raw-reviews queue.")
            else:
                error_payload = {"error": "Invalid review schema", "data": review_data}
                self.message_queue_producer.send_message("dead-letter-queue", error_payload)
                print(f"Invalid review schema detected for review {review_data.get('review_id', 'N/A')}. Sent to dead-letter-queue.")
        except Exception as e:
            error_payload = {"error": str(e), "data": review_data}
            self.message_queue_producer.send_message("dead-letter-queue", error_payload)
            print(f"Error processing review {review_data.get('review_id', 'N/A')}: {e}. Sent to dead-letter-queue.")

    def _validate_review_schema(self, review: dict) -> bool:
        """Performs basic structural validation for a review."""
        required_keys = ["review_id", "product_id", "user_id", "review_text", "rating", "review_timestamp"]
        if not all(key in review and review[key] is not None for key in required_keys):
            print(f"Missing or null required keys in review: {review}")
            return False
        # Add more specific type/format validation here if necessary
        if not isinstance(review.get("rating"), (int, float)) or not (0 <= review["rating"] <= 5):
            print(f"Invalid rating value in review: {review.get('rating')}")
            return False
        return True

# --- Example Implementations (for testing/mocking) ---

class MockReviewSourceClient(ReviewSourceClient):
    def __init__(self, reviews_to_provide: list):
        self.reviews = reviews_to_provide
        self.call_count = 0

    def get_new_reviews(self) -> list[dict]:
        self.call_count += 1
        if self.call_count == 1: # Provide reviews only on the first call for this mock
            print("MockReviewSourceClient: Providing initial set of reviews.")
            return self.reviews
        else:
            print("MockReviewSourceClient: No new reviews available.")
            return []

class ConsoleMessageQueueProducer(MessageQueueProducer):
    def send_message(self, topic: str, message: dict):
        print(f"[MQ Producer - {topic}]: {json.dumps(message, indent=2)}")

# --- Main execution for demonstration ---
if __name__ == "__main__":
    # Simulate some incoming review data
    mock_reviews = [
        {
            "review_id": "R1",
            "product_id": "B00123",
            "user_id": "U1",
            "review_text": "Great product, highly recommend!",
            "rating": 5,
            "review_timestamp": "2023-10-26T10:00:00Z"
        },
        {
            "review_id": "R2",
            "product_id": "B00456",
            "user_id": "U2",
            "review_text": "It was okay, nothing special.",
            "rating": 3,
            "review_timestamp": "2023-10-26T10:05:00Z"
        },
        {
            "review_id": "R3",
            "product_id": "B00789",
            "user_id": "U3",
            "review_text": "Absolutely terrible, don't buy!",
            "rating": 1,
            "review_timestamp": "2023-10-26T10:10:00Z"
        },
        {
            "review_id": "R4", # Invalid review: missing product_id
            "user_id": "U4",
            "review_text": "Missing key test",
            "rating": 4,
            "review_timestamp": "2023-10-26T10:15:00Z"
        },
        {
            "review_id": "R5", # Invalid review: bad rating
            "product_id": "B00101",
            "user_id": "U5",
            "review_text": "Bad rating test",
            "rating": 6, # Invalid rating
            "review_timestamp": "2023-10-26T10:20:00Z"
        }
    ]

    # Instantiate mock clients
    mock_source = MockReviewSourceClient(mock_reviews)
    console_producer = ConsoleMessageQueueProducer()

    # Instantiate and run the ingestion service
    ingestion_service = ReviewIngestionService(mock_source, console_producer)
    # For demonstration, we'll run the loop only a couple of times
    # In a real application, this would run indefinitely.
    for _ in range(2):
        ingestion_service.start_ingestion_loop()
        break # Exit after one iteration for this example to prevent infinite loop

```
