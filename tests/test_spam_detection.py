import unittest
from datetime import datetime
from arg_spam_detection import detect_spam, SPAM_KEYWORDS, SPAM_REGEX_PATTERNS
from arg_api_service import check_review_for_spam_api
from arg_review_service import ingest_review, get_review_by_id
from arg_data_models import db_session, Review

class TestSpamDetection(unittest.TestCase):

    def setUp(self):
        # Clear the mock database before each test
        db_session.reviews = []
        db_session.reviewers = []

    def test_detect_spam_keywords(self):
        # Test cases for keyword detection
        review_text = f"This product offers {SPAM_KEYWORDS[0]}!"
        is_spam, reason = detect_spam(review_text)
        self.assertTrue(is_spam)
        self.assertIn(SPAM_KEYWORDS[0], reason)

        review_text = "A great product, highly recommend."
        is_spam, reason = detect_spam(review_text)
        self.assertFalse(is_spam)
        self.assertEqual(reason, "No spam detected.")

    def test_detect_spam_regex(self):
        # Test cases for regex pattern detection
        review_text = f"Visit our site at https://example.com"
        is_spam, reason = detect_spam(review_text)
        self.assertTrue(is_spam)
        self.assertIn("Pattern", reason)

        review_text = "Contact us via whatsapp 1234567890"
        is_spam, reason = detect_spam(review_text)
        self.assertTrue(is_spam)
        self.assertIn("Pattern", reason)

        review_text = "Email us at test@example.com for details."
        is_spam, reason = detect_spam(review_text)
        self.assertTrue(is_spam)
        self.assertIn("Pattern", reason)

    def test_check_review_for_spam_api_spam(self):
        review_id = "R001"
        reviewer_id = "U001"
        product_id = "P001"
        review_text_spam = "This is a great product. Get free money now!"
        review_date = datetime.now()
        rating = 5

        ingest_review(review_id, reviewer_id, product_id, review_text_spam, review_date, rating)
        result = check_review_for_spam_api(review_id, review_text_spam)

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["is_spam"])
        self.assertIn("free money", result["detection_reason"])

        # Verify the flag in the database
        retrieved_review = get_review_by_id(review_id)
        self.assertTrue(retrieved_review.spam_flag)
        self.assertIn("free money", retrieved_review.detection_reason)

    def test_check_review_for_spam_api_no_spam(self):
        review_id = "R002"
        reviewer_id = "U002"
        product_id = "P002"
        review_text_clean = "This is a fantastic product, very happy with my purchase."
        review_date = datetime.now()
        rating = 4

        ingest_review(review_id, reviewer_id, product_id, review_text_clean, review_date, rating)
        result = check_review_for_spam_api(review_id, review_text_clean)

        self.assertEqual(result["status"], "success")
        self.assertFalse(result["is_spam"])
        self.assertEqual(result["detection_reason"], "No spam detected.")

        # Verify the flag in the database
        retrieved_review = get_review_by_id(review_id)
        self.assertFalse(retrieved_review.spam_flag)
        self.assertEqual(retrieved_review.detection_reason, "No spam detected.")

    def test_check_review_for_spam_api_review_not_found(self):
        review_id = "R999" # Non-existent review
        review_text = "Some text."
        result = check_review_for_spam_api(review_id, review_text)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Review not found.")

if __name__ == '__main__':
    unittest.main()