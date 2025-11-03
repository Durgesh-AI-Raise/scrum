from kafka import KafkaProducer
import json
import time
import random

# Configuration
KAFKA_BROKER = 'localhost:9092' # Replace with actual Kafka broker address
KAFKA_TOPIC = 'amazon_reviews_raw'

def get_new_amazon_reviews():
    """
    Simulates fetching a new review from an Amazon.com review data source.
    In a real-world scenario, this would involve API calls, parsing feeds,
    or reading from a dedicated stream.
    """
    review_id = f"R{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    product_id = f"B0{random.randint(1000000, 9999999)}"
    user_id = f"U{random.randint(10000, 99999)}"
    stars = random.randint(1, 5)
    headline_options = [
        "Great product!", "Not bad.", "Disappointing", "Highly recommended",
        "Just okay", "Love it!", "Wish it was better"
    ]
    body_options = [
        "I really enjoyed using this product. It works as advertised.",
        "It's decent for the price, but I've seen better.",
        "The quality is very poor, broke after a week.",
        "Excellent purchase, definitely worth the money.",
        "Could use some improvements, but serves its purpose.",
        "This is an amazing item, very happy with my decision.",
        "I expected more given the description."
    ]
    countries = ["US", "GB", "DE", "JP", "FR"]

    return {
        "review_id": review_id,
        "product_id": product_id,
        "user_id": user_id,
        "stars": stars,
        "headline": random.choice(headline_options),
        "body": random.choice(body_options),
        "timestamp": int(time.time() * 1000), # Unix timestamp in milliseconds
        "country": random.choice(countries),
        "source": "amazon.com"
    }

def produce_reviews_to_kafka():
    """
    Connects to Kafka and continuously produces simulated review data.
    """
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
        retries=3
    )
    print(f"Starting Kafka producer for topic: {KAFKA_TOPIC} on {KAFKA_BROKER}")
    try:
        while True:
            review_data = get_new_amazon_reviews()
            if review_data:
                future = producer.send(KAFKA_TOPIC, review_data)
                record_metadata = future.get(timeout=60) # Block until success or timeout
                print(f"Produced review: {review_data['review_id']} to partition {record_metadata.partition} offset {record_metadata.offset}")
            time.sleep(random.uniform(1, 3)) # Simulate reviews coming in every 1-3 seconds
    except KeyboardInterrupt:
        print("Stopping producer due to user interruption.")
    except Exception as e:
        print(f"An error occurred in producer: {e}")
    finally:
        producer.close()
        print("Kafka producer closed.")

if __name__ == "__main__":
    produce_reviews_to_kafka()
