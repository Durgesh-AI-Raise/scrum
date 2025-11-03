from typing import List, Tuple, Optional

from src.data_models.review_model import Review
from src.detection.rules_engine import Rule
from src.repositories.review_repository import ReviewRepository

class IdenticalReviewRule(Rule):
    def __init__(
        self, 
        review_repository: ReviewRepository,
        rule_id: str = "IDENTICAL_REVIEW_RULE", 
        description: str = "Detects identical review text submitted by different accounts."
    ):
        super().__init__(rule_id, description)
        self.review_repository = review_repository

    def _normalize_review_text(self, text: str) -> str:
        """Normalizes review text for comparison (lowercase, strip whitespace)."""
        return text.strip().lower()

    def evaluate(self, review: Review) -> Tuple[bool, Optional[str]]:
        normalized_current_review_text = self._normalize_review_text(review.reviewText)
        
        # Retrieve all existing reviews from the repository for comparison
        # NOTE: For a real-world system, this would need to be optimized
        # (e.g., using a dedicated text index, pre-calculated hashes, or database-level checks).
        existing_reviews = self.review_repository.get_all_reviews()

        for existing_review in existing_reviews:
            # Skip comparing the review with itself
            if existing_review.reviewId == review.reviewId:
                continue

            normalized_existing_review_text = self._normalize_review_text(existing_review.reviewText)

            if (
                normalized_current_review_text == normalized_existing_review_text and
                existing_review.reviewerId != review.reviewerId
            ):
                # Found an identical review from a different reviewer
                reason = (
                    f"Identical review text found (Review ID: {existing_review.reviewId}) "
                    f"from a different reviewer (Reviewer ID: {existing_review.reviewerId})."
                )
                review.detectionResults.identicalReview = True
                return True, reason
        
        return False, None

# Example Usage (for testing purposes, not part of the deployed code directly)
# if __name__ == "__main__":
#     from datetime import datetime
#     from src.data_models.review_model import Review
#     from src.repositories.review_repository import InMemoryReviewRepository
#
#     repo = InMemoryReviewRepository()
#     rule = IdenticalReviewRule(repo)
#
#     # Add some reviews to the repository
#     review_a = Review(
#         reviewId="R_dup_01", productId="P_dup", reviewerId="U_dup_A",
#         reviewText="This is a duplicate review example!", rating=5, timestamp=datetime.utcnow()
#     )
#     review_b = Review(
#         reviewId="R_dup_02", productId="P_dup", reviewerId="U_dup_B",
#         reviewText="This is a duplicate review example!", rating=5, timestamp=datetime.utcnow()
#     )
#     review_c = Review(
#         reviewId="R_unique_01", productId="P_unique", reviewerId="U_unique_C",
#         reviewText="This is a unique review.", rating=4, timestamp=datetime.utcnow()
#     )
#     review_d = Review(
#         reviewId="R_dup_03", productId="P_dup", reviewerId="U_dup_A", # Same reviewer as review_a
#         reviewText="This is a duplicate review example!", rating=5, timestamp=datetime.utcnow()
#     )
#     review_e = Review(
#         reviewId="R_dup_04", productId="P_dup", reviewerId="U_dup_C", # Different reviewer
#         reviewText="  this is a duplicate review EXAMPLE!  ", rating=5, timestamp=datetime.utcnow() # Normalized text matches
#     )
#
#     repo.save_review(review_a)
#     repo.save_review(review_c)
#
#     # Test case 1: Identical review from different account
#     triggered, reason = rule.evaluate(review_b)
#     print(f"Review B Triggered: {triggered}, Reason: {reason}, DetectionResults: {review_b.detectionResults.identicalReview}")
#     assert triggered is True
#     assert review_b.detectionResults.identicalReview is True
#
#     # Test case 2: Unique review
#     triggered, reason = rule.evaluate(review_c)
#     print(f"Review C Triggered: {triggered}, Reason: {reason}, DetectionResults: {review_c.detectionResults.identicalReview}")
#     assert triggered is False
#     assert review_c.detectionResults.identicalReview is False
#
#     # Test case 3: Identical review from SAME account (should NOT trigger this rule)
#     triggered, reason = rule.evaluate(review_d)
#     print(f"Review D Triggered: {triggered}, Reason: {reason}, DetectionResults: {review_d.detectionResults.identicalReview}")
#     assert triggered is False
#     assert review_d.detectionResults.identicalReview is False
#
#     # Add review_b to repo for further testing
#     repo.save_review(review_b)
#
#     # Test case 4: Identical review from a new, different account with normalized text
#     triggered, reason = rule.evaluate(review_e)
#     print(f"Review E Triggered: {triggered}, Reason: {reason}, DetectionResults: {review_e.detectionResults.identicalReview}")
#     assert triggered is True
#     assert review_e.detectionResults.identicalReview is True
