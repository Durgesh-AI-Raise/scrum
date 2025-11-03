
from confluent_kafka import Consumer, KafkaException
import json
import os
import boto3
import uuid
from datetime import datetime

# Configuration
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC', 'amazon_reviews_stream')
S3_BUCKET = os.environ.get('S3_BUCKET', 'amazon-review-integrity-guardian-staging')
S3_BUCKET_DLQ = os.environ.get('S3_BUCKET_DLQ', 'amazon-review-integrity-guardian-dlq')
S3_PREFIX = 'realtime_reviews/'

s3_client = boto3.client('s3')

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result. """
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")

def log_to_dlq(message_value, error_type, error_details=""):
    dlq_key = f"dlq/{error_type}/{datetime.utcnow().isoformat()}-{uuid.uuid4()}.json"
    error_record = {
        "original_message": message_value,
        "error_type": error_type,
        "error_details": error_details,
        "timestamp": datetime.utcnow().isoformat()
    }
    s3_client.put_object(
        Bucket=S3_BUCKET_DLQ,
        Key=dlq_key,
        Body=json.dumps(error_record).encode('utf-8')
    )
    print(f"Logged error to DLQ: {dlq_key}")

def process_message(message_value):
    """
    Processes a single Kafka message, performs basic validation, and writes to S3.
    """
    try:
        review_data = json.loads(message_value)
        # Basic validation: check for required fields
        required_fields = ['review_id', 'user_id', 'product_id', 'rating', 'content', 'review_date']
        if not all(field in review_data for field in required_fields):
            print(f"Skipping invalid message: missing required fields. Data: {review_data}")
            log_to_dlq(message_value, "missing_fields")
            return

        # Add ingestion timestamp
        review_data['ingestion_timestamp'] = datetime.utcnow().isoformat()

        # Determine S3 path (e.g., year/month/day/hour/file.json)
        current_time = datetime.utcnow()
        s3_key = f"{S3_PREFIX}year={current_time.year}/month={current_time.month:02d}/day={current_time.day:02d}/hour={current_time.hour:02d}/{uuid.uuid4()}.json"

        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(review_data).encode('utf-8')
        )
        print(f"Successfully processed and uploaded review_id {review_data.get('review_id')} to S3: {s3_key}")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e} - Message: {message_value}")
        log_to_dlq(message_value, "json_decode_error", str(e))
    except Exception as e:
        print(f"An unexpected error occurred: {e} - Message: {message_value}")
        log_to_dlq(message_value, "unexpected_error", str(e))

def consume_reviews():
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'review_integrity_guardian_group',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(conf)

    try:
        consumer.subscribe([KAFKA_TOPIC])

        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaException._PARTITION_EOF:
                    # End of partition event - no more messages for this partition.
                    print(f"{msg.topic()} [{msg.partition()}] reached end at offset {msg.offset()}")
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                process_message(msg.value().decode('utf-8'))

    except KeyboardInterrupt:
        print("Aborted by user.")
    finally:
        consumer.close()

if __name__ == "__main__":
    consume_reviews()
