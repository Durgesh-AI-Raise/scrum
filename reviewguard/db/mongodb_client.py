from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging
from typing import List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class MongoDBClient:
    def __init__(self, host='localhost', port=27017, db_name='reviewguard_db'):
        self.client = None
        self.db = None
        self.host = host
        self.port = port
        self.db_name = db_name
        self.connect()

    def connect(self):
        try:
            self.client = MongoClient(self.host, self.port)
            self.db = self.client[self.db_name]
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
            logger.info(f"Successfully connected to MongoDB at {self.host}:{self.port}")
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            self.client = None
            self.db = None

    def insert_review(self, review_data: dict):
        if not self.db:
            logger.error("Database not connected. Cannot insert review.")
            return None
        try:
            # MongoDB will automatically create _id if not provided
            # Ensure 'review_id' is indexed for efficient lookups
            self.db.reviews.create_index([("review_id", 1)], unique=True)
            result = self.db.reviews.insert_one(review_data)
            logger.info(f"Inserted review with DB _id: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting review: {e}")
            return None
    
    def find_review(self, review_id: str) -> dict:
        if not self.db:
            logger.error("Database not connected. Cannot find review.")
            return None
        try:
            return self.db.reviews.find_one({"review_id": review_id})
        except Exception as e:
            logger.error(f"Error finding review {review_id}: {e}")
            return None

    def update_review_fields(self, review_id: str, fields_to_update: dict):
        if not self.db:
            logger.error("Database not connected. Cannot update review fields.")
            return False
        try:
            update_result = self.db.reviews.update_one(
                {"review_id": review_id},
                {"$set": fields_to_update}
            )
            if update_result.matched_count > 0:
                logger.info(f"Updated fields for review ID: {review_id}. Matched: {update_result.matched_count}, Modified: {update_result.modified_count}")
                return True
            else:
                logger.warning(f"No review found with ID {review_id} for update.")
                return False
        except Exception as e:
            logger.error(f"Error updating review fields for {review_id}: {e}")
            return False

    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")