from confluent_kafka import Consumer, KafkaException
import json
import logging
from reviewguard.core.review_parser import ReviewModel
from reviewguard.db.mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class ReviewConsumer:
    def __init__(self, kafka_config: dict, topic: str, mongodb_client: MongoDBClient):
        self.consumer = Consumer(kafka_config)
        self.topic = topic
        self.mongodb_client = mongodb_client
        self.running = True

    def start(self):
        logger.info(f"Starting Kafka consumer for topic: {self.topic}")
        self.consumer.subscribe([self.topic])
        while self.running:
            try:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().is_eof():
                        logger.info("Reached end of topic partition. Exiting.")
                        break
                    else:
                        raise KafkaException(msg.error())
                else:
                    self._process_message(msg)
            except KeyboardInterrupt:
                logger.info("Consumer interrupted by user.")
                self.running = False
            except Exception as e:
                logger.error(f"Error while consuming message: {e}")
        self.consumer.close()
        logger.info("Kafka consumer closed.")

    def _process_message(self, msg):
        try:
            review_data_raw = json.loads(msg.value().decode('utf-8'))
            logger.debug(f"Received raw review: {review_data_raw.get('id', 'N/A')}")

            # Parse and validate using Pydantic model
            review = ReviewModel.from_raw_data(review_data_raw)
            review_dict = review.model_dump(by_alias=True)

            # Store in MongoDB
            inserted_id = self.mongodb_client.insert_review(review_dict)
            if inserted_id:
                logger.info(f"Successfully ingested and stored review: {review.review_id}")
            else:
                logger.error(f"Failed to store review: {review.review_id}")

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from message: {msg.value()}")
        except ValueError as ve:
            logger.error(f"Data validation error for message {msg.value()}: {ve}")
        except Exception as e:
            logger.error(f"Unexpected error processing message {msg.value()}: {e}")

    def stop(self):
        self.running = False

if __name__ == '__main__':
    # Example Usage (assuming Kafka and MongoDB are running)
    kafka_conf = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'review_ingestion_group',
        'auto.offset.reset': 'earliest'
    }
    mongo_client = MongoDBClient(host='localhost', port=27017, db_name='reviewguard_db')

    consumer = ReviewConsumer(kafka_conf, 'product_reviews', mongo_client)
    consumer.start()
