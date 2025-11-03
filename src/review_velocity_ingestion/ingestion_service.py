import json
import time
from datetime import datetime, timedelta, timezone

from kafka import KafkaConsumer
import psycopg2
from psycopg2 import extras

from .config import (
    KAFKA_BROKERS, KAFKA_TOPIC, DB_CONNECTION_STRING,
    TIME_WINDOW_HOURS, POSITIVE_RATING_THRESHOLD,
    NEGATIVE_RATING_THRESHOLD, FLUSH_BUFFER_SIZE, FLUSH_INTERVAL_SECONDS
)

class ReviewVelocityIngestionService:
    def __init__(self):
        self.consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BROKERS,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='review-velocity-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self.conn = self._get_db_connection()
        self.aggregation_buffer = {} # Key: (product_id, time_window_start_timestamp), Value: {count, positive_count, negative_count, total_rating_sum}
        self.last_flush_time = time.time()

    def _get_db_connection(self):
        return psycopg2.connect(DB_CONNECTION_STRING)

    def _get_time_window(self, timestamp):
        dt_object = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        # Round down to the nearest hour (or TIME_WINDOW_HOURS)
        start_hour = dt_object.hour // TIME_WINDOW_HOURS * TIME_WINDOW_HOURS
        time_window_start = dt_object.replace(
            hour=start_hour, minute=0, second=0, microsecond=0
        )
        time_window_end = time_window_start + timedelta(hours=TIME_WINDOW_HOURS)
        return time_window_start, time_window_end

    def _process_message(self, message):
        try:
            review_data = message.value
            product_id = review_data['product_id']
            rating = review_data['rating']
            # Assuming timestamp is a Unix timestamp (seconds since epoch)
            review_timestamp = review_data['timestamp']

            time_window_start, time_window_end = self._get_time_window(review_timestamp)
            buffer_key = (product_id, time_window_start.isoformat())

            if buffer_key not in self.aggregation_buffer:
                self.aggregation_buffer[buffer_key] = {
                    'review_count': 0,
                    'positive_review_count': 0,
                    'negative_review_count': 0,
                    'total_rating_sum': 0,
                    'time_window_end': time_window_end # Store to use during flush
                }

            self.aggregation_buffer[buffer_key]['review_count'] += 1
            self.aggregation_buffer[buffer_key]['total_rating_sum'] += rating

            if rating >= POSITIVE_RATING_THRESHOLD:
                self.aggregation_buffer[buffer_key]['positive_review_count'] += 1
            elif rating <= NEGATIVE_RATING_THRESHOLD:
                self.aggregation_buffer[buffer_key]['negative_review_count'] += 1

        except KeyError as e:
            print(f"Error processing message due to missing key: {e} in {message.value}")
        except Exception as e:
            print(f"Unexpected error processing message: {e} in {message.value}")

    def _flush_to_db(self):
        if not self.aggregation_buffer:
            return

        cur = self.conn.cursor()
        records_to_upsert = []

        for (product_id, time_window_start_str), data in self.aggregation_buffer.items():
            time_window_start = datetime.fromisoformat(time_window_start_str)
            records_to_upsert.append((
                product_id,
                time_window_start,
                data['time_window_end'],
                data['review_count'],
                data['positive_review_count'],
                data['negative_review_count'],
                data['total_rating_sum']
            ))

        # Using psycopg2.extras.execute_values for efficient batch upsert
        # This SQL uses an UPSERT (INSERT ... ON CONFLICT UPDATE)
        upsert_sql = """
            INSERT INTO product_review_velocity (
                product_id, time_window_start, time_window_end,
                review_count, positive_review_count, negative_review_count, total_rating_sum
            ) VALUES %s
            ON CONFLICT (product_id, time_window_start) DO UPDATE SET
                time_window_end = EXCLUDED.time_window_end,
                review_count = product_review_velocity.review_count + EXCLUDED.review_count,
                positive_review_count = product_review_velocity.positive_review_count + EXCLUDED.positive_review_count,
                negative_review_count = product_review_velocity.negative_review_count + EXCLUDED.negative_review_count,
                total_rating_sum = product_review_velocity.total_rating_sum + EXCLUDED.total_rating_sum,
                last_updated = CURRENT_TIMESTAMP;
        """
        try:
            extras.execute_values(
                cur, upsert_sql, records_to_upsert,
                page_size=FLUSH_BUFFER_SIZE
            )
            self.conn.commit()
            print(f"Flushed {len(self.aggregation_buffer)} aggregated records to DB.")
            self.aggregation_buffer.clear()
            self.last_flush_time = time.time()
        except Exception as e:
            self.conn.rollback()
            print(f"Error flushing to DB: {e}")
        finally:
            cur.close()


    def run(self):
        print(f"Starting Review Velocity Ingestion Service, consuming from {KAFKA_TOPIC}...")
        try:
            while True:
                messages = self.consumer.poll(timeout_ms=1000, max_records=FLUSH_BUFFER_SIZE)
                if messages:
                    for topic_partition, consumer_records in messages.items():
                        for record in consumer_records:
                            self._process_message(record)

                if len(self.aggregation_buffer) >= FLUSH_BUFFER_SIZE or \
                   (time.time() - self.last_flush_time) >= FLUSH_INTERVAL_SECONDS:
                    self._flush_to_db()

                time.sleep(1) # Small delay to prevent busy-waiting if no messages

        except KeyboardInterrupt:
            print("Shutting down ingestion service.")
        except Exception as e:
            print(f"Unhandled exception in ingestion service: {e}")
        finally:
            self.consumer.close()
            self.conn.close()
            print("Ingestion service stopped.")

if __name__ == '__main__':
    service = ReviewVelocityIngestionService()
    service.run()
