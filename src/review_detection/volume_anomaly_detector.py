
import os
import logging
from datetime import datetime, timedelta
import time
import json

import redis
import boto3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'reviews') # For flagging reviews
dynamodb = boto3.resource('dynamodb')
reviews_table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Anomaly Detection Configuration
SHORT_WINDOW_MINUTES = int(os.getenv('SHORT_WINDOW_MINUTES', 5))
LONG_WINDOW_HOURS = int(os.getenv('LONG_WINDOW_HOURS', 24))
SPIKE_THRESHOLD_FACTOR = float(os.getenv('SPIKE_THRESHOLD_FACTOR', 3.0)) # e.g., 3x the long-term average
DETECTION_INTERVAL_SECONDS = int(os.getenv('DETECTION_INTERVAL_SECONDS', 300)) # Run every 5 minutes

class VolumeAnomalyDetector:
    def __init__(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        logging.info(f"Initialized Redis client for Anomaly Detector: {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

    def _get_review_counts_in_window(self, product_id, start_time, end_time):
        product_ts_key = f"product_review_timestamps:{product_id}"
        # Use ZCOUNT to get the number of elements within the score range
        # Scores are milliseconds since epoch
        min_score = int(start_time.timestamp() * 1000)
        max_score = int(end_time.timestamp() * 1000)
        count = self.redis_client.zcount(product_ts_key, min_score, max_score)
        return count

    def detect_anomalies(self):
        logging.info("Starting anomaly detection scan...")
        current_time = datetime.utcnow()

        # Get all product_id keys from Redis. Assuming a pattern for product timestamp keys.
        # This might be inefficient for a very large number of products, but suitable for MVP.
        # A more robust solution might involve a separate Redis set of active product_ids.
        product_keys = self.redis_client.keys("product_review_timestamps:*")
        product_ids = [key.decode('utf-8').split(':')[1] for key in product_keys]

        for product_id in product_ids:
            # Define time windows
            short_window_start = current_time - timedelta(minutes=SHORT_WINDOW_MINUTES)
            long_window_start = current_time - timedelta(hours=LONG_WINDOW_HOURS)

            # Get review counts for each window
            short_window_count = self._get_review_counts_in_window(product_id, short_window_start, current_time)
            long_window_count = self._get_review_counts_in_window(product_id, long_window_start, current_time)

            # Calculate average review rate per minute for the long window
            long_window_duration_minutes = LONG_WINDOW_HOURS * 60
            long_term_average_per_minute = long_window_count / long_window_duration_minutes if long_window_duration_minutes > 0 else 0

            # Calculate expected count for the short window based on long-term average
            expected_short_window_count = long_term_average_per_minute * SHORT_WINDOW_MINUTES

            logging.debug(f"Product {product_id}: Short window count = {short_window_count}, Long window count = {long_window_count}")
            logging.debug(f"Expected short window count = {expected_short_window_count}, Long-term average/min = {long_term_average_per_minute}")

            # Anomaly detection logic
            if expected_short_window_count > 0 and \
               short_window_count > (expected_short_window_count * SPIKE_THRESHOLD_FACTOR):
                logging.warning(f"!!! ANOMALY DETECTED for product {product_id} !!!")
                logging.warning(f"Short window count ({short_window_count}) significantly higher than expected ({expected_short_window_count:.2f} * {SPIKE_THRESHOLD_FACTOR})")
                
                # --- Flagging mechanism (Integrated from Task 2.3) ---                
                # Retrieve some recent reviews for the product and flag them.
                # This is an approximation for the MVP.
                response = reviews_table.query(
                    IndexName='product_id-index',
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('product_id').eq(product_id),
                    Limit=short_window_count # Try to fetch up to the spike count
                )
                for review_to_flag in response.get('Items', []):
                     if not review_to_flag.get('is_flagged', False): # Only flag if not already flagged
                         reviews_table.update_item(
                             Key={'review_id': review_to_flag['review_id']},
                             UpdateExpression="SET is_flagged = :flag, flag_reason = :reason, flag_details = :details",
                             ExpressionAttributeValues={
                                 ':flag': True,
                                 ':reason': 'Volume Spike',
                                 ':details': {'short_window_count': short_window_count, 'expected_count': expected_short_window_count, 'detection_time': current_time.isoformat()}
                             }
                         )
                         logging.info(f"Flagged review {review_to_flag['review_id']} for product {product_id} due to volume spike.")


            elif expected_short_window_count > 0:
                logging.info(f"Product {product_id}: No anomaly. Short window count ({short_window_count}) vs expected ({expected_short_window_count:.2f} * {SPIKE_THRESHOLD_FACTOR})")
            else:
                logging.info(f"Product {product_id}: Not enough long-term data for meaningful anomaly detection or expected count is zero.")

    def run_periodically(self):
        logging.info(f"Starting Volume Anomaly Detector to run every {DETECTION_INTERVAL_SECONDS} seconds.")
        while True:
            self.detect_anomalies()
            time.sleep(DETECTION_INTERVAL_SECONDS)

if __name__ == "__main__":
    detector = VolumeAnomalyDetector()
    detector.run_periodically()
