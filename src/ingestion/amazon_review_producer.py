from kafka import KafkaProducer
import json
import time
from datetime import datetime
import random

# Initialize Kafka Producer
# Replace 'localhost:9092' with your Kafka broker address
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def generate_mock_review(review_id_counter, user_id_counter):
    """Generates a mock Amazon review for demonstration purposes."""
    product_id = f"PROD{random.randint(1000, 9999)}"
    user_id = f"USER{random.randint(100, 100 + user_id_counter % 50)}" # Simulate some users reviewing multiple products
    seller_id = f"SELL{random.randint(1, 10)}"
    rating = random.randint(1, 5)
    review_date = datetime.utcnow().isoformat() + 'Z'
    
    review_titles = ["Great Product!", "Highly Recommend", "Disappointed", "Works as expected", "Not worth it"]
    review_texts = [
        "This product is amazing, definitely buying again!",
        "I've been using it for a week now and it's fantastic. Five stars!",
        "Terrible quality, broke after first use. Do not buy!",
        "It's okay, does what it says on the tin. Nothing special.",
        "Waste of money, completely useless for my needs. Regret purchasing."
    ]
    product_categories = ["Electronics", "Home & Kitchen", "Books", "Clothing", "Sports"]

    return {
        "review_id": f"R{review_id_counter}",
        "product_id": product_id,
        "user_id": user_id,
        "rating": rating,
        "review_title": random.choice(review_titles),
        "review_text": random.choice(review_texts),
        "review_date": review_date,
        "helpful_votes": random.randint(0, 50),
        "verified_purchase": random.choice([True, False]),
        "product_category": random.choice(product_categories),
        "seller_id": seller_id
    }

if __name__ == "__main__":
    print("Starting Amazon Review Producer...")
    review_id_counter = 1
    user_id_counter = 0
    while True:
        review = generate_mock_review(review_id_counter, user_id_counter)
        try:
            producer.send('amazon_reviews_raw', review)
            print(f"Produced review: {review['review_id']} by {review['user_id']}")
            review_id_counter += 1
            user_id_counter += 1
        except Exception as e:
            print(f"Error sending message to Kafka: {e}")
        
        time.sleep(random.uniform(1, 5)) # Simulate reviews coming in at irregular intervals