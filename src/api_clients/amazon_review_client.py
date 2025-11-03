from datetime import datetime, timedelta
from typing import List, Optional
from src.data_models.review_model import Review, ReviewMetadata

class AmazonReviewAPIClient:
    def __init__(self):
        self._reviews_data = self._generate_mock_reviews()
        self._current_index = 0

    def _generate_mock_reviews(self) -> List[Review]:
        # Generate some synthetic review data
        reviews = []
        for i in range(1, 11): # Generate 10 mock reviews
            review_id = f"R_mock_{i}"
            product_id = f"P_mock_prod_A" if i % 2 == 0 else f"P_mock_prod_B"
            reviewer_id = f"U_mock_user_{i}"
            review_text = f"This is a mock review number {i}. It's a great product!"
            if i % 3 == 0:
                review_text = f"This is a mock review number {i}. free gift discount code." # Simulate suspicious keyword
            if i == 5 or i == 6: # Simulate identical reviews
                review_text = "This product is absolutely wonderful. Highly recommend!"

            rating = (i % 5) + 1
            timestamp = datetime.utcnow() - timedelta(hours=i)
            reviews.append(
                Review(
                    reviewId=review_id,
                    productId=product_id,
                    reviewerId=reviewer_id,
                    reviewText=review_text,
                    rating=rating,
                    timestamp=timestamp,
                    reviewTitle=f"Mock Title {i}",
                    isVerifiedPurchase=True
                )
            )
        return reviews

    def get_reviews(self, batch_size: int = 5) -> List[Review]:
        """
        Simulates fetching a batch of reviews from Amazon.
        For this mock, it returns a fixed set of generated reviews.
        In a real scenario, this would involve API calls and pagination logic.
        """
        if self._current_index >= len(self._reviews_data):
            return [] # No more mock reviews

        batch = self._reviews_data[self._current_index : self._current_index + batch_size]
        self._current_index += batch_size
        return batch

# Example Usage:
# client = AmazonReviewAPIClient()
# reviews = client.get_reviews()
# for review in reviews:
#     print(f"Review ID: {review.reviewId}, Text: {review.reviewText}")
