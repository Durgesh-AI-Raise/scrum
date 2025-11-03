
import json
from kafka import KafkaConsumer
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import logging

# Configuration
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'amazon-reviews-raw'
MONGO_DB_CONNECTION_STRING = 'mongodb://localhost:27017/'
MONGO_DB_NAME = 'review_system'
REVIEWS_COLLECTION = 'reviews'
REVIEWERS_COLLECTION = 'reviewers'

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def start_persistence_service():
    consumer = None
    mongo_client = None
    try:
        # Kafka Consumer
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='latest', # Start consuming from the latest message
            enable_auto_commit=True,
            group_id='review-persistence-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logging.info(f"Kafka Consumer started for topic: {KAFKA_TOPIC}")

        # MongoDB Client
        mongo_client = MongoClient(MONGO_DB_CONNECTION_STRING)
        db = mongo_client[MONGO_DB_NAME]
        reviews_collection = db[REVIEWS_COLLECTION]
        reviewers_collection = db[REVIEWERS_COLLECTION]
        logging.info(f"Connected to MongoDB database: {MONGO_DB_NAME}")

        for message in consumer:
            ingested_data = message.value
            review_data = ingested_data.get('review')
            reviewer_data = ingested_data.get('reviewer')

            if review_data:
                try:
                    # Insert review data (or update if review_id is present, but typically reviews are immutable)
                    reviews_collection.insert_one(review_data)
                    logging.info(f"Persisted review: {review_data['review_id']}")
                except PyMongoError as e:
                    logging.error(f"Error persisting review {review_data.get('review_id')}: {e}")
            else:
                logging.warning("Received message without 'review' data.")

            if reviewer_data:
                try:
                    # Upsert reviewer data to keep it updated
                    # Increment total_reviews_count and update last_review_timestamp
                    reviewers_collection.update_one(
                        {'reviewer_id': reviewer_data['reviewer_id']},
                        {
                            '$set': {
                                'username': reviewer_data.get('username'),
                                'account_age_days': reviewer_data.get('account_age_days'),
                                'ip_address_last_known': reviewer_data.get('ip_address_last_known'),
                                'device_info_last_known': reviewer_data.get('device_info_last_known'),
                                'last_review_timestamp': reviewer_data.get('last_review_timestamp'),
                                'flagged': reviewer_data.get('flagged', False), # Default to False if not present
                                'flagging_reason': reviewer_data.get('flagging_reason')
                            },
                            '$addToSet': {
                                'purchase_history_product_ids': {'$each': reviewer_data.get('purchase_history_product_ids', [])}
                            },
                            '$inc': {'total_reviews_count': 1} # Increment review count
                        },
                        upsert=True
                    )
                    logging.info(f"Upserted reviewer: {reviewer_data['reviewer_id']}")
                except PyMongoError as e:
                    logging.error(f"Error upserting reviewer {reviewer_data.get('reviewer_id')}: {e}")
            else:
                logging.warning("Received message without 'reviewer' data.")

    except Exception as e:
        logging.critical(f"Unhandled error in persistence service: {e}", exc_info=True)
    finally:
        if consumer:
            consumer.close()
            logging.info("Kafka Consumer closed.")
        if mongo_client:
            mongo_client.close()
            logging.info("MongoDB client closed.")

if __name__ == '__main__':
    start_persistence_service()
