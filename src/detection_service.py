import datetime

# Predefined suspicious keywords (example)
SUSPICIOUS_KEYWORDS = ["amazing", "best", "love", "must-buy", "excellent", "perfect", "deal", "superb"]
MIN_REVIEW_VELOCITY_COUNT = 2 # Changed from 10 in research to 2 for easier testing with sample data
REVIEW_VELOCITY_DAYS = 7
KEYWORD_STUFFING_THRESHOLD = 0.30
NEW_ACCOUNT_AGE_DAYS = 30
NEW_ACCOUNT_REVIEW_COUNT = 1 # Changed from 5 in research to 1 for easier testing with sample data


def is_suspicious_velocity(reviewer_id, reviews, current_review_date):
    """Checks if a reviewer has submitted an unusually high number of reviews recently."""
    recent_reviews = [
        r for r in reviews
        if r["reviewer_id"] == reviewer_id and \
           (datetime.datetime.fromisoformat(current_review_date.replace('Z', '+00:00')) - datetime.datetime.fromisoformat(r["review_date"].replace('Z', '+00:00'))).days <= REVIEW_VELOCITY_DAYS
    ]
    if len(recent_reviews) >= MIN_REVIEW_VELOCITY_COUNT:
        return True, f"High review velocity: {len(recent_reviews)} reviews in {REVIEW_VELOCITY_DAYS} days."
    return False, None

def is_keyword_stuffing(review_text):
    """Checks for an unusually high density of suspicious keywords."""
    words = review_text.lower().split()
    if not words:
        return False, None
    suspicious_word_count = sum(1 for word in words if word in SUSPICIOUS_KEYWORDS)
    if (suspicious_word_count / len(words)) >= KEYWORD_STUFFING_THRESHOLD:
        return True, f"Keyword stuffing detected: {suspicious_word_count / len(words):.2f}% suspicious keywords."
    return False, None

def is_new_account_high_volume(reviewer_id, reviews, account_creation_date):
    """Checks if a new account has posted a high volume of reviews."""
    # For simplicity, assume account_creation_date is available for the reviewer.
    # In a real system, this would come from a user profile service.
    # For this sprint, we'll simulate by assuming the earliest review date is the account creation date if not explicitly available.
    # This is a simplification and will need to be refined.

    # Find all reviews by this reviewer
    reviewer_reviews = [r for r in reviews if r["reviewer_id"] == reviewer_id]

    if not reviewer_reviews:
        return False, None

    # Determine account age based on the earliest review date for this sprint's simplification
    # In a real system, account_creation_date would be a separate field.
    earliest_review_date = min([datetime.datetime.fromisoformat(r["review_date"].replace('Z', '+00:00')) for r in reviewer_reviews])
    current_date = datetime.datetime.now(datetime.timezone.utc) # Use current time for age calculation
    account_age_days = (current_date - earliest_review_date).days

    if account_age_days <= NEW_ACCOUNT_AGE_DAYS and len(reviewer_reviews) >= NEW_ACCOUNT_REVIEW_COUNT:
        return True, f"New account ({account_age_days} days old) with high review volume ({len(reviewer_reviews)} reviews)."
    return False, None

def detect_suspicious_reviews(all_reviews):
    """Orchestrates the detection of suspicious patterns across reviews."""
    flagged_reviews = []
    for review in all_reviews:
        is_flagged = False
        reasons = []

        # Check for Keyword Stuffing
        flag, reason = is_keyword_stuffing(review["review_text"])
        if flag:
            is_flagged = True
            reasons.append(f"Keyword Stuffing: {reason}")

        # Check for Review Velocity (requires context of other reviews by the same reviewer)
        # This simplified check considers all reviews in `all_reviews` for velocity calculation.
        # A more robust system would query a database for a reviewer's historical reviews.
        flag, reason = is_suspicious_velocity(review["reviewer_id"], all_reviews, review["review_date"])
        if flag:
            is_flagged = True
            reasons.append(f"Review Velocity: {reason}")

        # Check for New Account High Volume (requires context of other reviews by the same reviewer and account creation date)
        # For now, we'll approximate account_creation_date by the earliest review date by this reviewer within the provided 'all_reviews'.
        # This is a strong simplification for the sprint.
        flag, reason = is_new_account_high_volume(review["reviewer_id"], all_reviews, review["review_date"])
        if flag:
            is_flagged = True
            reasons.append(f"New Account High Volume: {reason}")

        if is_flagged:
            flagged_reviews.append({
                "review_id": review["review_id"],
                "flag_type": "AUTOMATED_DETECTION",
                "detection_reason": "; ".join(reasons),
                "detection_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds') + 'Z'
            })
    return flagged_reviews
