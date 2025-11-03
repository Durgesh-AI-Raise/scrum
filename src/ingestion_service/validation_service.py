# Pseudocode for Data Validation Service (Python)
from kafka import KafkaConsumer, KafkaProducer
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

consumer = KafkaConsumer(
    'raw_reviews',
    bootstrap_servers=['kafka:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='validation_service_group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def validate_review(review_data):
    errors = []
    if not isinstance(review_data, dict):
        errors.append("Review data is not a dictionary.")
        return False, errors

    # Check for mandatory fields
    required_fields = ['product_id', 'user_id', 'review_text', 'rating', 'timestamp']
    for field in required_fields:
        if field not in review_data or not review_data[field]:
            errors.append(f"Missing or empty required field: {field}")

    # Check data types and basic ranges
    if 'rating' in review_data and not isinstance(review_data['rating'], int):
        errors.append("Rating must be an integer.")
    elif 'rating' in review_data and not (1 <= review_data['rating'] <= 5):
        errors.append("Rating must be between 1 and 5.")

    if 'review_text' in review_data and not isinstance(review_data['review_text'], str):
        errors.append("Review text must be a string.")
    elif 'review_text' in review_data and len(review_data['review_text']) > 5000: # Example max length
        errors.append("Review text exceeds maximum allowed length.")

    return not bool(errors), errors

if __name__ == '__main__':
    for message in consumer:
        review = message.value
        is_valid, errors = validate_review(review)

        if is_valid:
            producer.send('validated_reviews', review)
            logger.info(f"Successfully validated and sent review: {review.get('review_id', 'N/A')}")
        else:
            error_payload = {
                "original_data": json.dumps(review),
                "error_timestamp": datetime.utcnow().isoformat() + 'Z',
                "validation_errors": errors
            }
            producer.send('dead_letter_queue_reviews', error_payload)
            logger.warning(f"Invalid review data received. Errors: {errors}. Sent to DLQ.")
        producer.flush()
