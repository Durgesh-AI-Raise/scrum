import unittest
from datetime import datetime, timedelta
from data_models import Review, FlaggedReview
from pattern_detector import ReviewPatternDetector
from flagged_review_storage import FlaggedReviewStorage

class TestReviewPatternDetector(unittest.TestCase):
    def test_no_burst(self):
        detector = ReviewPatternDetector(burst_time_window_hours=1, burst_threshold_reviews=5)
        reviews = [
            Review("r1", "p1", "u1", datetime(2023, 1, 1, 10, 0, 0), 5, "ok"),
            Review("r2", "p1", "u2", datetime(2023, 1, 1, 11, 30, 0), 4, "ok"),
            Review("r3", "p1", "u3", datetime(2023, 1, 1, 12, 0, 0), 3, "ok"),
        ]
        flagged = detector.detect_bursts(reviews)
        self.assertEqual(len(flagged), 0)

    def test_single_burst(self):
        detector = ReviewPatternDetector(burst_time_window_hours=1, burst_threshold_reviews=3)
        base_time = datetime(2023, 1, 1, 10, 0, 0)
        reviews = [
            Review("r1", "p1", "u1", base_time, 5, "good"),
            Review("r2", "p1", "u2", base_time + timedelta(minutes=10), 4, "good"),
            Review("r3", "p1", "u3", base_time + timedelta(minutes=20), 5, "good"),
            Review("r4", "p1", "u4", base_time + timedelta(minutes=70), 3, "late"), # outside 1 hour window
        ]
        flagged = detector.detect_bursts(reviews)
        self.assertEqual(len(flagged), 3) # r1, r2, r3 should be flagged
        for fr in flagged:
            self.assertEqual(fr.pattern_type, "Review Burst")
            self.assertEqual(fr.product_id, "p1")

    def test_multiple_bursts_same_product(self):
        detector = ReviewPatternDetector(burst_time_window_hours=1, burst_threshold_reviews=3)
        base_time = datetime(2023, 1, 1, 10, 0, 0)
        reviews = [
            # First burst
            Review("r1", "p2", "u1", base_time, 5, "a"),
            Review("r2", "p2", "u2", base_time + timedelta(minutes=10), 4, "b"),
            Review("r3", "p2", "u3", base_time + timedelta(minutes=20), 5, "c"),
            # Gap
            Review("r4", "p2", "u4", base_time + timedelta(hours=2), 3, "d"),
            # Second burst
            Review("r5", "p2", "u5", base_time + timedelta(hours=2, minutes=10), 5, "e"),
            Review("r6", "p2", "u6", base_time + timedelta(hours=2, minutes=20), 4, "f"),
        ]
        flagged = detector.detect_bursts(reviews)
        # r1, r2, r3 form a burst (3 reviews in 20 min)
        # r4 is outside. r5,r6 cannot form a burst of 3.
        # So expected 3 flagged reviews.
        self.assertEqual(len(flagged), 3)

    def test_burst_with_different_products(self):
        detector = ReviewPatternDetector(burst_time_window_hours=1, burst_threshold_reviews=2)
        base_time = datetime(2023, 1, 1, 10, 0, 0)
        reviews = [
            Review("r1", "pA", "u1", base_time, 5, "x"),
            Review("r2", "pA", "u2", base_time + timedelta(minutes=5), 4, "y"), # pA burst
            Review("r3", "pB", "u3", base_time + timedelta(minutes=10), 3, "z"),
            Review("r4", "pB", "u4", base_time + timedelta(minutes=15), 5, "w"), # pB burst
        ]
        flagged = detector.detect_bursts(reviews)
        self.assertEqual(len(flagged), 4) # r1,r2 and r3,r4 should be flagged
        product_ids = {fr.product_id for fr in flagged}
        self.assertIn("pA", product_ids)
        self.assertIn("pB", product_ids)


class TestFlaggedReviewStorage(unittest.TestCase):
    def test_save_and_retrieve(self):
        storage = FlaggedReviewStorage()
        fr1 = FlaggedReview("fr1", "prodX", "Review Burst", datetime.now(), "Test reason 1", {})
        fr2 = FlaggedReview("fr2", "prodY", "Review Burst", datetime.now(), "Test reason 2", {})

        storage.save_flagged_review(fr1)
        storage.save_flagged_review(fr2)

        retrieved = storage.get_all_flagged_reviews()
        self.assertEqual(len(retrieved), 2)
        self.assertIn(fr1, retrieved)
        self.assertIn(fr2, retrieved)

    def test_empty_storage(self):
        storage = FlaggedReviewStorage()
        retrieved = storage.get_all_flagged_reviews()
        self.assertEqual(len(retrieved), 0)

if __name__ == '__main__':
    unittest.main()
