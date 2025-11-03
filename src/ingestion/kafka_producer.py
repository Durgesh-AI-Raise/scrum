from kafka import KafkaProducer
import json
import time
import os

def send_review_to_kafka(review_data: dict):
    kafka_brokers = os.environ.get('KAFKA_BROKERS', 'localhost:9092').split(',')
    producer = KafkaProducer(bootstrap_servers=kafka_brokers,
                             value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    topic = 'raw_reviews'
    producer.send(topic, review_data)
    producer.flush()
    print(f"Sent review to Kafka: {review_data.get('reviewId', 'N/A')}")

# Example usage:
# if __name__ == "__main__":
#     new_review = {"reviewId": "R12345", "productId": "B001", "reviewerId": "U9876", "rating": 5, "reviewText": "Great product!"}
#     send_review_to_kafka(new_review)
