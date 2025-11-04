import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging
# from logging.handlers import RotatingFileHandler # For local file logging example
# from pythonjsonlogger import jsonlogger # For structured JSON logging

# --- Mock Clients/Libraries for demonstration ---
# (Re-using mocks from previous tasks, assuming they are available or configured globally)
class MockStreamConsumer:
    def __init__(self, topic, bootstrap_servers):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self._records = [
            {"event_id": "e1", "timestamp": "2023-10-27T10:00:00Z", "source": "amazon_reviews",
             "payload": {"reviewId": "R001", "asin": "B001", "reviewerID": "A001", "overall": 5, "reviewText": "Great!", "reviewTime": "10 27, 2023"}},
            {"event_id": "e2", "timestamp": "2023-10-27T10:01:00Z", "source": "amazon_reviews",
             "payload": {"reviewId": "R002", "asin": "B002", "reviewerID": "A002", "overall": 4, "reviewText": "Good.", "reviewTime": "10 27, 2023"}},
            {"event_id": "e3", "timestamp": "2023-10-27T10:02:00Z", "source": "amazon_reviews",
             "payload": {"reviewId": "R003", "asin": "B003", "reviewerID": "A003", "overall": 1, "reviewText": None, "reviewTime": "10 27, 2023"}}, # Malformed
            {"event_id": "e4", "timestamp": "2023-10-27T10:03:00Z", "source": "amazon_reviews",
             "payload": {"reviewId": "R004", "asin": "B004", "reviewerID": "A004", "overall": 3, "reviewText": "Service API Down", "reviewTime": "10 27, 2023"}}, # Simulate external service failure
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
        print(f"Mock: Committed offset for {len(record_batch)} records.")

class MockS3Client:
    def upload_file(self, bucket, key, data):
        print(f"Mock: Uploaded raw data to s3://{bucket}/{key}")

class MockMessageQueueProducer:
    def send_message(self, topic, message):
        print(f"Mock: Sent message to topic '{topic}': {message.get('review_id', 'N/A')}")
        if "Service API Down" in message.get("review_text", ""):
             raise ConnectionError("Mock: External service connection failed.")


class MockDeadLetterQueueService:
    def send_to_dlq(self, record: Dict[str, Any], error_details: str):
        print(f"DLQ: Sent record {record.get('event_id', 'N/A')} to DLQ with error: {error_details}")

class MockReviewerMetadataService:
    def get_reviewer_by_id(self, reviewer_id: str) -> Optional[Dict[str, Any]]:
        # Simulate fetching reviewer data
        if reviewer_id == "A001":
            return {"reviewer_id": "A001", "reviewer_name": "John Doe", "reviewer_join_date": "2022-01-15T12:00:00Z", "total_reviews": 15, "average_rating_given": 4.2}
        elif reviewer_id == "A002":
            return {"reviewer_id": "A002", "reviewer_name": "Jane Smith", "reviewer_join_date": "2021-05-20T09:30:00Z", "total_reviews": 30, "average_rating_given": 3.9}
        # Simulate no metadata found
        return None

class MockProductMetadataService:
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        # Simulate fetching product data
        if product_id == "B001":
            return {"product_id": "B001", "product_name": "Wireless Headphones", "product_category": "Electronics", "brand": "AudioTech", "average_rating": 4.5, "total_reviews": 1200}
        elif product_id == "B002":
            return {"product_id": "B002", "product_name": "Ergonomic Office Chair", "product_category": "Office Furniture", "brand": "ComfySeats", "average_rating": 4.0, "total_reviews": 800}
        # Simulate no metadata found
        return None


# --- Centralized Logging Setup ---
# A more robust logging setup would use a proper logger with handlers,
# potentially configured via dictConfig or fileConfig.
# For this example, we'll keep it simple but demonstrate structured logging concept.

# Basic console logger for demonstration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# To enable JSON logging, you would replace the formatter with jsonlogger
# formatter = jsonlogger.JsonFormatter()
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# --- End Mock Clients/Libraries ---


class ReviewIngestionCoreLogicWithErrors:
    def __init__(self, stream_config: Dict[str, Any], s3_client: MockS3Client,
                 message_queue_producer: MockMessageQueueProducer, dlq_service: MockDeadLetterQueueService):
        self.stream_consumer = MockStreamConsumer(
            topic=stream_config['topic'],
            bootstrap_servers=stream_config['bootstrap_servers']
        )
        self.s3_client = s3_client
        self.message_queue_producer = message_queue_producer
        self.dlq_service = dlq_service
        self.logger = logger # Using the centralized logger
        self.raw_data_bucket = os.getenv("RAW_DATA_S3_BUCKET", "aris-raw-reviews")
        self.processed_data_topic = os.getenv("PROCESSED_DATA_MQ_TOPIC", "aris-processed-reviews")

    def _parse_and_validate_record(self, raw_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parses a raw stream record and performs basic validation."""
        try:
            event_payload = raw_record.get('payload', {})

            required_fields = ['reviewId', 'asin', 'reviewerID', 'overall', 'reviewText', 'reviewTime']
            for field in required_fields:
                if not event_payload.get(field):
                    self.logger.error(
                        f"Missing or empty required field '{field}'",
                        extra={
                            'event_id': raw_record.get('event_id', 'N/A'),
                            'error_type': 'DataValidationError',
                            'component': 'ReviewParser',
                            'raw_payload_snippet': str(raw_record)[:200] # Snippet for context
                        }
                    )
                    return None

            if not isinstance(event_payload['overall'], int) or not (1 <= event_payload['overall'] <= 5):
                self.logger.error(
                    f"Invalid 'overall' rating: {event_payload['overall']}",
                    extra={
                        'review_id': event_payload['reviewId'],
                        'error_type': 'DataValidationError',
                        'component': 'ReviewParser'
                    }
                )
                return None

            review_time_str = event_payload['reviewTime']
            try:
                review_timestamp = datetime.strptime(review_time_str, "%m %d, %Y").replace(tzinfo=timezone.utc)
            except ValueError as e:
                self.logger.error(
                    f"Could not parse reviewTime '{review_time_str}': {e}",
                    extra={
                        'review_id': event_payload['reviewId'],
                        'error_type': 'DateTimeParsingError',
                        'component': 'ReviewParser'
                    }
                )
                return None

            return {
                "review_id": event_payload['reviewId'],
                "raw_review_payload": raw_record,
                "product_id": event_payload['asin'],
                "reviewer_id": event_payload['reviewerID'],
                "rating": event_payload['overall'],
                "review_text": event_payload['reviewText'],
                "review_summary": event_payload.get('summary'),
                "review_timestamp": review_timestamp,
                "marketplace": event_payload.get('marketplace', 'US'),
                "ingestion_timestamp": datetime.now(timezone.utc)
            }
        except Exception as e:
            self.logger.error(
                f"Unexpected error during parsing/validation: {e}",
                exc_info=True, # Log full traceback
                extra={
                    'event_id': raw_record.get('event_id', 'N/A'),
                    'error_type': 'UnexpectedParsingError',
                    'component': 'ReviewParser'
                }
            )
            return None

    def ingest_reviews(self):
        self.logger.info("Starting core review ingestion logic.", extra={'component': 'IngestionMain'})
        for record_batch in self.stream_consumer.consume_records(batch_size=10):
            processed_records = []
            for record in record_batch:
                event_id = record.get('event_id', 'N/A')
                try:
                    # 1. Store raw data
                    raw_data_key = f"raw_reviews/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{event_id}.json"
                    self.s3_client.upload_file(self.raw_data_bucket, raw_data_key, json.dumps(record))

                    # 2. Parse and Validate
                    validated_data = self._parse_and_validate_record(record)
                    if validated_data:
                        processed_records.append(validated_data)
                        self.logger.info(
                            f"Successfully processed raw event: {event_id} -> review_id: {validated_data['review_id']}",
                            extra={
                                'event_id': event_id,
                                'review_id': validated_data['review_id'],
                                'component': 'IngestionProcessor'
                            }
                        )
                    else:
                        self.logger.warning(
                            f"Skipping malformed record (sent to DLQ if configured): {event_id}",
                            extra={
                                'event_id': event_id,
                                'error_type': 'MalformedRecordSkipped',
                                'component': 'IngestionProcessor'
                            }
                        )
                        self.dlq_service.send_to_dlq(record, "Malformed record during parsing/validation")
                except Exception as e:
                    self.logger.error(
                        f"Unhandled error during processing of individual record {event_id}: {e}",
                        exc_info=True,
                        extra={
                            'event_id': event_id,
                            'error_type': 'UnhandledIngestionError',
                            'component': 'IngestionProcessor'
                        }
                    )
                    self.dlq_service.send_to_dlq(record, f"Unhandled error: {e}")

            # 3. Hand-off processed records to the next stage (with retry/DLQ for publishing)
            successful_publishes = []
            for p_record in processed_records:
                try:
                    # Implement retry logic here for message queue publishing
                    # For simplicity, a direct call is shown
                    self.message_queue_producer.send_message(self.processed_data_topic, p_record)
                    successful_publishes.append(p_record)
                except ConnectionError as e:
                    self.logger.critical(
                        f"Failed to publish processed review {p_record['review_id']} to MQ after retries: {e}",
                        exc_info=True,
                        extra={
                            'review_id': p_record['review_id'],
                            'error_type': 'MessageQueuePublishFailure',
                            'component': 'IngestionPublisher'
                        }
                    )
                    self.dlq_service.send_to_dlq(p_record, f"Failed to publish to MQ: {e}")
                except Exception as e:
                    self.logger.error(
                        f"Unexpected error publishing review {p_record['review_id']} to MQ: {e}",
                        exc_info=True,
                        extra={
                            'review_id': p_record['review_id'],
                            'error_type': 'UnexpectedPublishError',
                            'component': 'IngestionPublisher'
                        }
                    )
                    self.dlq_service.send_to_dlq(p_record, f"Unexpected publish error: {e}")

            # 4. Commit offsets only for successfully processed and published records
            # A more nuanced approach might commit offsets for partially successful batches
            # or track individual record success/failure. For simplicity, we commit the batch
            # if all within the batch are processed or sent to DLQ.
            self.stream_consumer.commit_offset(record_batch)
            self.logger.info(f"Committed stream offset for batch containing {len(record_batch)} records.", extra={'component': 'IngestionMain'})

        self.logger.info("Finished ingesting reviews (mock stream exhausted).")


class MetadataEnrichmentServiceWithErrors:
    def __init__(self, stream_consumer: MockStreamConsumer,
                 reviewer_service: MockReviewerMetadataService,
                 product_service: MockProductMetadataService,
                 db_client: Any,
                 message_queue_producer: MockMessageQueueProducer,
                 dlq_service: MockDeadLetterQueueService):
        self.stream_consumer = stream_consumer
        self.reviewer_service = reviewer_service
        self.product_service = product_service
        self.db_client = db_client
        self.mq_producer = message_queue_producer
        self.dlq_service = dlq_service
        self.logger = logger # Using the centralized logger
        self.enriched_data_topic = os.getenv("ENRICHED_DATA_MQ_TOPIC", "aris-enriched-reviews")

    def _fetch_reviewer_metadata(self, reviewer_id: str) -> Dict[str, Any]:
        try:
            # Implement retry logic here for external API calls
            metadata = self.reviewer_service.get_reviewer_by_id(reviewer_id)
            if not metadata:
                self.logger.warning(
                    f"Could not find reviewer metadata for ID: {reviewer_id}",
                    extra={
                        'reviewer_id': reviewer_id,
                        'error_type': 'MetadataNotFound',
                        'component': 'ReviewerService'
                    }
                )
                return {}
            self.db_client.save_reviewer_metadata(metadata)
            return metadata
        except Exception as e:
            self.logger.error(
                f"Error fetching reviewer metadata for ID {reviewer_id}: {e}",
                exc_info=True,
                extra={
                    'reviewer_id': reviewer_id,
                    'error_type': 'ReviewerServiceError',
                    'component': 'ReviewerService'
                }
            )
            # Depending on severity, raise, return empty, or send to DLQ
            return {}

    def _fetch_product_metadata(self, product_id: str) -> Dict[str, Any]:
        try:
            # Implement retry logic here for external API calls
            metadata = self.product_service.get_product_by_id(product_id)
            if not metadata:
                self.logger.warning(
                    f"Could not find product metadata for ID: {product_id}",
                    extra={
                        'product_id': product_id,
                        'error_type': 'MetadataNotFound',
                        'component': 'ProductService'
                    }
                )
                return {}
            self.db_client.save_product_metadata(metadata)
            return metadata
        except Exception as e:
            self.logger.error(
                f"Error fetching product metadata for ID {product_id}: {e}",
                exc_info=True,
                extra={
                    'product_id': product_id,
                    'error_type': 'ProductServiceError',
                    'component': 'ProductService'
                }
            )
            return {}

    def enrich_reviews(self):
        self.logger.info("Starting metadata enrichment service.", extra={'component': 'EnrichmentMain'})
        for review_batch in self.stream_consumer.consume_records(batch_size=10):
            enriched_reviews = []
            for review_data in review_batch:
                review_id = review_data.get('review_id', 'N/A')
                try:
                    reviewer_id = review_data['reviewer_id']
                    product_id = review_data['product_id']

                    reviewer_metadata = self._fetch_reviewer_metadata(reviewer_id)
                    product_metadata = self._fetch_product_metadata(product_id)

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

                    self.db_client.update_enriched_review(review_data['review_id'], enriched_review)

                    self.logger.info(f"Successfully enriched review: {review_id}", extra={'review_id': review_id, 'component': 'EnrichmentProcessor'})
                except Exception as e:
                    self.logger.error(
                        f"Unhandled error during enrichment of review {review_id}: {e}",
                        exc_info=True,
                        extra={
                            'review_id': review_id,
                            'error_type': 'UnhandledEnrichmentError',
                            'component': 'EnrichmentProcessor'
                        }
                    )
                    self.dlq_service.send_to_dlq(review_data, f"Unhandled enrichment error: {e}")

            # Publish enriched reviews to the next stage
            for er in enriched_reviews:
                try:
                    self.mq_producer.send_message(self.enriched_data_topic, er)
                except ConnectionError as e:
                    self.logger.critical(
                        f"Failed to publish enriched review {er['review_id']} to MQ after retries: {e}",
                        exc_info=True,
                        extra={
                            'review_id': er['review_id'],
                            'error_type': 'EnrichedMessageQueuePublishFailure',
                            'component': 'EnrichmentPublisher'
                        }
                    )
                    self.dlq_service.send_to_dlq(er, f"Failed to publish enriched review to MQ: {e}")
                except Exception as e:
                    self.logger.error(
                        f"Unexpected error publishing enriched review {er['review_id']} to MQ: {e}",
                        exc_info=True,
                        extra={
                            'review_id': er['review_id'],
                            'error_type': 'UnexpectedEnrichedPublishError',
                            'component': 'EnrichmentPublisher'
                        }
                    )
                    self.dlq_service.send_to_dlq(er, f"Unexpected enriched publish error: {e}")

            self.stream_consumer.commit_offset(review_batch)
            self.logger.info(f"Committed stream offset for batch containing {len(review_batch)} enriched records.", extra={'component': 'EnrichmentMain'})

        self.logger.info("Finished metadata enrichment (mock stream exhausted).")

# Example Usage:
if __name__ == "__main__":
    # Setup for Ingestion Core Logic
    stream_configuration = {
        "topic": "amazon-reviews-stream",
        "bootstrap_servers": "kafka-broker-1:9092,kafka-broker-2:9092"
    }
    s3 = MockS3Client()
    mq_producer = MockMessageQueueProducer()
    dlq = MockDeadLetterQueueService()

    ingestion_service_with_errors = ReviewIngestionCoreLogicWithErrors(stream_configuration, s3, mq_producer, dlq)
    ingestion_service_with_errors.ingest_reviews()

    print("\n" + "="*50 + "\n")

    # Setup for Metadata Enrichment Service
    mock_stream_consumer_for_enrichment = MockStreamConsumer(topic="aris-processed-reviews")
    mock_reviewer_service = MockReviewerMetadataService()
    mock_product_service = MockProductMetadataService()
    mock_db_client = MockDatabaseClient() # Re-using from previous task, need to ensure methods exist
    mock_mq_producer_for_enrichment = MockMessageQueueProducer()

    enrichment_service_with_errors = MetadataEnrichmentServiceWithErrors(
        mock_stream_consumer_for_enrichment,
        mock_reviewer_service,
        mock_product_service,
        mock_db_client,
        mock_mq_producer_for_enrichment,
        dlq
    )
    enrichment_service_with_errors.enrich_reviews()
