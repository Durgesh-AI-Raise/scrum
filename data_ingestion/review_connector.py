from kafka import KafkaProducer
import json
import time
import random

def get_amazon_reviews():
    """
    Placeholder for fetching reviews from Amazon source.
    In a real scenario, this would involve API calls,
    web scraping, or reading from a data dump.
    """
    reviews = []
    for i in range(1, 11): # Simulate 10 reviews
        reviews.append({
            "review_id": f"R{i}",
            "product_id": f"P{random.randint(100, 200)}",
            "reviewer_id": f"U{random.randint(1, 5)}",
            "rating": random.randint(1, 5),
            "text": f"This is a review for product P{random.randint(100, 200)}. It was {random.choice(['great', 'good', 'okay', 'bad', 'terrible'])}.",
            "timestamp": int(time.time() - random.randint(0, 30*24*60*60)) # Last 30 days
        })
    return reviews

def produce_reviews_to_kafka(topic, reviews_data):
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'], # Replace with actual Kafka broker
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    for review in reviews_data:
        producer.send(topic, review)
        print(f"Sent review: {review['review_id']}")
    producer.flush()
    producer.close()

if __name__ == "__main__":
    review_topic = "amazon_raw_reviews"
    reviews = get_amazon_reviews()
    produce_reviews_to_kafka(review_topic, reviews)