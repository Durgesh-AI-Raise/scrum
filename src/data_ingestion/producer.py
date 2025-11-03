import json
import time
import uuid
import random
from datetime import datetime, timedelta
from kafka import KafkaProducer

# Kafka configuration
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC_RAW = 'amazon_reviews_raw'

# Initialize Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def generate_review():
    """Generates a synthetic Amazon product review."""
    review_id = str(uuid.uuid4())
    product_id = f"B0{random.randint(1000, 9999)}{random.randint(100, 999)}"
    user_id = f"A{random.randint(1000000000, 9999999999)}"
    rating = random.randint(1, 5)
    title_options = ["Great product!", "Disappointing", "Worth the money", "Could be better", "Amazing!"]
    text_options = [
        "I really enjoyed using this product. It exceeded my expectations.",
        "Not what I expected. The quality is poor for the price.",
        "Works as described. Fast shipping.",
        "It's okay, but I've seen better options.",
        "Absolutely love it! Will buy again."
    ]
    product_categories = ["Electronics", "Home Goods", "Books", "Apparel", "Beauty"]

    # Simulate review date within the last year
    review_date = (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat()
    verified_purchase = random.choice([True, False])
    reviewer_account_age_days = random.randint(1, 2000) # Age between 1 day and ~5.5 years

    review = {
        "reviewId": review_id,
        "productId": product_id,
        "userId": user_id,
        "rating": rating,
        "title": random.choice(title_options),
        "text": random.choice(text_options),
        "reviewDate": review_date,
        "verifiedPurchase": verified_purchase,
        "productCategory": random.choice(product_categories),
        "reviewerAccountAgeDays": reviewer_account_age_days
    }
    return review

def produce_reviews(num_reviews=10, interval_seconds=1):
    """Produces a specified number of reviews to Kafka."""
    print(f"Starting to produce {num_reviews} reviews to topic {KAFKA_TOPIC_RAW}...")
    for i in range(num_reviews):
        review = generate_review()
        try:
            future = producer.send(KAFKA_TOPIC_RAW, review)
            record_metadata = future.get(timeout=10) # Block until send is complete
            print(f"Produced review {i+1}/{num_reviews}: {review['reviewId']}")
            # print(f"Topic: {record_metadata.topic}, Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")
        except Exception as e:
            print(f"Error producing message: {e}")
        time.sleep(interval_seconds)
    producer.flush() # Ensure all messages are sent
    print("Finished producing reviews.")

if __name__ == "__main__":
    produce_reviews(num_reviews=100, interval_seconds=0.5)
