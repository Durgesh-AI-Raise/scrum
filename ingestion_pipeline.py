
# ingestion_pipeline.py

from kafka import KafkaProducer, KafkaConsumer
import json
import time
import logging
import psycopg2
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
RAW_REVIEWS_TOPIC = 'amazon_reviews_raw'

# --- Kafka Producer ---
def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def send_mock_review(producer):
    mock_review = {
        "reviewId": f"R{int(time.time() * 1000)}",
        "productId": "B07XXXXXXX",
        "sellerId": "S12345",
        "reviewerId": "A1B2C3D4E5",
        "rating": 5,
        "title": "Excellent Product!",
        "text": "This product exceeded my expectations and arrived quickly. Highly recommend!",
        "reviewDate": int(time.time()), # Unix timestamp
        "isVerifiedPurchase": True,
        "helpfulVotes": 10,
        "reviewerName": "John Doe",
        "reviewerProfileUrl": "http://amazon.com/profiles/A1B2C3D4E5"
    }
    producer.send(RAW_REVIEWS_TOPIC, mock_review)
    logger.info(f"Sent mock review: {mock_review['reviewId']}")
    producer.flush()

# --- Kafka Consumer (Ingestion Service) ---
DB_CONFIG = {
    'dbname': 'guardian_reviewer',
    'user': 'your_user',
    'password': 'your_password',
    'host': 'localhost'
}

def create_consumer():
    return KafkaConsumer(
        RAW_REVIEWS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='review-ingestion-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

def store_product_metadata(cur, product_data):
    try:
        cur.execute(
            """
            INSERT INTO products (product_id, product_name, product_url)
            VALUES (%s, %s, %s)
            ON CONFLICT (product_id) DO UPDATE SET
                product_name = EXCLUDED.product_name,
                product_url = EXCLUDED.product_url;
            """,
            (
                product_data['productId'],
                "Unknown Product Name", # Placeholder, would come from enrichment
                f"http://amazon.com/dp/{product_data['productId']}" # Placeholder
            )
        )
        logger.debug(f"Stored/updated product {product_data['productId']} metadata.")
    except Exception as e:
        logger.error(f"Error storing product {product_data['productId']}: {e}")

def store_seller_metadata(cur, seller_data):
    if not seller_data.get('sellerId'):
        return
    try:
        cur.execute(
            """
            INSERT INTO sellers (seller_id, seller_name, seller_url)
            VALUES (%s, %s, %s)
            ON CONFLICT (seller_id) DO UPDATE SET
                seller_name = EXCLUDED.seller_name,
                seller_url = EXCLUDED.seller_url;
            """,
            (
                seller_data['sellerId'],
                "Unknown Seller Name", # Placeholder
                f"http://amazon.com/seller/{seller_data['sellerId']}" # Placeholder
            )
        )
        logger.debug(f"Stored/updated seller {seller_data['sellerId']} metadata.")
    except Exception as e:
        logger.error(f"Error storing seller {seller_data['sellerId']}: {e}")

def store_reviewer_profile(cur, reviewer_data):
    try:
        cur.execute(
            """
            INSERT INTO reviewers (reviewer_id, reviewer_name, reviewer_profile_url)
            VALUES (%s, %s, %s)
            ON CONFLICT (reviewer_id) DO UPDATE SET
                reviewer_name = EXCLUDED.reviewer_name,
                reviewer_profile_url = EXCLUDED.reviewer_profile_url;
            """,
            (
                reviewer_data['reviewerId'],
                reviewer_data.get('reviewerName'),
                reviewer_data.get('reviewerProfileUrl')
            )
        )
        logger.debug(f"Stored/updated reviewer {reviewer_data['reviewerId']} profile.")
    except Exception as e:
        logger.error(f"Error storing reviewer {reviewer_data['reviewerId']}: {e}")


def store_review_in_database(cur, review_data):
    try:
        cur.execute(
            """
            INSERT INTO reviews (
                review_id, product_id, seller_id, reviewer_id, rating,
                title, review_text, review_date, is_verified_purchase,
                helpful_votes, reviewer_name, reviewer_profile_url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, to_timestamp(%s) AT TIME ZONE 'UTC', %s, %s, %s, %s)
            ON CONFLICT (review_id) DO NOTHING;
            """,
            (
                review_data['reviewId'],
                review_data['productId'],
                review_data.get('sellerId'),
                review_data['reviewerId'],
                review_data['rating'],
                review_data.get('title'),
                review_data.get('text'),
                review_data['reviewDate'], # Unix timestamp
                review_data.get('isVerifiedPurchase'),
                review_data.get('helpfulVotes', 0),
                review_data.get('reviewerName'),
                review_data.get('reviewerProfileUrl')
            )
        )
        logger.info(f"Stored review {review_data['reviewId']} in DB.")
    except Exception as e:
        logger.error(f"Error storing review {review_data['reviewId']}: {e}")

def run_ingestion_consumer():
    consumer = create_consumer()
    logger.info("Starting Kafka ingestion consumer...")
    while True:
        try:
            for message in consumer:
                review_data = message.value
                review_id = review_data['reviewId']
                logger.info(f"Processing review from Kafka: {review_id}")

                conn = None
                try:
                    conn = psycopg2.connect(**DB_CONFIG)
                    cur = conn.cursor()

                    # Store related metadata first (UPSERT logic)
                    store_product_metadata(cur, review_data)
                    store_seller_metadata(cur, review_data)
                    store_reviewer_profile(cur, review_data)

                    # Then store the review itself
                    store_review_in_database(cur, review_data)

                    conn.commit()
                    cur.close()
                except Exception as db_e:
                    logger.error(f"Database operation failed for review {review_id}: {db_e}", exc_info=True)
                    if conn:
                        conn.rollback() # Rollback in case of error
                finally:
                    if conn:
                        conn.close()

                # Placeholder for metrics
                # metrics_client.inc('reviews_ingested_total', {'status': 'success'})

        except Exception as e:
            logger.critical(f"Kafka ingestion consumer crashed: {e}", exc_info=True)
            # metrics_client.inc('consumer_crashes_total')
            time.sleep(5) # Attempt to restart after a short delay

if __name__ == "__main__":
    # Example: Run a mock producer to send a few messages
    # producer = create_producer()
    # for _ in range(3):
    #     send_mock_review(producer)
    #     time.sleep(1)
    # producer.close()
    # print("\nStarting consumer... wait for messages.")
    run_ingestion_consumer()
