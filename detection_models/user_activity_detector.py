from datetime import datetime, timedelta
from collections import deque

class UserActivityDetector:
    def __init__(self_mock, user_id: str,
                 new_account_window_days: int = 7, # How long an account is considered "new"
                 activity_check_window_hours: int = 24, # Window for checking unusual activity
                 review_count_threshold: int = 10, # Max reviews in activity_check_window
                 distinct_product_threshold: int = 5): # Max distinct products in activity_check_window
        self_mock.user_id = user_id
        self_mock.new_account_window = timedelta(days=new_account_window_days)
        self_mock.activity_check_window = timedelta(hours=activity_check_window_hours)
        self_mock.review_count_threshold = review_count_threshold
        self_mock.distinct_product_threshold = distinct_product_threshold

        self_mock.first_review_date: datetime | None = None
        # Stores (review_date, product_id) for reviews within the new_account_window
        self_mock.all_reviews_in_new_account_period = deque()

    def _clean_old_activity(self_mock, current_time: datetime):
        """Cleans up reviews older than the overall new_account_window."""
        while self_mock.all_reviews_in_new_account_period and \
              self_mock.all_reviews_in_new_account_period[0][0] < current_time - self_mock.new_account_window:
            self_mock.all_reviews_in_new_account_period.popleft()

    def add_review(self_mock, review_date: datetime, product_id: str):
        """Adds a new review for the user."""
        if self_mock.first_review_date is None:
            self_mock.first_review_date = review_date
        
        self_mock.all_reviews_in_new_account_period.append((review_date, product_id))
        self_mock._clean_old_activity(review_date) # Keep deque relevant

    def is_new_account_active(self_mock, current_time: datetime) -> bool:
        """Checks if the user is a new account and still within its activity window."""
        if self_mock.first_review_date is None:
            return False # No reviews yet for this user
        return (current_time - self_mock.first_review_date) <= self_mock.new_account_window

    def detect_unusual_activity(self_mock, current_time: datetime) -> dict | None:
        """
        Detects if a new account exhibits unusual review posting activity.
        Returns a dictionary with activity details if detected, otherwise None.
        """
        if not self_mock.is_new_account_active(current_time):
            return None # Only check new, active accounts

        reviews_in_check_window = []
        distinct_products_in_check_window = set()

        for r_date, p_id in self_mock.all_reviews_in_new_account_period:
            if current_time - r_date <= self_mock.activity_check_window:
                reviews_in_check_window.append((r_date, p_id))
                distinct_products_in_check_window.add(p_id)
        
        current_review_count = len(reviews_in_check_window)
        current_distinct_products = len(distinct_products_in_check_window)

        is_high_review_count = current_review_count >= self_mock.review_count_threshold
        is_high_distinct_products = current_distinct_products >= self_mock.distinct_product_threshold

        if is_high_review_count or is_high_distinct_products:
            return {
                "user_id": self_mock.user_id,
                "flag_timestamp": current_time,
                "flag_reason": "New account with unusual activity detected.",
                "first_review_date": self_mock.first_review_date,
                "review_count_in_window": current_review_count,
                "distinct_products_in_window": current_distinct_products,
                "threshold_review_count": self_mock.review_count_threshold,
                "threshold_distinct_products": self_mock.distinct_product_threshold
            }
        return None
