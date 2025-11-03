import json
import logging
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
# import jsonschema # Uncomment and install if more robust schema validation is needed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka configuration
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC_RAW = 'amazon_reviews_raw'
KAFKA_TOPIC_PROCESSED = 'amazon_reviews_processed'
KAFKA_TOPIC_DLQ = 'amazon_reviews_dlq'

# Define the expected schema for a valid review
# This is a simplified version; a full implementation might use a formal JSON Schema
# and a library like jsonschema to validate against it.
EXPECTED_REVIEW_SCHEMA = {
    "reviewId": str,
    "productId": str,
    "userId": str,
    "rating": int,
    "title": str,
    "text": str,
    "reviewDate": str, # Expecting ISO 8601 string
    "verifiedPurchase": bool,
    "productCategory": str,
    "reviewerAccountAgeDays": int
}

def validate_review(review_data):
    """
    Validates the incoming review data. Checks for required fields and basic data types.
    Returns (True, validated_data) if valid, (False, error_message) otherwise.
    """
    if not isinstance(review_data, dict):
        return False, "Review data is not a dictionary."

    # Check for presence of required fields and their basic types
    for field, expected_type in EXPECTED_REVIEW_SCHEMA.items():
        if field not in review_data:
            return False, f"Missing required field: {field}"
        if not isinstance(review_data[field], expected_type):
            return False, f"Field {field} has incorrect type. Expected {expected_type.__name__}, got {type(review_data[field]).__name__}"
    
    # Specific validation for 'rating' range
    rating = review_data.get("rating")
    if not (1 <= rating <= 5):
        return False, f"Rating must be between 1 and 5, got {rating}"

    # Basic date format check (can be expanded with regex or datetime parsing)
    try:
        datetime.fromisoformat(review_data.get("reviewDate"))
    except ValueError:
        return False, f"Invalid date format for reviewDate: {review_data.get('reviewDate')}. Expected ISO 8601."

    return True, review_data

def run_parser_consumer():
    consumer = KafkaConsumer(
        KAFKA_TOPIC_RAW,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='review-parser-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    logging.info(f"Listening for messages on topic {KAFKA_TOPIC_RAW}...")

    for message in consumer:
        review_raw = message.value
        if review_raw is None:
            logging.warning(f"Received a null message at offset {message.offset}. Skipping.")
            continue

        try:
            is_valid, processed_data_or_error = validate_review(review_raw)
            
            if is_valid:
                producer.send(KAFKA_TOPIC_PROCESSED, processed_data_or_error)
                logging.info(f"Successfully processed and forwarded review: {processed_data_or_error.get('reviewId', 'N/A')}")
            else:
                logging.warning(f"Validation failed for review (offset {message.offset}): {processed_data_or_error}. Original message: {review_raw}. Sending to DLQ.")
                dlq_message = {
                    "original_message": review_raw,
                    "error": processed_data_or_error,
                    "timestamp": datetime.now().isoformat()
                }
                producer.send(KAFKA_TOPIC_DLQ, dlq_message)

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON from message (offset {message.offset}): {message.value}. Error: {e}. Sending to DLQ.")
            dlq_message = {
                "original_message_bytes": message.value.decode('utf-8', errors='ignore'),
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            producer.send(KAFKA_TOPIC_DLQ, dlq_message)
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing message (offset {message.offset}): {review_raw}. Error: {e}. Sending to DLQ.")
            dlq_message = {
                "original_message": review_raw,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            producer.send(KAFKA_TOPIC_DLQ, dlq_message)

if __name__ == "__main__":
    run_parser_consumer()
