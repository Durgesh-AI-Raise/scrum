import json
from datetime import datetime

# Overall Architecture Design for Continuous Data Ingestion.
#
# Components:
# 1.  **Review Extractor Module:** (Implemented in Task 1.1.2)
#     *   Purpose: Connects to Amazon review sources (mocked for now) and extracts raw review data.
#     *   Output: Publishes `RawReview` objects (as JSON) to the `raw_reviews_queue`.
#
# 2.  **Message Queue (`raw_reviews_queue`):**
#     *   Technology: e.g., Apache Kafka, RabbitMQ, AWS SQS/Azure Service Bus.
#     *   Purpose: Decouples the extractor from downstream processing, provides buffering and fault tolerance.
#     *   Data Format: JSON representation of `RawReview`.
#
# 3.  **Data Validation and Cleansing Service:** (To be implemented in Task 1.1.3)
#     *   Purpose: Consumes `RawReview` data from `raw_reviews_queue`.
#     *   Processes:
#         *   Schema validation against expected `RawReview` structure.
#         *   Basic data type conversions (e.g., string date to datetime object).
#         *   Handling of missing or malformed data (e.g., set defaults, log errors, move to DLQ).
#     *   Output: Publishes `CleansedReview` objects (as JSON) to the `cleansed_reviews_queue`.
#
# 4.  **Message Queue (`cleansed_reviews_queue`):**
#     *   Technology: e.g., Apache Kafka, RabbitMQ, AWS SQS/Azure Service Bus.
#     *   Purpose: Further decoupling, making cleansed data available for various consumers (abuse detection, reviewer profiling).
#     *   Data Format: JSON representation of `CleansedReview`.
#
# 5.  **Downstream Consumers:**
#     *   **Abuse Pattern Detection Service:** (US1.2 - consumes `cleansed_reviews_queue`)
#     *   **Reviewer Profiling Service:** (US1.5 - consumes `cleansed_reviews_queue`)
#     *   **Abuse Database Storage Service:** (US1.4 - consumes `cleansed_reviews_queue` and/or detection results)
#
# Data Models:
# *   `RawReview`: As defined in `review_extractor.py`.
# *   `CleansedReview`:
#     ```python
#     import json
#     from datetime import datetime
#
#     class CleansedReview:
#         def __init__(self, review_id: str, product_id: str, reviewer_id: str, stars: int, review_text: str,
#                      review_date: datetime, verified_purchase: bool, processed_timestamp: datetime = None):
#             self.review_id = review_id
#             self.product_id = product_id
#             self.reviewer_id = reviewer_id
#             self.stars = stars
#             self.review_text = review_text
#             self.review_date = review_date # datetime object
#             self.verified_purchase = verified_purchase
#             self.processed_timestamp = processed_timestamp if processed_timestamp else datetime.utcnow()
#
#         def to_json(self):
#             # Custom encoder for datetime objects
#             class DateTimeEncoder(json.JSONEncoder):
#                 def default(self, obj):
#                     if isinstance(obj, datetime):
#                         return obj.isoformat()
#                     return json.JSONEncoder.default(self, obj)
#             return json.dumps(self.__dict__, cls=DateTimeEncoder)
#
#         @classmethod
#         def from_json(cls, json_str):
#             data = json.loads(json_str)
#             # Convert ISO format string back to datetime object
#             data['review_date'] = datetime.fromisoformat(data['review_date'])
#             if 'processed_timestamp' in data and data['processed_timestamp']:
#                 data['processed_timestamp'] = datetime.fromisoformat(data['processed_timestamp'])
#             return cls(**data)
#     ```
#
# Flow:
# Raw Review Data -> Review Extractor -> `raw_reviews_queue` -> Data Validation and Cleansing Service -> `cleansed_reviews_queue` -> [Abuse Detection / Reviewer Profiling / Abuse Database]


class CleansedReview:
    def __init__(self, review_id: str, product_id: str, reviewer_id: str, stars: int, review_text: str,
                 review_date: datetime, verified_purchase: bool, processed_timestamp: datetime = None):
        self.review_id = review_id
        self.product_id = product_id
        self.reviewer_id = reviewer_id
        self.stars = stars
        self.review_text = review_text
        self.review_date = review_date
        self.verified_purchase = verified_purchase
        self.processed_timestamp = processed_timestamp if processed_timestamp else datetime.utcnow()

    def to_json(self):
        # Custom encoder for datetime objects
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return json.JSONEncoder.default(self, obj)
        return json.dumps(self.__dict__, cls=DateTimeEncoder)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        # Convert ISO format string back to datetime object
        data['review_date'] = datetime.fromisoformat(data['review_date'])
        if 'processed_timestamp' in data and data['processed_timestamp']:
            data['processed_timestamp'] = datetime.fromisoformat(data['processed_timestamp'])
        return cls(**data)
