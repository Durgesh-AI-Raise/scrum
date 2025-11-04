
import json
import os
import logging
from datetime import datetime, timedelta
import time

from kafka import KafkaConsumer
import redis

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
PROCESSED_REVIEW_EVENTS_TOPIC = os.getenv('PROCESSED_REVIEW_EVENTS_TOPIC', 'processed_review_events')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Window configuration
WINDOW_SIZE_MINUTES = int(os.getenv('WINDOW_SIZE_MINUTES', 5))
WINDOW_SLIDE_SECONDS = int(os.getenv('WINDOW_SLIDE_SECONDS', 60)) # Update every 1 minute

class ReviewVolumeMonitor:
    def __init__(self):
        self.consumer = KafkaConsumer(
            PROCESSED_REVIEW_EVENTS_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='review-volume-monitor-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        logging.info(f"Initialized Kafka Consumer for topic: {PROCESSED_REVIEW_EVENTS_TOPIC}")
        logging.info(f"Initialized Redis client: {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

    def update_volume(self, product_id, review_timestamp):
        # Key to store review timestamps for a product
        product_ts_key = f"product_review_timestamps:{product_id}"

        # Add the current review timestamp to a sorted set, score it by its timestamp
        # Using milliseconds since epoch for score to ensure uniqueness and order
        score = int(review_timestamp.timestamp() * 1000) 
        self.redis_client.zadd(product_ts_key, {review_timestamp.isoformat(): score})

        # Trim old timestamps outside a reasonable window to prevent unbounded growth
        # Keep data for twice the WINDOW_SIZE_MINUTES to cover two full windows for calculation
        cutoff_time = datetime.utcnow() - timedelta(minutes=WINDOW_SIZE_MINUTES * 2)
        self.redis_client.zremrangebyscore(product_ts_key, 0, int(cutoff_time.timestamp() * 1000))
        
        logging.debug(f"Updated timestamps for product {product_id} in Redis.")


    def run(self):
        logging.info(f"Starting Review Volume Monitor, consuming from {PROCESSED_REVIEW_EVENTS_TOPIC}...")
        for message in self.consumer:
            logging.info(f"Received processed review event for review ID: {message.value.get('review_id')}")
            event_data = message.value
            product_id = event_data.get('product_id')
            review_date_str = event_data.get('review_date')

            if product_id and review_date_str:
                try:
                    review_timestamp = datetime.fromisoformat(review_date_str)
                    self.update_volume(product_id, review_timestamp)
                except ValueError:
                    logging.error(f"Invalid review_date format for review {event_data.get('review_id')}: {review_date_str}")
            else:
                logging.warning(f"Skipping event due to missing product_id or review_date: {event_data}")

if __name__ == "__main__":
    monitor = ReviewVolumeMonitor()
    monitor.run()
