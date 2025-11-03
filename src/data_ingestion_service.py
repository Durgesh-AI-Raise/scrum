from kafka import KafkaConsumer
from pymongo import MongoClient
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIngestionService:
    def __init__(self, kafka_brokers, kafka_topic, mongo_uri, mongo_db, mongo_collection):
        self.consumer = KafkaConsumer(
            kafka_topic,
            bootstrap_servers=kafka_brokers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='review-ingestion-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[mongo_db]
        self.collection = self.db[mongo_collection]
        logger.info(f"Initialized DataIngestionService for topic: {kafka_topic}")

    def consume_and_store(self):
        logger.info("Starting to consume messages...")
        for message in self.consumer:
            review_data = message.value
            logger.debug(f"Received review: {review_data.get('reviewId')}")
            try:
                self.collection.insert_one(review_data)
                logger.info(f"Successfully stored review: {review_data.get('reviewId')}")
            except Exception as e:
                logger.error(f"Error storing review {review_data.get('reviewId')}: {e}")
        logger.info("Consumer stopped.")

if __name__ == "__main__":
    KAFKA_BROKERS = ['localhost:9092'] # Replace with actual Kafka broker addresses
    KAFKA_TOPIC = 'raw-reviews'
    MONGO_URI = 'mongodb://localhost:27017/' # Replace with actual MongoDB URI
    MONGO_DB = 'aris'
    MONGO_COLLECTION = 'raw_reviews'

    service = DataIngestionService(KAFKA_BROKERS, KAFKA_TOPIC, MONGO_URI, MONGO_DB, MONGO_COLLECTION)
    service.consume_and_store()
