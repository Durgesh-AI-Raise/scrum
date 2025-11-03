# Sprint Backlog - User Story 1.4: Develop mechanism to flag suspicious reviews for storage

### Implementation Plan
*   **Consume Flagged Review Events:** Create a new microservice, `FlaggedReviewStorageService`, that subscribes to the `suspicious_review_flagged_events` topic (published by US1.3) in the message queue.
*   **Extract Metadata:** Upon receiving a `suspicious_review_flagged_event`, extract essential metadata about the flagged review, including `review_id`, the `flagged_by_rules`, and the `flagging_timestamp`.
*   **Store Flagged Reviews:** Persist this metadata into a dedicated data store for flagged reviews. This storage should be optimized for efficient retrieval by content moderators and designed to be extensible for future attributes.

### Data Models
*   **`SuspiciousReviewFlaggedEvent` (Consumed):**
    ```json
    {
        "review_id": "string",
        "flagged_by_rules": ["string"], // e.g., ["RapidSubmissionVelocity", "RepetitivePhrases"]
        "flagging_timestamp": "string" // ISO 8601 datetime
    }
    ```
*   **`FlaggedReview` (Stored Model):**
    ```python
    class FlaggedReview:
        id: str # Primary key, could be same as review_id or a new UUID
        review_id: str
        flagged_by_rules: List[str]
        flagging_timestamp: datetime
        # Additional fields for future: moderator_id, resolution_status, notes etc.
    ```

### Architecture
*   **`FlaggedReviewStorageService`:** A new, independent Python-based microservice.
*   **Message Queue (Kafka/RabbitMQ):** Used for consuming `suspicious_review_flagged_events`, ensuring asynchronous processing.
*   **Data Store:** PostgreSQL (or similar relational database) for durable storage of flagged review metadata. This could reside in a separate schema or table for optimal access by the moderator dashboard.

### Assumptions/Technical Decisions
*   The `SuspiciousReviewDetectorService` (US1.3) is reliably publishing `suspicious_review_flagged_events` to the message queue.
*   The `review_id` will be used as a primary identifier to link back to the original review content if a moderator needs to view full details.
*   The chosen data store is suitable for high read throughput, as moderators will frequently query flagged reviews.
*   The initial data model for `FlaggedReview` is minimal but designed to be easily extensible in subsequent sprints.
*   Error handling for database operations will be implemented, potentially including retry mechanisms or dead-letter queues for failed storage attempts.

### Code Snippets/Pseudocode (`app/services/flagged_review_storage_service.py`)
```python
import json
from datetime import datetime
from typing import List
import uuid

# Placeholder for a message queue consumer and database client
# from some_mq_library import MessageQueueConsumer
# from some_db_library import FlaggedReviewRepository

class FlaggedReviewStorageService:
    def __init__(self):
        # self.flagged_review_consumer = MessageQueueConsumer('suspicious_review_flagged_events')
        # self.flagged_review_repo = FlaggedReviewRepository()
        pass

    def start_listening(self):
        print("Starting FlaggedReviewStorageService, listening for suspicious_review_flagged_events...")
        # self.flagged_review_consumer.listen(self._process_flagged_review_event)
        self._simulate_process_event()

    def _simulate_process_event(self):
        # Simulate a flagged event from the detector service
        mock_flagged_event = {
            "review_id": "review_12345",
            "flagged_by_rules": ["RapidSubmissionVelocity", "RepetitivePhrases"],
            "flagging_timestamp": "2025-01-01T10:05:00Z"
        }
        print(f"Simulating processing flagged review event for: {mock_flagged_event['review_id']}")
        self._process_flagged_review_event(json.dumps(mock_flagged_event))

    def _process_flagged_review_event(self, message: str):
        event_data = json.loads(message)
        review_id = event_data['review_id']
        flagged_by_rules = event_data['flagged_by_rules']
        flagging_timestamp = datetime.fromisoformat(event_data['flagging_timestamp'].replace('Z', '+00:00'))

        flagged_review = {
            "id": str(uuid.uuid4()), # Generate a unique ID for the flagged entry
            "review_id": review_id,
            "flagged_by_rules": flagged_by_rules,
            "flagging_timestamp": flagging_timestamp
        }

        # Store in database (Pseudocode)
        # try:
        #     self.flagged_review_repo.save(flagged_review)
        #     print(f"Successfully stored flagged review: {review_id}")
        # except Exception as e:
        #     print(f"Database error storing flagged review {review_id}: {e}")
        #     # Log error, potentially send to a dead-letter queue
        print(f"Simulating DB save for flagged review: {flagged_review}")

if __name__ == '__main__':
    storage_service = FlaggedReviewStorageService()
    storage_service.start_listening()
```