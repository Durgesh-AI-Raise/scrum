import json
import psycopg2
import logging
from kafka import KafkaConsumer
from datetime import datetime

# Configuration
KAFKA_BROKERS = ['kafka-broker:9092']
RAW_REVIEWS_TOPIC = 'raw-reviews'
POSTGRES_DB = 'trust_safety_db'
POSTGRES_USER = 'user'
POSTGRES_PASSWORD = 'password'
POSTGRES_HOST = 'postgres-host'
POSTGRES_PORT = '5432'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        port=POSTGRES_PORT
    )

def store_review(review_data: dict, conn):
    """
    Stores a processed review into the PostgreSQL database.
    Handles potential duplicates by doing nothing on conflict of review_id.
    """
    try:
        with conn.cursor() as cur:
            insert_query = """
            INSERT INTO reviews (review_id, product_id, reviewer_id, title, content, rating, review_date, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (review_id) DO NOTHING;
            """
            cur.execute(insert_query, (
                review_data.get('reviewId'),
                review_data.get('productId'),
                review_data.get('reviewerId'),
                review_data.get('title'),
                review_data.get('content'),
                review_data.get('rating'),
                datetime.fromisoformat(review_data['reviewDate']) if 'reviewDate' in review_data else None,
                review_data.get('source')
            ))
            conn.commit()
            logger.info(f"Stored review {review_data.get('reviewId')}")
    except Exception as e:
        logger.error(f"Error storing review {review_data.get('reviewId')}: {e}")
        conn.rollback() # Rollback in case of an error

def consume_and_store_reviews():
    """Main function to consume reviews from Kafka and store them."""
    consumer = KafkaConsumer(
        RAW_REVIEWS_TOPIC,
        bootstrap_servers=KAFKA_BROKERS,
        auto_offset_reset='earliest', # Start reading from the beginning if no offset is committed
        enable_auto_commit=True,      # Automatically commit offsets
        group_id='review-storage-group', # Consumer group ID
        value_deserializer=lambda x: json.loads(x.decode('utf-8')) # Deserialize JSON messages
    )
    
    conn = None
    try:
        conn = create_db_connection()
        logger.info(f"Starting to consume from topic {RAW_REVIEWS_TOPIC}...")
        for message in consumer:
            review_data = message.value
            logger.debug(f"Received review: {review_data.get('reviewId')}")
            store_review(review_data, conn)
    except KeyboardInterrupt:
        logger.info("Stopping review storage service.")
    except Exception as e:
        logger.critical(f"Unhandled error in consumer: {e}")
    finally:
        if conn:
            conn.close()
        consumer.close()
        logger.info("Review storage service stopped.")

if __name__ == "__main__":
    consume_and_store_reviews()
