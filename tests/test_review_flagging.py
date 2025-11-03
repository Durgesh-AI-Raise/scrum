import unittest
from unittest.mock import patch
from services.detection.review_flagging_service import ReviewFlaggingService
from datetime import datetime

class TestReviewFlaggingService(unittest.TestCase):

    @patch('services.data_ingestion.mock_db.mock_db')
    def setUp(self, mock_db):
        self.service = ReviewFlaggingService()
        self.mock_db = mock_db # Store the mock for assertions

    def test_short_5_star_review(self):
        review = {
            "review_id": "R_SHORT_5",
            "product_id": "P1",
            "reviewer_id": "U1",
            "rating": 5,
            "review_title": "Great!",
            "review_content": "Love it.",
            "review_date": datetime(2023, 1, 1, 10, 0, 0),
            "source_url": "http://example.com/R_SHORT_5"
        }
        self.assertTrue(self.service.flag_review(review))
        self.mock_db.add_flagged_review.assert_called_once()
        flagged_data = self.mock_db.add_flagged_review.call_args[0][0]
        self.assertEqual(flagged_data['review_id'], "R_SHORT_5")
        self.assertIn("short_5_star_review", flagged_data['flag_reason'])

    def test_keyword_stuffing_review(self):
        review = {
            "review_id": "R_KEYWORD",
            "product_id": "P2",
            "reviewer_id": "U2",
            "rating": 3,
            "review_title": "Okay product",
            "review_content": "This product is okay, buy now while stocks last!",
            "review_date": datetime(2023, 1, 2, 11, 0, 0),
            "source_url": "http://example.com/R_KEYWORD"
        }
        self.assertTrue(self.service.flag_review(review))
        self.mock_db.add_flagged_review.assert_called_once()
        flagged_data = self.mock_db.add_flagged_review.call_args[0][0]
        self.assertEqual(flagged_data['review_id'], "R_KEYWORD")
        self.assertIn("keyword_stuffing: buy now", flagged_data['flag_reason'])

    def test_normal_review(self):
        review = {
            "review_id": "R_NORMAL",
            "product_id": "P3",
            "reviewer_id": "U3",
            "rating": 4,
            "review_title": "Good product",
            "review_content": "This is a good product, I'd recommend it to others.",
            "review_date": datetime(2023, 1, 3, 12, 0, 0),
            "source_url": "http://example.com/R_NORMAL"
        }
        self.assertFalse(self.service.flag_review(review))
        self.mock_db.add_flagged_review.assert_not_called()

    def test_long_5_star_review(self):
        review = {
            "review_id": "R_LONG_5",
            "product_id": "P4",
            "reviewer_id": "U4",
            "rating": 5,
            "review_title": "Fantastic Experience!",
            "review_content": "I had a fantastic experience with this product. It exceeded all my expectations.",
            "review_date": datetime(2023, 1, 4, 13, 0, 0),
            "source_url": "http://example.com/R_LONG_5"
        }
        self.assertFalse(self.service.flag_review(review))
        self.mock_db.add_flagged_review.assert_not_called()

if __name__ == '__main__':
    unittest.main()