
import json
from kafka import KafkaConsumer, KafkaProducer
from pymongo import MongoClient
from datetime import datetime, timedelta
import logging

# Configuration
KAFKA_BROKER = 'localhost:9092'
RAW_REVIEWS_TOPIC = 'amazon-reviews-raw'
FLAGGED_REVIEWS_TOPIC = 'flagged-reviews'
MONGO_DB_CONNECTION_STRING = 'mongodb://localhost:27017/'
MONGO_DB_NAME = 'review_system'
REVIEWS_COLLECTION = 'reviews'
REVIEWERS_COLLECTION = 'reviewers'

# Sudden High Volume Rules (from detection_rules/sudden_high_volume_rules.md)
RECENT_REVIEW_BURST_THRESHOLD = 5
RECENT_REVIEW_BURST_WINDOW_HOURS = 24
NEW_REVIEWER_ACCOUNT_AGE_DAYS = 7
NEW_REVIEWER_HIGH_ACTIVITY_REVIEWS = 3
NEW_REVIEWER_HIGH_ACTIVITY_WINDOW_HOURS = 24

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def evaluate_review_patterns(review_data, reviewer_data, reviews_collection, reviewers_collection, producer):
    flagged = False
    flagging_reasons = []

    # Rule 1: Recent Review Burst
    # Check if the reviewer has submitted more than X reviews in the last Y hours
    time_threshold = datetime.utcnow() - timedelta(hours=RECENT_REVIEW_BURST_WINDOW_HOURS)
    recent_reviews_count = reviews_collection.count_documents({
        'reviewer_id': reviewer_data['reviewer_id'],
        'ingestion_timestamp': {'$gte': time_threshold.isoformat(timespec='seconds') + 'Z'}
    })

    if recent_reviews_count >= RECENT_REVIEW_BURST_THRESHOLD:
        flagged = True
        flagging_reasons.append(f"Sudden High Volume: {recent_reviews_count} reviews in last {RECENT_REVIEW_BURST_WINDOW_HOURS} hours.")

    # Rule 2: New Reviewer High Activity
    # Check if the reviewer is new and has high activity
    if reviewer_data.get('account_age_days') and reviewer_data['account_age_days'] <= NEW_REVIEWER_ACCOUNT_AGE_DAYS:
        if recent_reviews_count >= NEW_REVIEWER_HIGH_ACTIVITY_REVIEWS: # Reusing recent_reviews_count from above
            flagged = True
            flagging_reasons.append(f"New Reviewer High Activity: Account age {reviewer_data['account_age_days']} days with {recent_reviews_count} reviews in last {NEW_REVIEWER_HIGH_ACTIVITY_WINDOW_HOURS} hours.")

    if flagged:
        reason_str = "; ".join(flagging_reasons)
        logging.warning(f"Reviewer {reviewer_data['reviewer_id']} flagged for: {reason_str}")

        # Update review in MongoDB
        reviews_collection.update_one(
            {'review_id': review_data['review_id']},
            {'$set': {'flagged': True, 'flagging_reason': reason_str}}
        )
        logging.info(f"Updated review {review_data['review_id']} as flagged.")

        # Update reviewer in MongoDB
        reviewers_collection.update_one(
            {'reviewer_id': reviewer_data['reviewer_id']},
            {'$set': {'flagged': True, 'flagging_reason': reason_str}},
            upsert=True # In case reviewer was not yet in collection, though persistence service should handle this
        )
        logging.info(f"Updated reviewer {reviewer_data['reviewer_id']} as flagged.")

        # Publish flagged event to Kafka topic
        flagged_event = {
            "review_id": review_data['review_id'],
            "reviewer_id": reviewer_data['reviewer_id'],
            "flagging_reason": reason_str,
            "timestamp": datetime.utcnow().isoformat(timespec='seconds') + 'Z'
        }
        producer.send(FLAGGED_REVIEWS_TOPIC, flagged_event)
        logging.info(f"Published flagged event for review {review_data['review_id']} to {FLAGGED_REVIEWS_TOPIC}.")


def start_pattern_analysis_service():
    consumer = None
    producer = None
    mongo_client = None
    try:
        consumer = KafkaConsumer(
            RAW_REVIEWS_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='review-pattern-analysis-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logging.info(f"Kafka Consumer started for topic: {RAW_REVIEWS_TOPIC}")

        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logging.info(f"Kafka Producer started for topic: {FLAGGED_REVIEWS_TOPIC}")


        mongo_client = MongoClient(MONGO_DB_CONNECTION_STRING)
        db = mongo_client[MONGO_DB_NAME]
        reviews_collection = db[REVIEWS_COLLECTION]
        reviewers_collection = db[REVIEWERS_COLLECTION]
        logging.info(f"Connected to MongoDB database: {MONGO_DB_NAME}")

        for message in consumer:
            ingested_data = message.value
            review_data = ingested_data.get('review')
            reviewer_data = ingested_data.get('reviewer')

            if review_data and reviewer_data:
                evaluate_review_patterns(review_data, reviewer_data, reviews_collection, reviewers_collection, producer)
            else:
                logging.warning("Received message without complete 'review' or 'reviewer' data.")

    except Exception as e:
        logging.critical(f"Unhandled error in pattern analysis service: {e}", exc_info=True)
    finally:
        if consumer:
            consumer.close()
            logging.info("Kafka Consumer closed.")
        if producer:
            producer.close()
            logging.info("Kafka Producer closed.")
        if mongo_client:
            mongo_client.close()
            logging.info("MongoDB client closed.")

if __name__ == '__main__':
    start_pattern_analysis_service()
