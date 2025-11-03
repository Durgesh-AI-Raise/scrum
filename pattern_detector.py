from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict
from data_models import Review, FlaggedReview

class ReviewPatternDetector:
    """
    Detects suspicious review patterns, specifically "Review Bursts".
    """
    def __init__(self, burst_time_window_hours: int = 2, burst_threshold_reviews: int = 10):
        self.burst_time_window_hours = burst_time_window_hours
        self.burst_threshold_reviews = burst_threshold_reviews

    def detect_bursts(self, reviews: List[Review]) -> List[FlaggedReview]:
        flagged_reviews: List[FlaggedReview] = []
        reviews_by_product: Dict[str, List[Review]] = defaultdict(list)

        # Group reviews by product and sort by timestamp
        for review in reviews:
            reviews_by_product[review.product_id].append(review)

        for product_id, product_reviews in reviews_by_product.items():
            product_reviews.sort(key=lambda r: r.timestamp) # Sort by timestamp

            # Use a sliding window to detect bursts
            left = 0
            for right in range(len(product_reviews)):
                current_review = product_reviews[right]
                window_end_time = current_review.timestamp
                window_start_time = window_end_time - timedelta(hours=self.burst_time_window_hours)

                # Shrink window from left until reviews are within the time window
                while product_reviews[left].timestamp < window_start_time:
                    left += 1

                # Check for burst condition
                reviews_in_window = right - left + 1
                if reviews_in_window >= self.burst_threshold_reviews:
                    # Flag all reviews in this burst window. Avoid duplicate flagging if already flagged.
                    for i in range(left, right + 1):
                        review_to_flag = product_reviews[i]
                        # Only flag if not already flagged in this run
                        if not any(fr.review_id == review_to_flag.review_id for fr in flagged_reviews):
                            flagged_reviews.append(
                                FlaggedReview(
                                    review_id=review_to_flag.review_id,
                                    product_id=product_id,
                                    pattern_type="Review Burst",
                                    detection_timestamp=datetime.now(),
                                    reason=f"Detected {reviews_in_window} reviews in {self.burst_time_window_hours} hours for product {product_id}.",
                                    details={
                                        "burst_start_time": product_reviews[left].timestamp,
                                        "burst_end_time": product_reviews[right].timestamp,
                                        "review_count_in_burst": reviews_in_window
                                    }
                                )
                            )
        return flagged_reviews
