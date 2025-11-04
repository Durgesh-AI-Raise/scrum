import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# --- Mock Clients/Libraries for demonstration (similar to previous task) ---
class MockDatabaseClient:
    def save_reviewer_metadata(self, metadata: Dict[str, Any]):
        print(f"Mock DB: Saved reviewer metadata for {metadata['reviewer_id']}")

    def save_product_metadata(self, metadata: Dict[str, Any]):
        print(f"Mock DB: Saved product metadata for {metadata['product_id']}")

    def update_enriched_review(self, review_id: str, enriched_data: Dict[str, Any]):
        print(f"Mock DB: Updated review {review_id} with enriched data.")

class MockReviewerMetadataService:
    def get_reviewer_by_id(self, reviewer_id: str) -> Optional[Dict[str, Any]]:
        # Simulate fetching reviewer data
        if reviewer_id == "A001":
            return {"reviewer_id": "A001", "reviewer_name": "John Doe", "reviewer_join_date": "2022-01-15T12:00:00Z", "total_reviews": 15, "average_rating_given": 4.2}
        elif reviewer_id == "A002":
            return {"reviewer_id": "A002", "reviewer_name": "Jane Smith", "reviewer_join_date": "2021-05-20T09:30:00Z", "total_reviews": 30, "average_rating_given": 3.9}
        elif reviewer_id == "A003": # For malformed data from previous task
            return {"reviewer_id": "A003", "reviewer_name": "Alice Brown", "reviewer_join_date": "2023-01-01T00:00:00Z", "total_reviews": 5, "average_rating_given": 2.5}
        return None

class MockProductMetadataService:
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        # Simulate fetching product data
        if product_id == "B001":
            return {"product_id": "B001", "product_name": "Wireless Headphones", "product_category": "Electronics", "brand": "AudioTech", "average_rating": 4.5, "total_reviews": 1200}
        elif product_id == "B002":
            return {"product_id": "B002", "product_name": "Ergonomic Office Chair", "product_category": "Office Furniture", "brand": "ComfySeats", "average_rating": 4.0, "total_reviews": 800}
        elif product_id == "B003": # For malformed data from previous task
            return {"product_id": "B003", "product_name": "Fitness Tracker", "product_category": "Wearable Tech", "brand": "FitLife", "average_rating": 3.0, "total_reviews": 300}
        return None

class MockStreamConsumer:
    def __init__(self, topic):
        self.topic = topic
        # Simulating records from the previous ingestion step
        self._records = [
            {"review_id": "R001", "product_id": "B001", "reviewer_id": "A001", "rating": 5, "review_text": "Great!", "review_timestamp": datetime.now(timezone.utc).isoformat()},
            {"review_id": "R002", "product_id": "B002", "reviewer_id": "A002", "rating": 4, "review_text": "Good.", "review_timestamp": datetime.now(timezone.utc).isoformat()},
            {"review_id": "R003", "product_id": "B003", "reviewer_id": "A003", "rating": 1, "review_text": "Horrible!", "review_timestamp": datetime.now(timezone.utc).isoformat()},
            {"review_id": "R004", "product_id": "BXXX", "reviewer_id": "AXXX", "rating": 3, "review_text": "Okay", "review_timestamp": datetime.now(timezone.utc).isoformat()} # No metadata
        ]
        self._offset = 0

    def consume_records(self, batch_size=1):
        if self._offset < len(self._records):
            records_to_return = self._records[self._offset : self._offset + batch_size]
            self._offset += len(records_to_return)
            yield records_to_return
        else:
            return

    def commit_offset(self, record_batch):
        print(f"Mock: Committed offset for {len(record_batch)} records on topic {self.topic}.")

class MockMessageQueueProducer:
    def send_message(self, topic, message):
        print(f"Mock: Sent enriched message to topic '{topic}': {message['review_id']}")

class Logger:
    def info(self, message):
        print(f"[INFO] {message}")
    def error(self, message):
        print(f"[ERROR] {message}")

def get_logger(name):
    return Logger()
# --- End Mock Clients/Libraries ---


class MetadataEnrichmentService:
    def __init__(self,
                 stream_consumer: MockStreamConsumer,
                 reviewer_service: MockReviewerMetadataService,
                 product_service: MockProductMetadataService,
                 db_client: MockDatabaseClient,
                 message_queue_producer: MockMessageQueueProducer):
        self.stream_consumer = stream_consumer
        self.reviewer_service = reviewer_service
        self.product_service = product_service
        self.db_client = db_client
        self.mq_producer = message_queue_producer
        self.logger = get_logger("MetadataEnrichmentService")
        self.enriched_data_topic = os.getenv("ENRICHED_DATA_MQ_TOPIC", "aris-enriched-reviews")

    def _fetch_reviewer_metadata(self, reviewer_id: str) -> Dict[str, Any]:
        metadata = self.reviewer_service.get_reviewer_by_id(reviewer_id)
        if not metadata:
            self.logger.warning(f"Could not find reviewer metadata for ID: {reviewer_id}")
            return {}
        # Potentially store/update in DB if it's the first time or data is stale
        self.db_client.save_reviewer_metadata(metadata) # Mock for persistence
        return metadata

    def _fetch_product_metadata(self, product_id: str) -> Dict[str, Any]:
        metadata = self.product_service.get_product_by_id(product_id)
        if not metadata:
            self.logger.warning(f"Could not find product metadata for ID: {product_id}")
            return {}
        # Potentially store/update in DB if it's the first time or data is stale
        self.db_client.save_product_metadata(metadata) # Mock for persistence
        return metadata

    def enrich_reviews(self):
        self.logger.info("Starting metadata enrichment service...")
        for review_batch in self.stream_consumer.consume_records(batch_size=10):
            enriched_reviews = []
            for review_data in review_batch:
                try:
                    reviewer_id = review_data['reviewer_id']
                    product_id = review_data['product_id']

                    reviewer_metadata = self._fetch_reviewer_metadata(reviewer_id)
                    product_metadata = self._fetch_product_metadata(product_id)

                    # Combine original review data with metadata
                    enriched_review = {
                        **review_data,
                        "reviewer_name": reviewer_metadata.get("reviewer_name"),
                        "reviewer_join_date": reviewer_metadata.get("reviewer_join_date"),
                        "total_reviewer_reviews": reviewer_metadata.get("total_reviews"),
                        "average_rating_given_by_reviewer": reviewer_metadata.get("average_rating_given"),
                        "product_name": product_metadata.get("product_name"),
                        "product_category": product_metadata.get("product_category"),
                        "product_brand": product_metadata.get("brand"),
                        "product_average_rating": product_metadata.get("average_rating"),
                        "product_total_reviews": product_metadata.get("total_reviews"),
                        "enrichment_timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    enriched_reviews.append(enriched_review)

                    # Update review in main DB with enriched data
                    self.db_client.update_enriched_review(review_data['review_id'], enriched_review)

                    self.logger.info(f"Successfully enriched review: {review_data['review_id']}")
                except Exception as e:
                    self.logger.error(f"Error enriching review {review_data.get('review_id', 'N/A')}: {e}")
                    # If enrichment fails, we might still want to pass the original review through
                    # or send to a DLQ. For now, we skip and log.

            # Publish enriched reviews to the next stage
            for er in enriched_reviews:
                self.mq_producer.send_message(self.enriched_data_topic, er)

            self.stream_consumer.commit_offset(review_batch)

        self.logger.info("Finished metadata enrichment (mock stream exhausted).")

# Example Usage:
# if __name__ == "__main__":
#     mock_stream_consumer = MockStreamConsumer(topic="aris-processed-reviews")
#     mock_reviewer_service = MockReviewerMetadataService()
#     mock_product_service = MockProductMetadataService()
#     mock_db_client = MockDatabaseClient()
#     mock_mq_producer = MockMessageQueueProducer()

#     enrichment_service = MetadataEnrichmentService(
#         mock_stream_consumer,
#         mock_reviewer_service,
#         mock_product_service,
#         mock_db_client,
#         mock_mq_producer
#     )
#     enrichment_service.enrich_reviews()