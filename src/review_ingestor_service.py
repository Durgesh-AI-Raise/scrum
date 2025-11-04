import json
from datetime import datetime
from kafka import KafkaProducer
import time
import random

# --- Configuration ---
KAFKA_BROKER = 'localhost:9092' # Replace with actual Kafka broker address
RAW_REVIEWS_TOPIC = 'raw_reviews'
# AMAZON_REVIEW_API_ENDPOINT = 'https://api.amazon.com/reviews' # Placeholder
# AMAZON_API_KEY = 'YOUR_AMAZON_API_KEY' # Placeholder

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def fetch_amazon_reviews():
    """
    Simulates fetching new reviews from an Amazon-like API.
    In a real scenario, this would involve HTTP requests, authentication,
    and handling API pagination/rate limits.
    """
    print("Simulating fetching reviews from Amazon...")
    # Placeholder for actual API call
    # response = requests.get(AMAZON_REVIEW_API_ENDPOINT, headers={'Authorization': f'Bearer {AMAZON_API_KEY}'})
    # response.raise_for_status()
    # raw_reviews_data = response.json()

    # Simulate some raw review data
    sample_reviews = [
        {
            "id": f"R{random.randint(100000, 999999)}",
            "product_id": f"P{random.randint(1000, 9999)}",
            "user_id": f"U{random.randint(100, 999)}",
            "text": "This product is absolutely fantastic! Highly recommend it to everyone. Great quality and value.",
            "rating": 5,
            "timestamp": datetime.now().isoformat(),
            "purchase_verified": True,
            "user_name": "HappyCustomer",
            "ip_address": f"192.168.1.{random.randint(1, 254)}",
            "product_title": "Amazing Widget",
            "category": "Electronics",
            "brand": "TechCo"
        },
        {
            "id": f"R{random.randint(100000, 999999)}",
            "product_id": f"P{random.randint(1000, 9999)}",
            "user_id": f"U{random.randint(100, 999)}",
            "text": "It's okay, nothing special. Does the job but I've seen better.",
            "rating": 3,
            "timestamp": datetime.now().isoformat(),
            "purchase_verified": True,
            "user_name": "NeutralReviewer",
            "ip_address": f"192.168.1.{random.randint(1, 254)}",
            "product_title": "Generic Gadget",
            "category": "Home Goods",
            "brand": "EverydayCo"
        },
        {
            "id": f"R{random.randint(100000, 999999)}",
            "product_id": f"P{random.randint(1000, 9999)}",
            "user_id": f"U{random.randint(100, 999)}",
            "text": "Total waste of money! Broke after a week. Do not buy this garbage. Seriously, worst purchase ever.",
            "rating": 1,
            "timestamp": datetime.now().isoformat(),
            "purchase_verified": False,
            "user_name": "AngryUser",
            "ip_address": f"192.168.1.{random.randint(1, 254)}",
            "product_title": "Faulty Device",
            "category": "Electronics",
            "brand": "ProblematicCorp"
        }
    ]
    return sample_reviews

def parse_and_publish_review(raw_review):
    """
    Parses raw review data into a standardized ReviewData format
    and publishes it to Kafka.
    """
    try:
        review_data = {
            "reviewId": raw_review["id"],
            "productId": raw_review["product_id"],
            "reviewerId": raw_review["user_id"],
            "reviewText": raw_review["text"],
            "overallRating": raw_review["rating"],
            "reviewTime": raw_review["timestamp"],
            "verifiedPurchase": raw_review["purchase_verified"],
            "reviewerName": raw_review.get("user_name", "Anonymous"),
            "reviewerIP": raw_review.get("ip_address", "N/A"),
            "productMetadata": {
                "productTitle": raw_review.get("product_title", "Unknown Product"),
                "categoryId": raw_review.get("category", "Unknown Category"),
                "brand": raw_review.get("brand", "Unknown Brand")
            },
            "ingestionTimestamp": datetime.now().isoformat(),
            "status": "pending", # Initial status
            "flags": []
        }
        producer.send(RAW_REVIEWS_TOPIC, review_data)
        print(f"Published review {review_data['reviewId']} to Kafka.")
    except KeyError as e:
        print(f"Error parsing raw review: Missing key {e}. Raw data: {raw_review}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}. Raw data: {raw_review}")

def run_ingestor():
    while True:
        reviews = fetch_amazon_reviews()
        for review in reviews:
            parse_and_publish_review(review)
        time.sleep(5) # Poll every 5 seconds (adjust as needed)

if __name__ == "__main__":
    print(f"Starting Review Ingestor Service. Publishing to {RAW_REVIEWS_TOPIC} on {KAFKA_BROKER}")
    run_ingestor()