# producer.py
from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime, timedelta

def generate_mock_review(review_id_prefix="R", product_id_prefix="P", reviewer_id_prefix="U"):
    """Generates a mock Amazon review."""
    review_id = f"{review_id_prefix}{random.randint(10000, 99999)}"
    product_id = f"{product_id_prefix}{random.randint(1, 10)}"
    reviewer_id = f"{reviewer_id_prefix}{random.randint(100, 999)}"
    rating = random.randint(1, 5)
    review_date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
    title_options = ["Great product!", "Good value.", "Disappointed", "Works as expected", "Excellent!"]
    text_options = [
        "I really enjoyed using this product. It's exactly what I needed.",
        "The quality is decent for the price. Would recommend to others.",
        "Not happy with my purchase. It broke after a week.",
        "Simple and effective. No complaints.",
        "Fantastic item, exceeded my expectations in every way."
    ]

    return {
        "review_id": review_id,
        "product_id": product_id,
        "reviewer_id": reviewer_id,
        "overall_rating": rating,
        "review_text": random.choice(text_options),
        "review_title": random.choice(title_options),
        "review_date": review_date,
        "verified_purchase": random.choice([True, False]),
        "helpful_votes": random.randint(0, 50)
    }

def produce_reviews_to_kafka(topic, broker_list, num_reviews_per_batch=5):
    """
    Fetches mock reviews and produces them to a Kafka topic.
    In a real scenario, this would connect to an external API or file source.
    """
    producer = KafkaProducer(
        bootstrap_servers=broker_list,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print(f"Starting Kafka producer for topic: {topic}")
    try:
        while True:
            reviews_batch = [generate_mock_review() for _ in range(num_reviews_per_batch)]
            for review in reviews_batch:
                producer.send(topic, review)
                print(f"Produced review: {review['review_id']} (Product: {review['product_id']})")
            producer.flush() # Ensure all messages are sent
            time.sleep(10) # Wait 10 seconds before generating next batch
    except KeyboardInterrupt:
        print("Producer stopped by user.")
    except Exception as e:
        print(f"An error occurred in producer: {e}")
    finally:
        producer.close()

if __name__ == "__main__":
    KAFKA_BROKER = ['localhost:9092'] # Adjust to your Kafka broker address
    KAFKA_TOPIC = 'raw_amazon_reviews'
    produce_reviews_to_kafka(KAFKA_TOPIC, KAFKA_BROKER)
