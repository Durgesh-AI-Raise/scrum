from datetime import datetime
from arg_data_models import Review, db_session

def ingest_review(review_id: str, reviewer_id: str, product_id: str, review_text: str, review_date: datetime, rating: int) -> Review:
    """
    Ingests a new review into the system.
    """
    new_review = Review(
        review_id=review_id,
        reviewer_id=reviewer_id,
        product_id=product_id,
        review_text=review_text,
        review_date=review_date,
        rating=rating
    )
    db_session.add(new_review)
    db_session.commit()
    return new_review

def get_review_by_id(review_id: str) -> Review:
    """
    Retrieves a review by its ID.
    """
    return db_session.query(Review).filter_by(review_id=review_id).first()

def update_review_flags(review_id: str, spam_flag: bool = None, fabricated_flag: bool = None, suspicious_account_flag: bool = None, detection_reason: str = None):
    """
    Updates the flags and detection reason for a review.
    """
    review = get_review_by_id(review_id)
    if review:
        if spam_flag is not None:
            review.spam_flag = spam_flag
        if fabricated_flag is not None:
            review.fabricated_flag = fabricated_flag
        if suspicious_account_flag is not None:
            review.suspicious_account_flag = suspicious_account_flag
        if detection_reason is not None:
            review.detection_reason = detection_reason
        db_session.commit()
        return True
    return False
