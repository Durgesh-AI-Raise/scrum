
import json
import time
from datetime import datetime, timedelta
from kafka import KafkaProducer
import uuid
import random

# Kafka Producer configuration
KAFKA_BROKER = 'localhost:9092' # Replace with actual broker address
KAFKA_TOPIC = 'amazon-reviews-raw'

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def generate_mock_review():
    review_id = str(uuid.uuid4())
    product_id = f"PROD-{random.randint(1000, 9999)}"
    reviewer_id = f"REV-{random.randint(100, 999)}" # Simplified, could be more persistent across runs

    review_date = (datetime.utcnow() - timedelta(days=random.randint(0, 365))).isoformat(timespec='seconds') + 'Z'
    ingestion_timestamp = datetime.utcnow().isoformat(timespec='seconds') + 'Z'

    review = {
        "review_id": review_id,
        "product_id": product_id,
        "reviewer_id": reviewer_id,
        "rating": random.randint(1, 5),
        "title": f"Great Product {product_id}!",
        "content": f"This is a review for product {product_id}. I found it to be {random.choice(['excellent', 'good', 'average', 'poor'])}. Definitely recommend it.",
        "review_date": review_date,
        "source_url": f"http://amazon.com/reviews/{review_id}",
        "ingestion_timestamp": ingestion_timestamp,
        "flagged": False,
        "flagging_reason": None
    }

    # Simplified reviewer data for the mock
    reviewer = {
        "reviewer_id": reviewer_id,
        "username": f"User_{reviewer_id}",
        "account_age_days": random.randint(100, 2000),
        "purchase_history_product_ids": [f"PROD-{random.randint(1000, 9999)}" for _ in range(random.randint(1, 5))],
        "ip_address_last_known": f"192.168.1.{random.randint(1, 254)}",
        "device_info_last_known": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "total_reviews_count": random.randint(1, 50),
        "last_review_timestamp": ingestion_timestamp,
        "flagged": False,
        "flagging_reason": None
    }
    return {"review": review, "reviewer": reviewer}

def start_mock_producer():
    print(f"Starting mock Amazon review producer for topic: {KAFKA_TOPIC}")
    try:
        while True:
            mock_data = generate_mock_review()
            producer.send(KAFKA_TOPIC, mock_data)
            print(f"Produced: Review ID {mock_data['review']['review_id']} by Reviewer ID {mock_data['reviewer']['reviewer_id']}")
            time.sleep(random.uniform(0.5, 2.0)) # Send a review every 0.5 to 2 seconds
    except Exception as e:
        print(f"Error in mock producer: {e}")
    finally:
        producer.close()

if __name__ == "__main__":
    start_mock_producer()
