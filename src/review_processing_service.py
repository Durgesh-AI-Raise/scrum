from kafka import KafkaConsumer
from pymongo import MongoClient
import json
import logging
from datetime import datetime
from linguistic_detector import LinguisticDetector
from account_activity_detector import AccountActivityDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReviewProcessingService:
    def __init__(self, kafka_brokers, raw_topic, processed_db, processed_collection):
        self.consumer = KafkaConsumer(
            raw_topic,
            bootstrap_servers=kafka_brokers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='review-detection-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self.mongo_client = MongoClient('mongodb://localhost:27017/')
        self.db = self.mongo_client[processed_db]
        self.processed_collection = self.db[processed_collection]
        self.linguistic_detector = LinguisticDetector()
        self.account_activity_detector = AccountActivityDetector(
            mongo_uri='mongodb://localhost:27017/',
            mongo_db=processed_db,
            processed_collection=processed_collection
        )
        logger.info(f"Initialized ReviewProcessingService for topic: {raw_topic}")

    def process_reviews(self):
        logger.info("Starting to process messages...")
        for message in self.consumer:
            review_data = message.value
            review_id = review_data.get('reviewId', 'unknown')
            review_content = review_data.get('content', '')
            user_id = review_data.get('userId', 'unknown')

            logger.debug(f"Processing review: {review_id} by user: {user_id}")

            linguistic_detection_result = self.linguistic_detector.detect(review_content)
            account_activity_detection_result = self.account_activity_detector.detect(review_data)
            
            overall_flagged = linguistic_detection_result["is_flagged"] or account_activity_detection_result["is_flagged"]
            overall_reasons = linguistic_detection_result["reasons"] + account_activity_detection_result["reasons"]
            
            processed_review = {
                **review_data,
                "linguisticFlag": {
                    "isFlagged": linguistic_detection_result["is_flagged"],
                    "reasons": linguistic_detection_result["reasons"]
                },
                "accountActivityFlag": {
                    "isFlagged": account_activity_detection_result["is_flagged"],
                    "reasons": account_activity_detection_result["reasons"]
                },
                "overallFlag": {
                    "isFlagged": overall_flagged,
                    "reasons": list(set(overall_reasons))
                },
                "status": "pending" if overall_flagged else "approved",
                "processedTimestamp": datetime.utcnow()
            }

            try:
                self.processed_collection.update_one(
                    {'reviewId': review_id},
                    {'$set': processed_review},
                    upsert=True
                )
                logger.info(f"Successfully processed and stored review: {review_id} (Flagged: {overall_flagged})")
            except Exception as e:
                logger.error(f"Error storing processed review {review_id}: {e}")
        logger.info("Processing stopped.")

if __name__ == "__main__":
    KAFKA_BROKERS = ['localhost:9092']
    RAW_REVIEWS_TOPIC = 'raw-reviews'
    PROCESSED_DB = 'aris'
    PROCESSED_COLLECTION = 'processed_reviews'

    service = ReviewProcessingService(KAFKA_BROKERS, RAW_REVIEWS_TOPIC, PROCESSED_DB, PROCESSED_COLLECTION)
    service.process_reviews()
