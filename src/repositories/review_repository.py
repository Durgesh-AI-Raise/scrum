from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from src.data_models.review_model import Review

class ReviewRepository(ABC):
    @abstractmethod
    def save_review(self, review: Review) -> None:
        pass

    @abstractmethod
    def get_review_by_id(self, review_id: str) -> Optional[Review]:
        pass

    @abstractmethod
    def get_all_reviews(self) -> List[Review]:
        pass

    @abstractmethod
    def get_flagged_reviews(self) -> List[Review]:
        pass

class InMemoryReviewRepository(ReviewRepository):
    def __init__(self):
        self._reviews: Dict[str, Review] = {}

    def save_review(self, review: Review) -> None:
        self._reviews[review.reviewId] = review
        print(f"Saved review: {review.reviewId}")

    def get_review_by_id(self, review_id: str) -> Optional[Review]:
        return self._reviews.get(review_id)

    def get_all_reviews(self) -> List[Review]:
        return list(self._reviews.values())

    def get_flagged_reviews(self) -> List[Review]:
        return [review for review in self._reviews.values() if review.abuseFlags]
