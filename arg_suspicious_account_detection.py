from arg_data_models import Reviewer

REVIEW_THRESHOLD_24H = 50 # Example threshold

def detect_suspicious_account(reviewer: Reviewer) -> (bool, str):
    """
    Detects suspicious behavior for a given reviewer based on predefined rules.
    Returns a tuple of (is_suspicious, detection_reason).
    """
    if reviewer.reviews_last_24h > REVIEW_THRESHOLD_24H:
        return True, f"High review volume: {reviewer.reviews_last_24h} reviews in 24 hours (threshold: {REVIEW_THRESHOLD_24H})."

    # Add more rules here in future sprints
    # if reviewer.reviews_for_specific_seller > X:
    #    return True, "Reviews concentrated on specific seller."

    return False, "No suspicious activity detected."
