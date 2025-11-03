# Sprint Backlog - User Story 1.3: Implement rules engine for pattern detection

### Implementation Plan
*   **Consume Review Ingested Events:** Develop a new microservice, `SuspiciousReviewDetectorService`, that will subscribe to the `review_ingested_events` topic (published by US1.2) in the message queue.
*   **Data Enrichment:** Upon receiving a `review_ingested_event`, the service will retrieve additional necessary data for rule evaluation from the primary data store. This includes user history (e.g., past review submission timestamps, user creation timestamp) and product statistics (e.g., average rating, standard deviation, total review count).
*   **Apply Rules:** Implement the detection logic for the MVP suspicious review patterns defined in US1.1:
    1.  **Rapid Submission Velocity:** Check if a new account submits more than 5 reviews within a 60-minute window.
    2.  **Unusual Rating Deviation:** Determine if the review's rating significantly deviates (e.g., >2 standard deviations) from the product's average, given sufficient review history.
    3.  **Repetitive Phrases:** Perform basic keyword matching to find multiple instances of predefined suspicious phrases within the review text.
*   **Flag Reviews:** If any of the rules are triggered, the review will be flagged as suspicious.
*   **Publish Flagged Event:** A `suspicious_review_flagged_event` will be published to a new message queue topic (e.g., `suspicious_review_flagged_events`), containing the `review_id`, the specific rules that were triggered, and a flagging timestamp. This event will be consumed by downstream services (e.g., for storage in US1.4).

### Data Models
*   **`ReviewIngestedEvent` (Consumed):**
    ```json
    {
        "review_id": "string",
        "product_id": "string",
        "user_id": "string",
        "rating": "integer",
        "review_text": "string", // Full text needed for pattern matching
        "submission_timestamp": "string" // ISO 8601 datetime
        "user_creation_timestamp": "string" // ISO 8601 datetime, if available
    }
    ```
*   **`SuspiciousReviewFlaggedEvent` (Produced):**
    ```python
    class SuspiciousReviewFlaggedEvent:
        review_id: str
        flagged_by_rules: List[str] # e.g., ["RapidSubmissionVelocity", "UnusualRatingDeviation"]
        flagging_timestamp: datetime # Timestamp when the review was flagged
        # Potentially add more context like a severity score or rule-specific details
    ```
*   **Internal Data for Rules (Fetched from Database/Cache):**
    *   **User History:** `user_id`, `review_submission_timestamps` (list of `datetime`), `user_creation_timestamp`
    *   **Product Stats:** `product_id`, `average_rating`, `standard_deviation`, `total_reviews_count`

### Architecture
*   **`SuspiciousReviewDetectorService`:** A new, independent Python-based microservice (e.g., using Flask or FastAPI for internal components, and a message queue client for event processing).
*   **Message Queue (Kafka/RabbitMQ):** Used for consuming `review_ingested_events` and publishing `suspicious_review_flagged_events`, ensuring asynchronous and decoupled communication.
*   **Data Store (PostgreSQL):** The service will interact with the primary database to fetch user review history and product statistics required for rule evaluation.
*   **Caching Layer (Optional, Future):** For high-throughput scenarios, a caching layer (e.g., Redis) could be introduced to store frequently accessed user histories or product statistics to reduce database load.

### Assumptions/Technical Decisions
*   The `ReviewIngestionService` (US1.2) is successfully publishing `review_ingested_events` with complete review data, including `review_text` and `user_creation_timestamp` if available.
*   A reliable message queue (e.g., Kafka) is in place and correctly configured for event consumption and production.
*   Efficient database queries for user review history and product statistics will be available. These queries should be optimized for performance as this service will be a critical part of the detection pipeline.
*   The MVP rules are hardcoded within the service. Future iterations may involve externalizing rule configuration for dynamic updates.
*   The service is designed to be stateless, allowing for easy horizontal scaling to handle increased review ingestion volume.
*   Robust error handling will be implemented for message queue interactions and database lookups to ensure the service's resilience and prevent processing failures.

### Code Snippets/Pseudocode (`app/services/suspicious_review_detector_service.py`)
```python
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Placeholder for a message queue consumer and producer
# from some_mq_library import MessageQueueConsumer, MessageQueueProducer
# from some_db_library import ReviewRepository, UserRepository, ProductRepository

class SuspiciousReviewDetectorService:
    def __init__(self):
        # self.review_consumer = MessageQueueConsumer('review_ingested_events')
        # self.flagged_review_producer = MessageQueueProducer('suspicious_review_flagged_events')
        # self.review_repo = ReviewRepository() # To fetch full review, user history
        # self.user_repo = UserRepository() # To fetch user creation timestamp, other user details
        # self.product_repo = ProductRepository() # To fetch product average rating, std dev
        self.suspicious_keywords = ["best product ever!!!", "super great", "must buy", "amazing quality"] # From US1.1

    def start_listening(self):
        print("Starting SuspiciousReviewDetectorService, listening for review_ingested_events...")
        # self.review_consumer.listen(self._process_review_event)
        # For demonstration purposes, simulate processing a single event
        self._simulate_process_event()

    def _simulate_process_event(self):
        # Simulate an event from the ingestion service with data that triggers rules
        mock_review_event = {
            "review_id": "review_12345",
            "product_id": "prod_abc",
            "user_id": "user_101",
            "rating": 1, # Low rating for high average product
            "review_text": "This is the best product ever!!! I must buy more. super great!", # Multiple keywords
            "submission_timestamp": "2025-01-01T10:00:00Z",
            "user_creation_timestamp": "2025-01-01T09:30:00Z" # User created 30 mins ago
        }
        print(f"Simulating processing review: {mock_review_event['review_id']}")
        self._process_review_event(json.dumps(mock_review_event))

    def _process_review_event(self, message: str):
        review_data = json.loads(message)
        review_id = review_data['review_id']
        product_id = review_data['product_id']
        user_id = review_data['user_id']
        rating = review_data['rating']
        review_text = review_data['review_text']
        submission_timestamp = datetime.fromisoformat(review_data['submission_timestamp'].replace('Z', '+00:00'))
        user_creation_timestamp_str = review_data.get('user_creation_timestamp')
        user_creation_timestamp = datetime.fromisoformat(user_creation_timestamp_str.replace('Z', '+00:00')) if user_creation_timestamp_str else None

        flagged_rules = []

        # --- Simulate fetching additional data for rules ---
        # In a real system, these would be database/cache calls:
        # user_reviews_history = self._get_user_review_history(user_id)
        # product_stats = self._get_product_statistics(product_id)

        # For the mock event, let's create simulated data that triggers rules
        simulated_user_history = [
            datetime.fromisoformat("2025-01-01T09:35:00Z"), # 5 mins after creation
            datetime.fromisoformat("2025-01-01T09:40:00Z"), # 10 mins after creation
            datetime.fromisoformat("2025-01-01T09:45:00Z"), # 15 mins after creation
            datetime.fromisoformat("2025-01-01T09:50:00Z"), # 20 mins after creation
            datetime.fromisoformat("2025-01-01T09:55:00Z")  # 25 mins after creation
        ] # 5 reviews submitted within 20 mins before the current review
        simulated_product_stats = {
            "average_rating": 4.5,
            "standard_deviation": 0.3,
            "total_reviews_count": 150
        }

        # Apply Rule 1: Rapid Submission Velocity
        if self._check_rapid_submission_velocity(user_id, submission_timestamp, user_creation_timestamp, simulated_user_history):
            flagged_rules.append("RapidSubmissionVelocity")

        # Apply Rule 2: Unusual Rating Deviation
        if self._check_unusual_rating_deviation(product_id, rating, simulated_product_stats):
            flagged_rules.append("UnusualRatingDeviation")

        # Apply Rule 3: Repetitive Phrases
        if self._check_repetitive_phrases(review_text): # For MVP, user history not directly used here
            flagged_rules.append("RepetitivePhrases")

        if flagged_rules:
            print(f"Review {review_id} flagged by rules: {flagged_rules}")
            flagged_event = {
                "review_id": review_id,
                "flagged_by_rules": flagged_rules,
                "flagging_timestamp": datetime.now().isoformat()
            }
            # self.flagged_review_producer.publish(flagged_event)
            print(f"Simulating publish of suspicious_review_flagged_event for review: {review_id}")
        else:
            print(f"Review {review_id} passed all suspicious pattern checks.")

    # --- Rule Implementations ---
    def _get_user_review_history(self, user_id: str) -> List[datetime]:
        # Pseudocode: Fetch review submission timestamps for the user from database
        # Example: return [r.submission_timestamp for r in self.review_repo.get_by_user_id(user_id)]
        return [] # Placeholder for actual database call

    def _get_product_statistics(self, product_id: str) -> Dict:
        # Pseudocode: Fetch average rating, std dev, total review count for product from database
        # Example: return self.product_repo.get_statistics(product_id)
        return {} # Placeholder for actual database call

    def _check_rapid_submission_velocity(self, user_id: str, current_review_timestamp: datetime, user_creation_timestamp: datetime, user_reviews_history: List[datetime]) -> bool:
        """
        Rule 1: Rapid Submission Velocity
        Criteria:
        * User Account Age: Less than 24 hours old.
        * Review Count: Submits more than 5 reviews (including current one).
        * Time Window: Within a 60-minute period (relative to current review).
        """
        if not user_creation_timestamp or (current_review_timestamp - user_creation_timestamp).total_seconds() / 3600 >= 24:
            return False # User account is too old or creation timestamp not available

        recent_reviews_count = 0
        time_window_start = current_review_timestamp - timedelta(minutes=60)

        for timestamp in user_reviews_history:
            if time_window_start <= timestamp < current_review_timestamp:
                recent_reviews_count += 1

        # Add the current review to the count
        recent_reviews_count += 1
        print(f"  User {user_id}: {recent_reviews_count} reviews in last 60 mins (created { (current_review_timestamp - user_creation_timestamp).total_seconds() / 3600 :.2f} hours ago)")
        return recent_reviews_count > 5

    def _check_unusual_rating_deviation(self, product_id: str, review_rating: int, product_stats: Dict) -> bool:
        """
        Rule 2: Unusual Rating Deviation
        Criteria:
        * Product Review Count: Product has more than 100 existing reviews.
        * Rating Deviation: The review's rating is more than 2 standard deviations away from the product's current average rating.
        """
        total_reviews_count = product_stats.get("total_reviews_count", 0)
        if total_reviews_count <= 100:
            print(f"  Product {product_id}: Not enough reviews ({total_reviews_count}) for deviation check.")
            return False # Not enough reviews for statistical significance

        avg_rating = product_stats.get("average_rating")
        std_dev = product_stats.get("standard_deviation")

        if avg_rating is None or std_dev is None or std_dev == 0:
            print(f"  Product {product_id}: Cannot calculate deviation (avg_rating or std_dev missing/zero).")
            return False # Cannot calculate deviation

        z_score = (review_rating - avg_rating) / std_dev
        print(f"  Product {product_id}: Review rating {review_rating}, Avg rating {avg_rating}, Std dev {std_dev}, Z-score {z_score:.2f}")
        return abs(z_score) > 2

    def _check_repetitive_phrases(self, review_text: str) -> bool:
        """
        Rule 3: Repetitive Phrases (Basic Keyword Matching)
        Criteria:
        * The presence of more than one instance of a suspicious keyword/phrase in a single review.
        """
        detected_keywords_count = 0
        for keyword in self.suspicious_keywords:
            if keyword.lower() in review_text.lower():
                detected_keywords_count += 1
        print(f"  Review text contains {detected_keywords_count} suspicious keywords.")
        return detected_keywords_count > 1 # Simple MVP: more than one suspicious keyword in current review

if __name__ == '__main__':
    detector = SuspiciousReviewDetectorService()
    detector.start_listening()
```