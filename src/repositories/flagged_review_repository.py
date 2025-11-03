from typing import List, Dict, Optional
from models.flagged_review import FlaggedReview

class FlaggedReviewRepository:
    def __init__(self):
        self._flagged_reviews: Dict[str, FlaggedReview] = {}

    def save(self, flagged_review: FlaggedReview):
        """Saves a flagged review to the repository."""
        self._flagged_reviews[flagged_review.review_id] = flagged_review
        print(f"Saved flagged review: {flagged_review.review_id}")

    def get_all(self) -> List[FlaggedReview]:
        """Retrieves all flagged reviews."""
        return list(self._flagged_reviews.values())

    def get_by_id(self, review_id: str) -> Optional[FlaggedReview]:
        """Retrieves a single flagged review by its ID."""
        return self._flagged_reviews.get(review_id)