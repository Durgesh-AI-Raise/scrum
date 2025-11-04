from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime

def generate_mock_review():
    review_id = f"R{random.randint(100000, 999999)}"
    product_id = f"P{random.randint(1000, 9999)}"
    reviewer_id = f"U{random.randint(10000, 99999)}"
    rating = random.randint(1, 5)
    review_text_options = [
        "This product is amazing! Highly recommend.",
        "Absolutely terrible, a complete waste of money.",
        "It's okay, not great but not bad either.",
        "The best purchase I've made this year. So happy!",
        "Customer service was unhelpful. Product broke quickly.",
        "Such a scam! Do not buy this. #scam #fraud",
        "Wow, this is truly fantastic quality. Love it!",
        "I regret buying this. Very poor design.",
        "Good value for money. Does exactly what it says.",
        "This is a piece of trash, total garbage.",
        "What a fantastic device. It works perfectly.",
        "Avoid this at all costs. Horrible experience."
    ]
    review_text = random.choice(review_text_options)
    timestamp = datetime.now().isoformat()
    return {
        "review_id": review_id,
        "product_id": product_id,
        "reviewer_id": reviewer_id,
        "rating": rating,
        "review_text": review_text,
        "timestamp": timestamp
    }

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'], # Or your Kafka cluster
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("Starting review data producer...")
try:
    while True:
        review = generate_mock_review()
        producer.send('amazon_reviews', value=review)
        print(f"Sent review: {review['review_id']}")
        time.sleep(random.uniform(0.5, 2.0))
except KeyboardInterrupt:
    print("Stopping producer.")
finally:
    producer.close()
