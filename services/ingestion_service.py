import time
import json
from datetime import datetime
import uuid

def generate_mock_review():
    """Generates a synthetic Amazon review for testing purposes."""
    review_id = str(uuid.uuid4())
    product_id = f"PROD-{uuid.uuid4().hex[:8].upper()}"
    user_id = f"USER-{uuid.uuid4().hex[:8].upper()}"
    review_text = f"This is a mock review text for product {product_id}. It's {['great', 'terrible', 'okay', 'spammy', 'suspicious'][len(review_id) % 5]}! Keywords like damn, hell, and BUY NOW are sometimes here."
    rating = (len(review_id) % 5) + 1
    timestamp = datetime.now().isoformat()
    return {
        "review_id": review_id,
        "product_id": product_id,
        "user_id": user_id,
        "review_text": review_text,
        "rating": rating,
        "timestamp": timestamp,
        "source": "mock_amazon",
        "ingestion_timestamp": datetime.now().isoformat()
    }

def ingest_reviews_to_queue_and_db(mock_queue_writer, mock_db_writer, num_reviews=1):
    """
    Simulates ingesting reviews and sending them to a mock queue and database.
    In a real system, mock_queue_writer and mock_db_writer would be actual
    client instances for Kafka/SQS and DynamoDB/MongoDB.
    """
    for _ in range(num_reviews):
        review = generate_mock_review()
        print(f"Ingested review: {json.dumps(review)}")
        mock_queue_writer.send(review)
        mock_db_writer.save(review)
    print(f"Finished ingesting {num_reviews} mock reviews.")

if __name__ == "__main__":
    # Mock implementations for demonstration
    class MockQueueWriter:
        def send(self, data):
            print(f"  [MockQueue] Sent: {data['review_id']}")

    class MockDBWriter:
        def __init__(self):
            self.reviews = []
        def save(self, data):
            self.reviews.append(data)
            print(f"  [MockDB] Saved: {data['review_id']}")

    mock_queue = MockQueueWriter()
    mock_db = MockDBWriter()

    print("Starting continuous mock review ingestion (Ctrl+C to stop)...")
    while True:
        ingest_reviews_to_queue_and_db(mock_queue, mock_db, num_reviews=1)
        time.sleep(2) # Simulate polling every 2 seconds
