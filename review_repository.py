from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta

class ReviewRepository:
    def __init__(self, db_url="mongodb://localhost:27017/", db_name="reviewguard"):
        self.client = MongoClient(db_url)
        self.db = self.client[db_name]
        self.reviews_collection = self.db.reviews
        self.ingestion_state_collection = self.db.ingestion_state
        self.reviews_collection.create_index("amazon_review_id", unique=True)
        self.reviews_collection.create_index([("product_id", 1), ("ingestion_timestamp", -1)])
        self.reviews_collection.create_index("reviewer_id")
        self.reviews_collection.create_index("risk_score")

    def save_review(self, review_data):
        # Default fields for new reviews
        if "ingestion_timestamp" not in review_data:
            review_data["ingestion_timestamp"] = datetime.utcnow().isoformat() + "Z"
        if "status" not in review_data:
            review_data["status"] = "pending"
        if "flags" not in review_data:
            review_data["flags"] = []
        if "risk_score" not in review_data:
            review_data["risk_score"] = 0
        if "reviewer_profile" not in review_data:
            review_data["reviewer_profile"] = {}
        if "last_manual_status_update" not in review_data:
            review_data["last_manual_status_update"] = None

        # Upsert: insert if not exists, update if exists
        # Use amazon_review_id as the unique key for upsert
        result = self.reviews_collection.update_one(
            {"amazon_review_id": review_data["amazon_review_id"]},
            {"$set": review_data},
            upsert=True
        )
        if result.upserted_id:
            review_data["_id"] = result.upserted_id
            print(f"Inserted review {review_data.get('amazon_review_id')}")
        else:
            print(f"Updated review {review_data.get('amazon_review_id')}")
        return self.reviews_collection.find_one({"amazon_review_id": review_data["amazon_review_id"]})

    def get_latest_ingested_id(self, source="Amazon"):
        state = self.ingestion_state_collection.find_one({"source": source})
        return state.get("last_ingested_id") if state else None

    def update_ingestion_state(self, source="Amazon", last_ingested_id=None, last_timestamp=None):
        update_fields = {"last_successful_run": datetime.utcnow().isoformat() + "Z"}
        if last_ingested_id:
            update_fields["last_ingested_id"] = last_ingested_id
        elif last_timestamp: # Fallback if ID not available
            update_fields["last_ingested_timestamp"] = last_timestamp

        self.ingestion_state_collection.update_one(
            {"source": source},
            {"$set": update_fields},
            upsert=True
        )
        print(f"Updated ingestion state for {source}")

    def update_review_fields(self, review_object_id, update_data):
        result = self.reviews_collection.update_one(
            {"_id": review_object_id},
            {"$set": update_data}
        )
        if result.matched_count:
            print(f"Updated fields for review {review_object_id}")
        return result.matched_count > 0

    def update_review_status(self, review_object_id, new_status):
        result = self.reviews_collection.update_one(
            {"_id": review_object_id},
            {"$set": {"status": new_status, "last_manual_status_update": datetime.utcnow().isoformat() + "Z"}}
        )
        if result.matched_count:
            print(f"Review {review_object_id} status updated to {new_status}")
        return result.matched_count > 0

    def get_flagged_reviews_for_dashboard(self):
        # Exclude reviews marked as 'removed'
        return list(self.reviews_collection.find(
            {"flags": {"$exists": True, "$ne": []}, "status": {"$ne": "removed"}}
        ).sort("risk_score", -1))

    # Methods for flagging engine to query historical data
    def get_recent_5star_reviews(self, product_id, start_time):
        return list(self.reviews_collection.find({
            "product_id": product_id,
            "rating": 5,
            "ingestion_timestamp": {"$gte": start_time}
        }))

    def get_similar_reviews_by_text(self, review_text, min_similarity, exclude_review_id):
        # For MVP, very basic exact match. In production, use NLP.
        return list(self.reviews_collection.find({
            "review_text": review_text,
            "amazon_review_id": {"$ne": exclude_review_id}
        }))

    def get_reviewer_recent_reviews(self, reviewer_id, time_window_hours):
        time_window_start = datetime.utcnow() - timedelta(hours=time_window_hours)
        return list(self.reviews_collection.find({
            "reviewer_id": reviewer_id,
            "ingestion_timestamp": {"$gte": time_window_start.isoformat() + "Z"}
        }))

