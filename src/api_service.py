import json
from flask import Flask, jsonify, request
from src.flagged_reviews_store import get_all_flagged_reviews, get_flagged_review_by_id, add_flagged_review
from src.detection_service import detect_suspicious_reviews
import os

app = Flask(__name__)

# --- Data Loading (Temporary for Sprint 1) ---
# In a real system, this would be a database interaction or a dedicated service call.
def load_all_reviews():
    reviews_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_reviews.json')
    if not os.path.exists(reviews_file_path):
        return []
    with open(reviews_file_path, 'r') as f:
        return json.load(f)

ALL_REVIEWS = load_all_reviews() # Load all reviews once on startup

# --- Endpoint 1: Get all flagged reviews ---
@app.route('/flagged_reviews', methods=['GET'])
def get_flagged_cases():
    flagged_cases = get_all_flagged_reviews()
    # Basic sorting by detection_timestamp (descending)
    flagged_cases.sort(key=lambda x: x.get('detection_timestamp', ''), reverse=True)
    return jsonify(flagged_cases)

# --- Endpoint 2: Get detailed info for a specific flagged review (and its original review details) ---
@app.route('/flagged_reviews/<string:flag_id>', methods=['GET'])
def get_flagged_case_details(flag_id):
    flagged_case = get_flagged_review_by_id(flag_id)
    if not flagged_case:
        return jsonify({"error": "Flagged case not found"}), 404

    # Fetch original review details
    original_review = next((review for review in ALL_REVIEWS if review["review_id"] == flagged_case["review_id"]), None)

    if not original_review:
        # This shouldn't happen if data integrity is maintained, but good to handle
        return jsonify({"error": "Original review for flagged case not found"}), 404

    # Combine flagged case info with original review details
    detailed_case = {**flagged_case, "original_review_details": original_review}
    return jsonify(detailed_case)

# --- Endpoint 3: (Internal/Development) Trigger detection and store flags ---
# This endpoint is for testing and demonstration purposes in this sprint.
# In a production system, detection would be an automated, scheduled process.
@app.route('/trigger_detection', methods=['POST'])
def trigger_detection():
    # Clear existing flagged reviews for a fresh run (for demo purposes)
    # This is a simplification; in real life, you'd manage new flags vs. existing.
    # For now, let's just re-run and add.
    # with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'flagged_reviews.json'), 'w') as f:
    #     f.write("[]")

    all_reviews = load_all_reviews()
    flagged_data = detect_suspicious_reviews(all_reviews)

    added_flag_ids = []
    for flag_entry in flagged_data:
        # Enrich the flag_entry with product_id and reviewer_id from original review
        original_review = next((review for review in all_reviews if review["review_id"] == flag_entry["review_id"]), None)
        if original_review:
            flag_entry["product_id"] = original_review.get("product_id")
            flag_entry["reviewer_id"] = original_review.get("reviewer_id")
        added_flag_ids.append(add_flagged_review(flag_entry))

    return jsonify({"message": f"Detection triggered. {len(added_flag_ids)} new suspicious reviews flagged."}), 200

if __name__ == '__main__':
    # Initial run of detection to populate some data for the API
    # This would typically be a separate scheduled job, but for demo, we run it at startup if the file is empty.
    from src.flagged_reviews_store import FLAGGED_REVIEWS_FILE
    if not os.path.exists(FLAGGED_REVIEWS_FILE) or os.stat(FLAGGED_REVIEWS_FILE).st_size == 0:
        print("No flagged reviews found. Triggering initial detection...")
        all_reviews = load_all_reviews()
        flagged_data = detect_suspicious_reviews(all_reviews)
        for flag_entry in flagged_data:
            original_review = next((review for review in all_reviews if review["review_id"] == flag_entry["review_id"]), None)
            if original_review:
                flag_entry["product_id"] = original_review.get("product_id")
                flag_entry["reviewer_id"] = original_review.get("reviewer_id")
            add_flagged_review(flag_entry)
        print(f"Initial detection complete. {len(flagged_data)} reviews flagged.")

    app.run(debug=True, port=5000)
