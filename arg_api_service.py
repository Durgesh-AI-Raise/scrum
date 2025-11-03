from arg_review_service import get_review_by_id, update_review_flags
from arg_spam_detection import detect_spam

def check_review_for_spam_api(review_id: str, review_text: str) -> dict:
    """
    Simulates an API endpoint for checking a review for spam.
    Accepts a review ID and review text, processes it for spam, 
    updates the review's spam flag in the database, and returns the result.
    """
    review = get_review_by_id(review_id)
    if not review:
        return {"status": "error", "message": "Review not found."}

    is_spam, detection_reason = detect_spam(review_text)

    # Update the review in the database
    update_review_flags(review_id, spam_flag=is_spam, detection_reason=detection_reason)

    return {
        "status": "success",
        "review_id": review_id,
        "is_spam": is_spam,
        "detection_reason": detection_reason
    }
