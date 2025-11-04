# data_ingestion/kafka_producer.py
from confluent_kafka import Producer
import json
import time
import uuid
import random
from datetime import datetime, timedelta
import jsonschema
import os

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = 'review_data'

# Load review schema
SCHEMA_PATH = 'schemas/review_schema.json'
REVIEW_SCHEMA = None
try:
    # Adjust path for running from root or data_ingestion dir
    schema_file_path = SCHEMA_PATH
    if not os.path.exists(schema_file_path):
        schema_file_path = os.path.join(os.path.dirname(__file__), '..', SCHEMA_PATH)
    
    with open(schema_file_path, 'r') as f:
        REVIEW_SCHEMA = json.load(f)
except FileNotFoundError:
    print(f"Error: Schema file not found at {SCHEMA_PATH}")
except json.JSONDecodeError:
    print(f"Error: Invalid JSON in schema file at {SCHEMA_PATH}")

def generate_review_data():
    review_id = str(uuid.uuid4())
    product_id = str(uuid.uuid4())
    reviewer_id = str(uuid.uuid4())
    rating = random.randint(1, 5)
    title = f"Great product {random.choice(['!', '!!', '.'])}"
    comment = f"I really enjoyed this product. It's {random.choice(['amazing', 'good', 'decent'])} and I would {random.choice(['recommend', 'not recommend'])} it to others."
    review_date = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat() + 'Z'
    sentiment_score = round(random.uniform(-0.5, 0.9), 2)
    is_verified_purchase = random.choice([True, False])
    helpful_votes = random.randint(0, 100)

    # Introduce occasional invalid data for testing error handling
    if random.random() < 0.05: # 5% chance of invalid data
        invalid_field = random.choice(['rating', 'review_date', 'product_id'])
        if invalid_field == 'rating':
            rating = 99 # Invalid rating
        elif invalid_field == 'review_date':
            review_date = "not-a-date" # Invalid date format
        elif invalid_field == 'product_id':
            product_id = 12345 # Invalid type

    return {
        "review_id": review_id,
        "product_id": product_id,
        "reviewer_id": reviewer_id,
        "rating": rating,
        "title": title,
        "comment": comment,
        "review_date": review_date,
        "sentiment_score": sentiment_score,
        "is_verified_purchase": is_verified_purchase,
        "helpful_votes": helpful_votes
    }

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to topic {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def produce_reviews():
    if REVIEW_SCHEMA is None:
        print("Schema not loaded, exiting producer.")
        return

    producer_conf = {'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS}
    producer = Producer(producer_conf)

    try:
        while True:
            review = generate_review_data()
            try:
                jsonschema.validate(instance=review, schema=REVIEW_SCHEMA)
                producer.produce(
                    KAFKA_TOPIC,
                    key=review['review_id'].encode('utf-8'),
                    value=json.dumps(review).encode('utf-8'),
                    callback=delivery_report
                )
                producer.poll(0)
                print(f"Produced valid review: {review['review_id']}")
            except jsonschema.exceptions.ValidationError as e:
                print(f"Skipping invalid review due to schema validation error: {e.message} in {review}")
            except Exception as e:
                print(f"An unexpected error occurred during message production: {e}")

            time.sleep(random.uniform(1, 5))
    except KeyboardInterrupt:
        print("Producer stopped by user.")
    finally:
        producer.flush()
        print("Producer flushed. Exiting.")

if __name__ == '__main__':
    print(f"Starting Kafka producer for topic: {KAFKA_TOPIC}")
    produce_reviews()
