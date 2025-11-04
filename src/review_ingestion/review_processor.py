
import json
import os
import logging
from datetime import datetime

from kafka import KafkaConsumer
import boto3

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
RAW_REVIEWS_TOPIC = os.getenv('RAW_REVIEWS_TOPIC', 'raw_reviews')
PROCESSED_REVIEW_EVENTS_TOPIC = os.getenv('PROCESSED_REVIEW_EVENTS_TOPIC', 'processed_review_events')
DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'reviews')

# AWS Clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

class ReviewProcessor:
    def __init__(self):
        self.consumer = KafkaConsumer(
            RAW_REVIEWS_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='latest', # Start consuming at the latest message
            enable_auto_commit=True,
            group_id='review-processor-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        # Placeholder for Kafka Producer if needed for PROCESSED_REVIEW_EVENTS_TOPIC.
        # For simplicity in this snippet, we'll just log the processed event.
        logging.info(f"Initialized Kafka Consumer for topic: {RAW_REVIEWS_TOPIC}")

    def _validate_review_schema(self, review_data):
        # Basic schema validation for critical fields
        required_fields = ['review_id', 'product_id', 'reviewer_id', 'rating', 'content', 'review_date']
        if not all(field in review_data for field in required_fields):
            logging.warning(f"Skipping review due to missing required fields: {review_data.get('review_id', 'N/A')}")
            return False
        if not isinstance(review_data.get('rating'), int) or not (1 <= review_data['rating'] <= 5):
            logging.warning(f"Skipping review due to invalid rating: {review_data.get('review_id', 'N/A')}")
            return False
        return True

    def process_review(self, raw_review):
        review_id = raw_review.get('review_id', 'N/A')
        try:
            if not self._validate_review_schema(raw_review):
                return

            # Add ingestion timestamp and standardize review_date
            raw_review['ingestion_timestamp'] = datetime.utcnow().isoformat()
            
            # Ensure review_date is ISO 8601
            try:
                # Attempt to parse and re-format to ensure consistency
                raw_review['review_date'] = datetime.fromisoformat(raw_review['review_date']).isoformat()
            except ValueError:
                logging.warning(f"Review date for {review_id} is not ISO 8601, attempting to use as-is: {raw_review['review_date']}")
            
            # Set initial flagging status
            raw_review['is_flagged'] = False

            # Store in DynamoDB
            table.put_item(Item=raw_review)
            logging.info(f"Successfully stored review: {review_id} to DynamoDB.")

            # Publish a lighter event for downstream monitoring
            processed_event = {
                'review_id': raw_review['review_id'],
                'product_id': raw_review['product_id'],
                'reviewer_id': raw_review['reviewer_id'],
                'review_date': raw_review['review_date'],
                'ingestion_timestamp': raw_review['ingestion_timestamp']
            }
            # In a real scenario, you'd use a KafkaProducer here
            # self.producer.send(PROCESSED_REVIEW_EVENTS_TOPIC, value=processed_event)
            logging.info(f"Published processed event for review: {review_id} to {PROCESSED_REVIEW_EVENTS_TOPIC}.")

        except Exception as e:
            logging.error(f"Error processing review {review_id}: {e}", exc_info=True)

    def run(self):
        logging.info(f"Starting Review Processor, consuming from {RAW_REVIEWS_TOPIC}...")
        for message in self.consumer:
            logging.info(f"Received message from topic: {message.topic}, offset: {message.offset}")
            self.process_review(message.value)

if __name__ == "__main__":
    processor = ReviewProcessor()
    processor.run()
