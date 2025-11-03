## Sprint Backlog - User Story 2.4: Implement back-end logic to store customer reports

### Implementation Plan
*   **Consume Customer Report Events:** Create a new microservice, `CustomerReportStorageService`, that subscribes to the `customer_abuse_reports_events` topic (published by US2.3) in the message queue.
*   **Extract Data:** Upon receiving a `CustomerReportEvent`, extract all relevant fields: `report_id`, `review_id`, `reason`, `comment` (optional), `reporting_user_id` (optional), and `report_timestamp`.
*   **Store Customer Reports:** Persist this report data into a dedicated data store for customer-reported abuse. This storage should link back to the original review and be optimized for moderator retrieval.
*   **No immediate action/event:** For MVP, simply store the report. Future sprints might involve publishing an event for immediate moderator notification or analysis.

### Data Models
*   **`CustomerReportEvent` (Consumed):**
    ```json
    {
        "report_id": "string",               // Unique ID generated for this specific report
        "review_id": "string",
        "reason": "string",
        "comment": "string",                 // Optional detailed comment from the user
        "reporting_user_id": "string",       // Optional, ID of the user submitting the report (if logged in)
        "report_timestamp": "string"         // ISO 8601 datetime
    }
    ```
*   **`CustomerReport` (Stored Model):**
    ```python
    class CustomerReport:
        id: str                 # Primary key, same as report_id
        review_id: str
        reason: str
        comment: Optional[str]
        reporting_user_id: Optional[str]
        report_timestamp: datetime
        status: str = "PENDING" # Initial status, can be updated by moderators (e.g., "RESOLVED", "DISMISSED")
        # Additional fields for future: moderator_id, resolution_timestamp, notes etc.
    ```

### Architecture
*   **`CustomerReportStorageService`:** A new, independent Python-based microservice.
*   **Message Queue (Kafka/RabbitMQ):** Used for consuming `customer_abuse_reports_events`.
*   **Data Store:** PostgreSQL (or similar relational database) for durable storage of customer abuse reports. This could be a separate table or schema within the main database or a dedicated database.

### Assumptions/Technical Decisions
*   The `CustomerReportingService` (US2.3) is reliably publishing `customer_abuse_reports_events` to the message queue.
*   The `report_id` from the incoming event will be used as the primary key for the stored report.
*   The service will focus solely on storage; any further actions (e.g., notifying moderators) are out of scope for this MVP task.
*   Error handling for database operations will be implemented, including retry mechanisms or dead-letter queues for failed storage attempts.
*   The service is designed to be stateless for scalability.

### Code Snippets/Pseudocode (`app/services/customer_report_storage_service.py`)
```python
import json
from datetime import datetime
from typing import Optional

# Placeholder for a message queue consumer and database client
# from some_mq_library import MessageQueueConsumer
# from some_db_library import CustomerReportRepository

class CustomerReportStorageService:
    def __init__(self):
        # self.report_consumer = MessageQueueConsumer('customer_abuse_reports_events')
        # self.customer_report_repo = CustomerReportRepository()
        pass

    def start_listening(self):
        print("Starting CustomerReportStorageService, listening for customer_abuse_reports_events...")
        # self.report_consumer.listen(self._process_customer_report_event)
        self._simulate_process_event()

    def _simulate_process_event(self):
        # Simulate an event from the API endpoint
        mock_report_event = {
            "report_id": "report_abc-123",
            "review_id": "review_456",
            "reason": "spam",
            "comment": "This review contains unsolicited advertisements for another product.",
            "reporting_user_id": "user_789",
            "report_timestamp": "2025-01-02T15:30:00Z"
        }
        print(f"Simulating processing customer report event for: {mock_report_event['report_id']}")
        self._process_customer_report_event(json.dumps(mock_report_event))

    def _process_customer_report_event(self, message: str):
        event_data = json.loads(message)
        report_id = event_data['report_id']
        review_id = event_data['review_id']
        reason = event_data['reason']
        comment = event_data.get('comment')
        reporting_user_id = event_data.get('reporting_user_id')
        report_timestamp = datetime.fromisoformat(event_data['report_timestamp'].replace('Z', '+00:00'))

        customer_report = {
            "id": report_id,
            "review_id": review_id,
            "reason": reason,
            "comment": comment,
            "reporting_user_id": reporting_user_id,
            "report_timestamp": report_timestamp,
            "status": "PENDING" # Initial status
        }

        # Store in database (Pseudocode)
        # try:
        #     self.customer_report_repo.save(customer_report)
        #     print(f"Successfully stored customer report: {report_id}")
        # except Exception as e:
        #     print(f"Database error storing customer report {report_id}: {e}")
        #     # Log error, potentially send to a dead-letter queue
        print(f"Simulating DB save for customer report: {customer_report}")

if __name__ == '__main__':
    storage_service = CustomerReportStorageService()
    storage_service.start_listening()
