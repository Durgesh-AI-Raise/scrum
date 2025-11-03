import uuid
from datetime import datetime

class ReviewService:
    _reviews_db = {} # In-memory store for simulation

    @staticmethod
    def ingest_review(review_data):
        from .logging_service import LoggingService # Deferred import to avoid circular dependency

        # Apply validation and cleansing (Task 2.3)
        validated_data = ReviewService.validate_and_cleanse(review_data)
        
        new_review = {
            "review_id": str(uuid.uuid4()),
            "product_asin": validated_data.get("product_asin"),
            "reviewer_id": validated_data.get("reviewer_id"),
            "order_id": validated_data.get("order_id"),
            "review_text": validated_data.get("review_text"),
            "rating": validated_data.get("rating"),
            "review_timestamp": datetime.fromisoformat(validated_data["review_timestamp"]) if "review_timestamp" in validated_data and isinstance(validated_data["review_timestamp"], str) else datetime.utcnow(),
            "ip_address": validated_data.get("ip_address"),
            "device_type": validated_data.get("device_type"),
            "country_code": validated_data.get("country_code"),
            "ingested_at": datetime.utcnow(),
            "current_status": "pending" # Initial status
        }
        ReviewService._reviews_db[new_review["review_id"]] = new_review
        LoggingService.log_ingestion(new_review["review_id"]) # Log ingestion (Task 7.2)
        return new_review

    @staticmethod
    def validate_and_cleanse(data):
        # Basic validation: check for required fields
        required_fields = ["product_asin", "reviewer_id", "review_text", "rating"]
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing or empty required field: {field}")
        
        # Basic cleansing: strip whitespace, ensure rating is int
        data["review_text"] = str(data["review_text"]).strip()
        data["product_asin"] = str(data["product_asin"]).upper() # Example: standardize ASIN
        try:
            data["rating"] = int(data["rating"])
            if not (1 <= data["rating"] <= 5):
                raise ValueError("Rating must be between 1 and 5.")
        except (ValueError, TypeError):
            raise ValueError("Rating must be an integer.")

        # Validate review_timestamp format if provided
        if "review_timestamp" in data and data["review_timestamp"]:
            try:
                datetime.fromisoformat(data["review_timestamp"])
            except ValueError:
                raise ValueError("review_timestamp must be in ISO 8601 format.")

        # More complex validation/cleansing would go here (e.g., regex for ASIN, IP format)
        return data

    @staticmethod
    def get_review_by_id(review_id):
        return ReviewService._reviews_db.get(review_id)

    @staticmethod
    def get_all_reviews():
        return list(ReviewService._reviews_db.values())

    @staticmethod
    def update_review_status(review_id, new_status):
        if review_id in ReviewService._reviews_db:
            ReviewService._reviews_db[review_id]["current_status"] = new_status
            return True
        return False