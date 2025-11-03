from datetime import datetime

# --- Configuration for Flagging Rules (Can be externalized later) ---
SUSPICIOUS_KEYWORDS = ["scam", "fraud", "fake review", "discount code", "free offer", "buy now"]
VELOCITY_THRESHOLD_HOURS = 1 # Number of hours to check for high velocity
VELOCITY_THRESHOLD_COUNT = 5 # Max reviews per product within the threshold hours

def _check_suspicious_keywords(review_text: str) -> bool:
    """Checks if the review text contains any suspicious keywords."""
    review_text_lower = review_text.lower()
    return any(keyword in review_text_lower for keyword in SUSPICIOUS_KEYWORDS)

def _check_review_velocity(product_id: str, db_client) -> bool:
    """Checks for unusual review velocity for a given product."""
    review_count = db_client.count_reviews_for_product_in_window(product_id, VELOCITY_THRESHOLD_HOURS)
    return review_count >= VELOCITY_THRESHOLD_COUNT

def _check_duplicate_content(review_text: str, current_review_id: str, db_client) -> bool:
    """Checks if identical review content exists from another user."""
    return db_client.check_for_duplicate_review_text(review_text, current_review_id)

def flag_review(review_data: dict, db_client) -> dict:
    """
    Applies various flagging rules to a review and updates its status.
    Returns the review_data dictionary with 'is_flagged' and 'flag_reason' updated.
    """
    review_data['is_flagged'] = False
    review_data['flag_reason'] = None
    review_data['flag_date'] = None
    reasons = []

    # 1. Check for suspicious keywords
    if _check_suspicious_keywords(review_data['review_text']):
        reasons.append("Suspicious keyword usage detected.")

    # 2. Check for unusual review velocity for the product
    if _check_review_velocity(review_data['product_id'], db_client):
        reasons.append(f"Unusual review velocity detected for product (>{VELOCITY_THRESHOLD_COUNT} in {VELOCITY_THRESHOLD_HOURS}h).")

    # 3. Check for duplicate content from other users
    if _check_duplicate_content(review_data['review_text'], review_data['review_id'], db_client):
        reasons.append("Duplicate review content detected.")

    if reasons:
        review_data['is_flagged'] = True
        review_data['flag_reason'] = " | ".join(reasons)
        review_data['flag_date'] = datetime.utcnow()

    return review_data
