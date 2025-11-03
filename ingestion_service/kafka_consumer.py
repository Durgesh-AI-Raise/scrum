from confluent_kafka import Consumer, KafkaException
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_consumer():
    conf = {
        'bootstrap.servers': os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'group.id': 'review-ingestion-group',
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    topic_raw = 'product-reviews-raw'

    logging.info(f"Starting Kafka consumer for topic: {topic_raw}")

    try:
        consumer.subscribe([topic_raw])

        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaException._PARTITION_EOF:
                    logging.info("End of partition reached.")
                else:
                    logging.error(f"Kafka consumer error: {msg.error()}")
                continue

            review_data_raw = msg.value().decode('utf-8')
            logging.info(f"Received raw message: {review_data_raw}")
            # Placeholder for validation and storage (RATS-3, RATS-4)

    except KeyboardInterrupt:
        logging.info("Consumer stopped by user.")
    finally:
        consumer.close()
        logging.info("Kafka consumer closed.")

if __name__ == '__main__':
    run_consumer()