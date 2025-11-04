import json
import os
import uuid
from datetime import datetime, timezone

FLAGGED_REVIEWS_FILE = "data/flagged_reviews.json"

def _load_flagged_reviews():
    """Loads all flagged reviews from the JSON file."""
    if not os.path.exists(FLAGGED_REVIEWS_FILE):
        return []
    with open(FLAGGED_REVIEWS_FILE, 'r') as f:
        return json.load(f)

def _save_flagged_reviews(flagged_reviews_list):
    """Saves the list of flagged reviews to the JSON file."""
    os.makedirs(os.path.dirname(FLAGGED_REVIEWS_FILE), exist_ok=True)
    with open(FLAGGED_REVIEWS_FILE, 'w') as f:
        json.dump(flagged_reviews_list, f, indent=2)

def add_flagged_review(review_data):
    """
    Adds a new flagged review to the temporary store.
    review_data is expected to contain:
    {'review_id', 'product_id', 'reviewer_id', 'flag_type', 'detection_reason', 'detection_timestamp'}
    """
    flagged_reviews = _load_flagged_reviews()
    new_flag = {
        "flag_id": str(uuid.uuid4()), # Generate a unique ID for the flag itself
        "review_id": review_data["review_id"],
        "product_id": review_data.get("product_id"),
        "reviewer_id": review_data.get("reviewer_id"),
        "flag_type": review_data["flag_type"],
        "detection_reason": review_data["detection_reason"],
        "detection_timestamp": review_data["detection_timestamp"],
        "status": "PENDING_REVIEW", # Default status
        "analyst_id": None,
        "priority": "MEDIUM" # Default priority
    }
    flagged_reviews.append(new_flag)
    _save_flagged_reviews(flagged_reviews)
    return new_flag["flag_id"]

def get_all_flagged_reviews():
    """Retrieves all flagged reviews from the temporary store."""
    return _load_flagged_reviews()

def get_flagged_review_by_id(flag_id):
    """Retrieves a single flagged review by its flag_id."""
    flagged_reviews = _load_flagged_reviews()
    for review in flagged_reviews:
        if review["flag_id"] == flag_id:
            return review
    return None
