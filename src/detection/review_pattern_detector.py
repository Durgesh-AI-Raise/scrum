import time
from collections import defaultdict
from typing import List
from src.data_models.review_data_models import ProcessedReview

class ReviewPatternDetector:
    def __init__(self, burst_threshold: int = 10, burst_time_window_minutes: int = 60):
        """
        Initializes the ReviewPatternDetector.
        :param burst_threshold: Number of reviews within the time window to trigger a burst.
        :param burst_time_window_minutes: The time window in minutes for burst detection.
        """
        self.burst_threshold = burst_threshold
        self.burst_time_window_ms = burst_time_window_minutes * 60 * 1000 # Convert to milliseconds

    def _get_recent_reviews_for_product(self, product_id: str, current_time_ms: int) -> List[ProcessedReview]:
        """
        [PLACEHOLDER] Simulates fetching recent processed reviews for a product.
        In a real system, this would query the processed review data store (e.g., MongoDB, Cassandra).
        """
        # For this sprint, we'll return a dummy list.
        # In a real system, this would be a database call:
        # e.g., db.reviews.find({'product_id': product_id, 'timestamp': {'$gte': current_time_ms - self.burst_time_window_ms}})
        
        # Dummy data for demonstration
        if product_id == "new_product_XYZ":
            # Simulate a burst for a new product
            reviews = []
            for i in range(self.burst_threshold + 2): # Two more than threshold
                # Spread reviews within half the window to ensure they are recent
                review_timestamp = current_time_ms - (i * (self.burst_time_window_ms // (self.burst_threshold + 2)))
                reviews.append(ProcessedReview(
                    original_review_id=f"org_r{i}",
                    product_id=product_id,
                    reviewer_id=f"u{i}",
                    rating=5,
                    timestamp=review_timestamp,
                    cleaned_text="great product!"
                ))
            return reviews
        return []

    def detect_rapid_review_burst(self, product_id: str, current_review_timestamp: int) -> bool:
        """
        Detects if there's a rapid review burst for a given product.
        :param product_id: The ID of the product to check.
        :param current_review_timestamp: The timestamp of the review that triggered this check (in ms).
        :return: True if a burst is detected, False otherwise.
        """
        
        # Fetch reviews within the defined time window leading up to the current review
        # For simplicity, we'll assume _get_recent_reviews_for_product handles the time window
        # based on the current_review_timestamp and the configured window size.
        recent_reviews = self._get_recent_reviews_for_product(
            product_id, current_review_timestamp
        )

        five_star_reviews_in_window = [
            r for r in recent_reviews 
            if r.rating == 5 and 
            (current_review_timestamp - r.timestamp) <= self.burst_time_window_ms
        ]
        
        if len(five_star_reviews_in_window) >= self.burst_threshold:
            print(f"DEBUG: Detected {len(five_star_reviews_in_window)} 5-star reviews for product {product_id} in {self.burst_time_window_ms / 60000} minutes.")
            return True
        return False

# Example Usage (for testing)
if __name__ == "__main__":
    detector = ReviewPatternDetector(burst_threshold=5, burst_time_window_minutes=30)
    current_time = int(time.time() * 1000)

    # Simulate a product receiving many 5-star reviews in a short time
    is_burst = detector.detect_rapid_review_burst("new_product_XYZ", current_time)
    if is_burst:
        print("Rapid review burst detected for new_product_XYZ!")
    else:
        print("No rapid review burst detected for new_product_XYZ.")

    # Simulate a regular product
    is_burst_normal = detector.detect_rapid_review_burst("regular_product_ABC", current_time)
    if is_burst_normal:
        print("Rapid review burst detected for regular_product_ABC!")
    else:
        print("No rapid review burst detected for regular_product_ABC.")
