import unittest
from datetime import datetime, timedelta
from collections import deque # Added import for deque
# from detection_models.burst_detector import ProductBurstDetector # Keep commented for standalone test

# Minimal ProductBurstDetector for testing if not imported
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
        self_mock.review_history = deque()

    def _clean_old_reviews(self_mock, current_time: datetime):
        while self_mock.review_history and self_mock.review_history[0][0] < current_time - self_mock.long_window:
            self_mock.review_history.popleft()

    def add_review(self_mock, review_date: datetime, rating: int):
        self_mock.review_history.append((review_date, rating))
        self_mock._clean_old_reviews(review_date)

    def detect_burst(self_mock, current_time: datetime) -> dict | None:
        self_mock._clean_old_reviews(current_time)

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
        
        long_window_duration_hours = self_mock.long_window.total_seconds() / 3600
        if long_window_duration_hours == 0: long_window_duration_hours = 1

        avg_positive_rate_per_hour = long_window_positive_count / long_window_duration_hours
        avg_negative_rate_per_hour = long_window_negative_count / long_window_duration_hours

        short_window_duration_hours = self_mock.short_window.total_seconds() / 3600
        if short_window_duration_hours == 0: short_window_duration_hours = 1

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


class TestProductBurstDetector(unittest.TestCase):

    def test_add_review_and_clean_up(self):
        detector = ProductBurstDetector("P_TEST", short_window_minutes=10, long_window_hours=1)
        now = datetime.now()
        detector.add_review(now - timedelta(hours=2), 5) # Too old
        detector.add_review(now - timedelta(minutes=50), 4)
        detector.add_review(now - timedelta(minutes=5), 1)
        
        detector._clean_old_reviews(now) # Manually trigger clean up

        # Only reviews within long_window (1 hour) should remain
        self.assertEqual(len(detector.review_history), 2)
        self.assertEqual(detector.review_history[0][1], 4) # Check content

    def test_detect_positive_burst(self):
        detector = ProductBurstDetector("P_BURST_POS", short_window_minutes=5, long_window_hours=1,
                                        burst_threshold_multiplier=2.0, min_burst_count=5)
        now = datetime.now()

        # Establish a baseline (e.g., 10 positive reviews over 1 hour)
        for i in range(10):
            detector.add_review(now - timedelta(minutes=59 - i*5), 4) # Spread out
        
        # Add a burst of positive reviews in the short window (e.g., 6 reviews in 5 minutes)
        for i in range(6):
            detector.add_review(now - timedelta(minutes=i), 5)

        burst_alert = detector.detect_burst(now)
        self.assertIsNotNone(burst_alert)
        self.assertEqual(burst_alert['burst_type'], 'positive')
        self.assertGreaterEqual(burst_alert['current_positive_reviews_short_window'], 6)

    def test_detect_negative_burst(self):
        detector = ProductBurstDetector("P_BURST_NEG", short_window_minutes=5, long_window_hours=1,
                                        burst_threshold_multiplier=2.0, min_burst_count=5)
        now = datetime.now()

        # Establish a baseline
        for i in range(10):
            detector.add_review(now - timedelta(minutes=59 - i*5), 3)
        
        # Add a burst of negative reviews
        for i in range(6):
            detector.add_review(now - timedelta(minutes=i), 1)

        burst_alert = detector.detect_burst(now)
        self.assertIsNotNone(burst_alert)
        self.assertEqual(burst_alert['burst_type'], 'negative')
        self.assertGreaterEqual(burst_alert['current_negative_reviews_short_window'], 6)

    def test_no_burst_normal_activity(self):
        detector = ProductBurstDetector("P_NO_BURST", short_window_minutes=5, long_window_hours=1,
                                        burst_threshold_multiplier=2.0, min_burst_count=5)
        now = datetime.now()

        # Add regular reviews, no significant burst
        for i in range(20):
            detector.add_review(now - timedelta(minutes=i*2), 3) # Spread out 20 reviews over ~40 mins

        burst_alert = detector.detect_burst(now)
        self.assertIsNone(burst_alert)

    def test_below_min_burst_count(self):
        detector = ProductBurstDetector("P_LOW_COUNT", short_window_minutes=5, long_window_hours=1,
                                        burst_threshold_multiplier=2.0, min_burst_count=5)
        now = datetime.now()

        for i in range(10):
            detector.add_review(now - timedelta(minutes=59 - i*5), 3)

        # Add only 3 reviews in short window, below min_burst_count
        for i in range(3):
            detector.add_review(now - timedelta(minutes=i), 5)

        burst_alert = detector.detect_burst(now)
        self.assertIsNone(burst_alert)

if __name__ == '__main__':
    unittest.main()
