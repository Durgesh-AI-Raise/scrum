# Pseudocode for Kafka Consumer
from kafka import KafkaConsumer
import json
import psycopg2 # or an ORM like SQLAlchemy

def process_review_event(event_data):
    # Validate event_data
    # Transform data if necessary
    # Insert into PostgreSQL reviews table
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reviews (review_id, reviewer_id, ip_address, device_fingerprint,
                                 review_text, rating, product_asin, timestamp, purchase_history)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event_data['review_id'],
            event_data['reviewer_id'],
            event_data['ip_address'],
            event_data['device_fingerprint'],
            event_data['review_text'],
            event_data['rating'],
            event_data['product_asin'],
            event_data['timestamp'],
            json.dumps(event_data['purchase_history']) # Store as JSONB
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error processing review: {e}")
        # Implement robust error handling, e.g., send to a dead-letter queue

consumer = KafkaConsumer(
    'review_events',
    bootstrap_servers=['kafka-broker:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='review-ingestion-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

for message in consumer:
    print(f"Received review event: {message.value}")
    process_review_event(message.value)
