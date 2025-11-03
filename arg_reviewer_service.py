from arg_data_models import Reviewer, db_session

def get_reviewer_by_id(reviewer_id: str) -> Reviewer:
    """
    Retrieves a reviewer by their ID.
    """
    return db_session.query(Reviewer).filter_by(reviewer_id=reviewer_id).first()

def create_or_update_reviewer(reviewer_id: str, username: str = None, email: str = None) -> Reviewer:
    """
    Creates a new reviewer or updates an existing one.
    """
    reviewer = get_reviewer_by_id(reviewer_id)
    if not reviewer:
        reviewer = Reviewer(reviewer_id=reviewer_id, username=username, email=email)
        db_session.add(reviewer)
    else:
        if username:
            reviewer.username = username
        if email:
            reviewer.email = email
    db_session.commit()
    return reviewer

def update_reviewer_activity(reviewer_id: str, total_reviews_increment: int = 0, reviews_last_24h_count: int = None) -> bool:
    """
    Updates basic activity metrics for a reviewer.
    total_reviews_increment: how many reviews to add to the total count.
    reviews_last_24h_count: set the specific count for reviews in the last 24 hours.
                           In a real system, this would be calculated, not directly set.
    """
    reviewer = get_reviewer_by_id(reviewer_id)
    if reviewer:
        reviewer.total_reviews += total_reviews_increment
        if reviews_last_24h_count is not None:
            reviewer.reviews_last_24h = reviews_last_24h_count
        db_session.commit()
        return True
    return False

def update_reviewer_flags(reviewer_id: str, suspicious_flag: bool = None, detection_reason: str = None):
    """
    Updates the suspicious flag and detection reason for a reviewer.
    """
    reviewer = get_reviewer_by_id(reviewer_id)
    if reviewer:
        if suspicious_flag is not None:
            reviewer.suspicious_flag = suspicious_flag
        if detection_reason is not None:
            reviewer.detection_reason = detection_reason
        db_session.commit()
        return True
    return False
