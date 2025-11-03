from typing import List
from data_models import FlaggedReview

class FlaggedReviewStorage:
    """
    Simulates a storage mechanism for flagged reviews.
    For this sprint, it uses an in-memory list.
    """
    def __init__(self):
        self._storage: List[FlaggedReview] = []

    def save_flagged_review(self, flagged_review: FlaggedReview):
        """
        Saves a single flagged review to the storage.
        """
        self._storage.append(flagged_review)
        print(f"Saved Flagged Review: {flagged_review.review_id} for product {flagged_review.product_id}")

    def get_all_flagged_reviews(self) -> List[FlaggedReview]:
        """
        Retrieves all currently stored flagged reviews.
        """
        return self._storage
