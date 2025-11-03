# src/api/review_status_api.py

from flask import Flask, request, jsonify
from datetime import datetime
from enum import Enum

app = Flask(__name__)

# --- Data Model Definition (aligned with Task 5.1 and extended for 5.2) ---
class ReviewStatus(Enum):
    UNDER_INVESTIGATION = "Under Investigation"
    CONFIRMED_ABUSE = "Confirmed Abuse"
    FALSE_POSITIVE = "False Positive"

# Pseudocode for a database client/ORM
# In a real application, this would interact with a database like MongoDB, PostgreSQL, etc.
class MockReviewDatabase:
    def __init__(self):
        # Initial mock data for flagged reviews
        self.reviews = {
            "rev_123": {
                "review_id": "rev_123",
                "flagged_reason": ["rapid_burst"],
                "flagging_timestamp": "2023-10-26T10:00:00Z",
                "review_text": "This is a suspicious review 1.",
                "rating": 1,
                "reviewer_id": "user_A",
                "product_id": "prod_X",
                "investigation_status": ReviewStatus.UNDER_INVESTIGATION.value,
                "investigator_id": None,
                "status_update_timestamp": None
            },
            "rev_456": {
                "review_id": "rev_456",
                "flagged_reason": ["identical_reviews"],
                "flagging_timestamp": "2023-10-26T11:30:00Z",
                "review_text": "Another bad review 2.",
                "rating": 2,
                "reviewer_id": "user_B",
                "product_id": "prod_Y",
                "investigation_status": ReviewStatus.UNDER_INVESTIGATION.value,
                "investigator_id": None,
                "status_update_timestamp": None
            }
        }

    def get_review_by_id(self, review_id: str) -> dict | None:
        """Retrieves a review by its ID."""
        return self.reviews.get(review_id)

    def update_review_status(self, review_id: str, new_status: str, investigator_id: str) -> bool:
        """
        Updates the investigation status of a review.
        Returns True if updated, False otherwise (e.g., review_id not found).
        """
        if review_id in self.reviews:
            review = self.reviews[review_id]
            review["investigation_status"] = new_status
            review["investigator_id"] = investigator_id
            review["status_update_timestamp"] = datetime.utcnow().isoformat(timespec='seconds') + "Z"
            return True
        return False

# Initialize the mock database
db = MockReviewDatabase()

# --- API Endpoint Implementation ---
@app.route("/reviews/<string:review_id>/status", methods=["PUT"])
def update_review_status_endpoint(review_id: str):
    """
    API endpoint to update the investigation status of a flagged review.
    Request Body:
        {
            "status": "Confirmed Abuse" | "False Positive" | "Under Investigation",
            "investigator_id": "investigator_alpha" (optional, for logging)
        }
    """
    data = request.get_json()

    if not data or "status" not in data:
        return jsonify({"error": "Missing 'status' in request body."}), 400

    new_status_str = data["status"]
    # In a real app, investigator_id would come from authenticated user context
    investigator_id = data.get("investigator_id", "System/Unauthenticated")

    # Validate the new status
    try:
        # Convert string to Enum value, handling spaces and case insensitivity
        valid_status_enum_value = ReviewStatus[new_status_str.upper().replace(" ", "_")].value
    except KeyError:
        allowed_statuses = [s.value for s in ReviewStatus]
        return jsonify({
            "error": f"Invalid status: '{new_status_str}'. Allowed values are: {allowed_statuses}"
        }), 400

    # Check if review exists
    if not db.get_review_by_id(review_id):
        return jsonify({"error": f"Review with ID '{review_id}' not found."}), 404

    # Update the review status in the database
    if db.update_review_status(review_id, valid_status_enum_value, investigator_id):
        return jsonify({
            "message": f"Review '{review_id}' status updated to '{valid_status_enum_value}' by '{investigator_id}'."
        }), 200
    else:
        # This case implies a database update failure after finding the review,
        # which should ideally be rare with robust DB interactions.
        return jsonify({"error": f"Failed to update status for review '{review_id}' due to an internal error."}), 500

# Example of how to run the Flask app (for local testing):
# if __name__ == "__main__":
#     app.run(debug=True, port=5000)