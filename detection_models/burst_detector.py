from collections import deque
from datetime import datetime, timedelta

class ProductBurstDetector:
    def __init__(self_mock, product_id: str,
                 short_window_minutes: int = 60, # e.g., 1 hour
                 long_window_hours: int = 24, # e.g., 24 hours for baseline
                 burst_threshold_multiplier: float = 3.0, # e.g., 3x the average
                 min_burst_count: int = 10): # Minimum reviews to consider a burst
        self_mock.product_id = product_id
        self_mock.short_window = timedelta(minutes=short_window_minutes)
        self_mock.long_window = timedelta(hours=long_window_hours)
        self_mock.burst_threshold_multiplier = burst_threshold_multiplier
        self_mock.min_burst_count = min_burst_count

        # Stores (timestamp, rating) for reviews within the long_window
        self_mock.review_history = deque()

    def _clean_old_reviews(self_mock, current_time: datetime):
        """Removes reviews older than the long_window."""
        while self_mock.review_history and self_mock.review_history[0][0] < current_time - self_mock.long_window:
            self_mock.review_history.popleft()

    def add_review(self_mock, review_date: datetime, rating: int):
        """Adds a new review to the product's history."""
        self_mock.review_history.append((review_date, rating))
        self_mock._clean_old_reviews(review_date) # Clean up on adding to keep deque size manageable

    def detect_burst(self_mock, current_time: datetime) -> dict | None:
        """
        Detects if there's a sudden burst of positive or negative reviews.
        Returns a dictionary with burst details if detected, otherwise None.
        """
        self_mock._clean_old_reviews(current_time) # Ensure history is up-to-date

        short_window_positive_count = 0
        short_window_negative_count = 0
        
        long_window_positive_count = 0
        long_window_negative_count = 0

        for r_date, r_rating in self_mock.review_history:
            if current_time - r_date <= self_mock.long_window:
                if r_rating >= 4: long_window_positive_count += 1
                if r_rating <= 2: long_window_negative_count += 1
            
            if current_time - r_date <= self_mock.short_window:
                if r_rating >= 4: short_window_positive_count += 1
                if r_rating <= 2: short_window_negative_count += 1
        
        # Calculate average rates over the long window
        # Avoid division by zero if long_window has no reviews
        long_window_duration_hours = self_mock.long_window.total_seconds() / 3600
        if long_window_duration_hours == 0: long_window_duration_hours = 1 # Prevent ZeroDivisionError

        avg_positive_rate_per_hour = long_window_positive_count / long_window_duration_hours
        avg_negative_rate_per_hour = long_window_negative_count / long_window_duration_hours

        # Scale short window counts to hourly rate for comparison
        short_window_duration_hours = self_mock.short_window.total_seconds() / 3600
        if short_window_duration_hours == 0: short_window_duration_hours = 1 # Prevent ZeroDivisionError

        current_positive_rate_per_hour = short_window_positive_count / short_window_duration_hours
        current_negative_rate_per_hour = short_window_negative_count / short_window_duration_hours

        is_positive_burst = False
        is_negative_burst = False

        if short_window_positive_count >= self_mock.min_burst_count and \
           current_positive_rate_per_hour > avg_positive_rate_per_hour * self_mock.burst_threshold_multiplier:
            is_positive_burst = True

        if short_window_negative_count >= self_mock.min_burst_count and \
           current_negative_rate_per_hour > avg_negative_rate_per_hour * self_mock.burst_threshold_multiplier:
            is_negative_burst = True

        if is_positive_burst or is_negative_burst:
            burst_type = ""
            if is_positive_burst and is_negative_burst: burst_type = "mixed"
            elif is_positive_burst: burst_type = "positive"
            else: burst_type = "negative"

            return {
                "product_id": self_mock.product_id,
                "flag_timestamp": current_time,
                "burst_type": burst_type,
                "current_positive_reviews_short_window": short_window_positive_count,
                "current_negative_reviews_short_window": short_window_negative_count,
                "avg_positive_rate_long_window_per_hour": avg_positive_rate_per_hour,
                "avg_negative_rate_long_window_per_hour": avg_negative_rate_per_hour,
                "flag_reason": "Sudden burst of reviews detected."
            }
        return None
