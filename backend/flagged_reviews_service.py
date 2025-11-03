
# backend/flagged_reviews_service.py - Core API endpoints for Flagged Reviews Service

from flask import Flask, jsonify, request
from datetime import datetime
import logging
import uuid

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Mock Database / ORM Client (Replace with actual DB client later) ---
class MockDB:
    def __init__(self):
        self.flagged_reviews = {} # Stores FlaggedReview objects
        self.reviews = {} # Stores Review objects

    def get_summary_data(self):
        # In a real application, this would query the database
        # For now, returning mock counts based on in-memory data
        total = len(self.flagged_reviews)
        pending = sum(1 for fr in self.flagged_reviews.values() if fr['status'] == 'PENDING')
        abusive = sum(1 for fr in self.flagged_reviews.values() if fr['status'] == 'ABUSIVE')
        not_abusive = sum(1 for fr in self.flagged_reviews.values() if fr['status'] == 'NOT_ABUSIVE')
        
        # Simulate new flags today (simple logic for mock)
        new_flags_today = sum(1 for fr in self.flagged_reviews.values() if (datetime.utcnow() - datetime.fromisoformat(fr['flag_timestamp'].replace('Z', ''))).days == 0)

        return {
            "total_flagged": total,
            "pending_reviews": pending,
            "abusive_reviews": abusive,
            "not_abusive_reviews": not_abusive,
            "new_flags_today": new_flags_today
        }

    def get_flagged_review_details(self, flag_id: str):
        flag = self.flagged_reviews.get(flag_id)
        if flag:
            review = self.reviews.get(flag['review_id'])
            if review:
                # Merge flag details with review details
                details = {**review, **flag}
                return details
        return None

    def create_flag(self, review_id: str, flag_type: str, status: str = 'PENDING'):
        flag_id = str(uuid.uuid4())
        new_flag = {
            "flag_id": flag_id,
            "review_id": review_id,
            "flag_type": flag_type,
            "flag_timestamp": datetime.utcnow().isoformat() + 'Z',
            "status": status
        }
        self.flagged_reviews[flag_id] = new_flag
        # Ensure the corresponding review is marked as flagged
        if review_id in self.reviews:
            self.reviews[review_id]['is_flagged'] = True
        return new_flag

    def update_flagged_review_status(self, flag_id: str, new_status: str, analyst_notes: str, updated_by: str):
        if flag_id in self.flagged_reviews:
            flag = self.flagged_reviews[flag_id]
            flag['status'] = new_status
            flag['analyst_notes'] = analyst_notes
            flag['last_updated_by'] = updated_by
            flag['last_updated_timestamp'] = datetime.utcnow().isoformat() + 'Z'
            return flag
        return None

    def add_review(self, review_data: dict):
        review_id = review_data.get("review_id", str(uuid.uuid4()))
        review_data['review_id'] = review_id
        review_data['is_flagged'] = review_data.get('is_flagged', False)
        self.reviews[review_id] = review_data
        return review_id

db = MockDB()

# --- Pre-populate mock data for dashboard ---
mock_review_1_id = db.add_review({
    "reviewer_id": "user_a", "product_asin": "B00ABCD",
    "review_date": "2023-10-25T09:00:00Z", "rating": 1, "seller_id": "seller_x",
    "review_text": "This is a terrible product and contains hate_word_1."
})
mock_review_2_id = db.add_review({
    "reviewer_id": "user_b", "product_asin": "B00EFGH",
    "review_date": "2023-10-25T10:30:00Z", "rating": 5, "seller_id": "seller_y",
    "review_text": "Great product! Call me at 123-456-7890 for more info."
})
mock_review_3_id = db.add_review({
    "reviewer_id": "user_c", "product_asin": "B00IJKL",
    "review_date": "2023-10-26T11:00:00Z", "rating": 3, "seller_id": "seller_z",
    "review_text": "Neutral review. Visit my website for free_shipping offers."
})

db.create_flag(mock_review_1_id, "HATE_SPEECH", "PENDING")
db.create_flag(mock_review_2_id, "PERSONAL_INFO", "ABUSIVE")
db.create_flag(mock_review_3_id, "SPAM", "PENDING")
db.create_flag(db.reviews[list(db.reviews.keys())[0]]['review_id'], "SPAM", "NOT_ABUSIVE") # Another flag

# --- API Endpoints ---
@app.route("/api/v1/flagged-reviews/summary", methods=["GET"])
def get_flagged_reviews_summary():
    """Retrieves a summary of flagged reviews for the dashboard."""
    summary_data = db.get_summary_data()
    return jsonify(summary_data)

@app.route("/api/v1/flagged-reviews/<string:flag_id>", methods=["GET"])
def get_flagged_review_by_id(flag_id):
    """Retrieves full details of a specific flagged review by its flag_id."""
    details = db.get_flagged_review_details(flag_id)
    if details:
        return jsonify(details)
    return jsonify({"message": "Flagged review not found"}), 404

@app.route("/api/v1/flagged-reviews/<string:flag_id>/status", methods=["PUT"])
def update_flagged_review_status(flag_id):
    """Updates the status of a flagged review."""
    data = request.get_json()
    new_status = data.get("status")
    analyst_notes = data.get("analyst_notes")
    updated_by = data.get("updated_by", "system_user") # In real app, get from auth context

    ALLOWED_STATUSES = ["PENDING", "ABUSIVE", "NOT_ABUSIVE", "RESOLVED"]

    if not new_status or new_status not in ALLOWED_STATUSES:
        return jsonify({"message": "Invalid status provided"}), 400

    updated_flag = db.update_flagged_review_status(flag_id, new_status, analyst_notes, updated_by)
    if updated_flag:
        logger.info(
            f"Flag status changed: flag_id={flag_id}, new_status={new_status}, "
            f"analyst={updated_by}, timestamp={updated_flag['last_updated_timestamp']}"
        )
        return jsonify(updated_flag), 200
    
    logger.warning(f"Failed to update flag status: flag_id={flag_id} not found by analyst {updated_by}")
    return jsonify({"message": "Flagged review not found"}), 404

# To run this mock API:
# if __name__ == "__main__":
#     app.run(debug=True, port=5001)
