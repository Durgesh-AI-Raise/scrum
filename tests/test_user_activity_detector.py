import unittest
from datetime import datetime, timedelta
from collections import deque # Added for deque

# Minimal UserActivityDetector for testing if not imported
class UserActivityDetector:
    def __init__(self_mock, user_id: str,
                 new_account_window_days: int = 7,
                 activity_check_window_hours: int = 24,
                 review_count_threshold: int = 10,
                 distinct_product_threshold: int = 5):
        self_mock.user_id = user_id
        self_mock.new_account_window = timedelta(days=new_account_window_days)
        self_mock.activity_check_window = timedelta(hours=activity_check_window_hours)
        self_mock.review_count_threshold = review_count_threshold
        self_mock.distinct_product_threshold = distinct_product_threshold
        self_mock.first_review_date: datetime | None = None
        self_mock.all_reviews_in_new_account_period = deque()

    def _clean_old_activity(self_mock, current_time: datetime):
        while self_mock.all_reviews_in_new_account_period and \
              self_mock.all_reviews_in_new_account_period[0][0] < current_time - self_mock.new_account_window:
            self_mock.all_reviews_in_new_account_period.popleft()

    def add_review(self_mock, review_date: datetime, product_id: str):
        if self_mock.first_review_date is None:
            self_mock.first_review_date = review_date
        self_mock.all_reviews_in_new_account_period.append((review_date, product_id))
        self_mock._clean_old_activity(review_date)

    def is_new_account_active(self_mock, current_time: datetime) -> bool:
        if self_mock.first_review_date is None:
            return False
        return (current_time - self_mock.first_review_date) <= self_mock.new_account_window

    def detect_unusual_activity(self_mock, current_time: datetime) -> dict | None:
        if not self_mock.is_new_account_active(current_time):
            return None

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


class TestUserActivityDetector(unittest.TestCase):

    def test_is_new_account_active_logic(self):
        detector = UserActivityDetector("U_NEW_ACC", new_account_window_days=7)
        now = datetime.now()

        # First review makes it new
        detector.add_review(now - timedelta(days=2), "P_A")
        self.assertTrue(detector.is_new_account_active(now))

        # After window, no longer new
        detector.first_review_date = now - timedelta(days=8)
        self.assertFalse(detector.is_new_account_active(now))

    def test_detect_unusual_activity_high_review_count(self):
        detector = UserActivityDetector("U_HIGH_REVIEWS", new_account_window_days=7,
                                        activity_check_window_hours=24,
                                        review_count_threshold=5, distinct_product_threshold=1)
        now = datetime.now()
        detector.add_review(now - timedelta(days=0, hours=23), "P_X") # First review establishes new account
        
        # Add reviews to exceed count threshold within 24 hours
        for i in range(5):
            detector.add_review(now - timedelta(hours=i), f"P_X") # 5 reviews for same product

        alert = detector.detect_unusual_activity(now)
        self.assertIsNotNone(alert)
        self.assertTrue(alert['review_count_in_window'] >= detector.review_count_threshold)
        self.assertEqual(alert['distinct_products_in_window'], 1)

    def test_detect_unusual_activity_high_distinct_products(self):
        detector = UserActivityDetector("U_HIGH_PRODUCTS", new_account_window_days=7,
                                        activity_check_window_hours=24,
                                        review_count_threshold=1, distinct_product_threshold=3)
        now = datetime.now()
        detector.add_review(now - timedelta(days=0, hours=23), "P_A") # First review
        detector.add_review(now - timedelta(hours=22), "P_B")
        detector.add_review(now - timedelta(hours=21), "P_C") # 3rd distinct product
        detector.add_review(now - timedelta(hours=20), "P_A") # Another for P_A, but not new distinct

        alert = detector.detect_unusual_activity(now)
        self.assertIsNotNone(alert)
        self.assertTrue(alert['distinct_products_in_window'] >= detector.distinct_product_threshold)
        self.assertEqual(alert['review_count_in_window'], 4)

    def test_no_unusual_activity(self):
        detector = UserActivityDetector("U_NORMAL", new_account_window_days=7,
                                        activity_check_window_hours=24,
                                        review_count_threshold=10, distinct_product_threshold=5)
        now = datetime.now()
        detector.add_review(now - timedelta(days=2), "P_1") # New account
        detector.add_review(now - timedelta(days=1), "P_2") # 2 reviews, 2 distinct products

        alert = detector.detect_unusual_activity(now)
        self.assertIsNone(alert)

    def test_account_too_old(self):
        detector = UserActivityDetector("U_OLD", new_account_window_days=7,
                                        activity_check_window_hours=24,
                                        review_count_threshold=10, distinct_product_threshold=5)
        now = datetime.now()
        detector.add_review(now - timedelta(days=8), "P_OLD") # First review outside new account window
        detector.add_review(now - timedelta(hours=1), "P_OLD_RECENT") # Recent review, but user not new
        
        alert = detector.detect_unusual_activity(now)
        self.assertIsNone(alert)

if __name__ == '__main__':
    unittest.main()
