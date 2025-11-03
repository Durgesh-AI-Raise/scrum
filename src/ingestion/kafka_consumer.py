import json
import os
import time
from kafka import KafkaConsumer

# Configuration (replace with actual values or environment variables)
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'product_reviews')
# In a real-world scenario, this would be a cloud storage bucket (e.g., s3://my-bucket/raw-reviews/)
STORAGE_PATH = os.getenv('STORAGE_PATH', './raw_reviews/') 

def ingest_review_data():
    """
    Consumes review data from Kafka and stores it in raw storage.
    """
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset='earliest',  # Start reading at the earliest message available
        enable_auto_commit=True,       # Commit offsets automatically
        group_id='review-ingestion-group', # Consumer group ID
        value_deserializer=lambda x: json.loads(x.decode('utf-8')) # Deserialize JSON messages
    )

    print(f"Starting Kafka consumer for topic: {KAFKA_TOPIC}")

    if not os.path.exists(STORAGE_PATH):
        os.makedirs(STORAGE_PATH)
        print(f"Created storage directory: {STORAGE_PATH}")

    try:
        for message in consumer:
            review_data = message.value
            review_id = review_data.get('review_id', 'unknown_review')
            product_id = review_data.get('product_id', 'unknown_product')
            timestamp_ms = review_data.get('timestamp', int(time.time() * 1000)) # Use current time if not provided

            print(f"Received review: {review_id} for product {product_id}")
            
            # Construct a filename. In a real system, pathing would involve partitioning (e.g., /year/month/day/hour)
            file_name = f"{STORAGE_PATH}review_{timestamp_ms}_{review_id}.json"
            
            # Store raw data - saving to a local file for this sprint
            # This would be replaced by a cloud storage client (e.g., boto3 for S3)
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(review_data, f, ensure_ascii=False, indent=2)
            print(f"Stored review to {file_name}")

    except Exception as e:
        print(f"Error during ingestion: {e}")
    finally:
        consumer.close()
        print("Kafka consumer closed.")

if __name__ == "__main__":
    ingest_review_data()
