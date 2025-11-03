import unittest
from unittest.mock import Mock
from datetime import datetime, timedelta

# Assuming the service is located at abuse_detection.services.suspicious_account_service
# You might need to adjust the import path based on your project structure
from src.abuse_detection.services.suspicious_account_service import SuspiciousAccountDetectionService

class TestSuspiciousAccountDetectionService(unittest.TestCase):

    def setUp(self):
        # Mock repositories
        self.mock_account_repo = Mock()
        self.mock_review_repo = Mock()
        self.service = SuspiciousAccountDetectionService(self.mock_account_repo, self.mock_review_repo)

    def test_new_account_high_volume_reviews(self):
        # Setup mock data for a new account with many reviews
        self.mock_account_repo.get_account.return_value = {"creation_date": datetime.now() - timedelta(days=2)}
        self.mock_review_repo.get_reviews_by_account.return_value = [
            {"rating": 5, "timestamp": datetime.now() - timedelta(hours=1), "product_id": "P1", "product_category": "Electronics"},
            {"rating": 5, "timestamp": datetime.now() - timedelta(hours=2), "product_id": "P2", "product_category": "Books"},
            {"rating": 5, "timestamp": datetime.now() - timedelta(hours=3), "product_id": "P3", "product_category": "Clothing"},
            {"rating": 5, "timestamp": datetime.now() - timedelta(hours=4), "product_id": "P4", "product_category": "Food"},
            {"rating": 5, "timestamp": datetime.now() - timedelta(hours=5), "product_id": "P5", "product_category": "Toys"},
        ]
        result = self.service.detect_suspicion("new_suspicious_account")
        self.assertTrue(result["is_suspicious"])
        self.assertIn("Account is new", result["reasons"])
        self.assertIn("High review volume", result["reasons"])
        self.assertEqual(result["confidence_score"], "High")

    def test_only_five_star_diverse_products(self):
        # Setup mock data for an account with only 5-star reviews across diverse products
        self.mock_account_repo.get_account.return_value = {"creation_date": datetime.now() - timedelta(days=100)} # Not new
        self.mock_review_repo.get_reviews_by_account.return_value = [
            {"rating": 5, "timestamp": datetime.now() - timedelta(days=10), "product_id": "P1", "product_category": "Electronics"},
            {"rating": 5, "timestamp": datetime.now() - timedelta(days=20), "product_id": "P2", "product_category": "Books"},
            {"rating": 5, "timestamp": datetime.now() - timedelta(days=30), "product_id": "P3", "product_category": "Clothing"},
        ]
        result = self.service.detect_suspicion("five_star_diverse_account")
        self.assertTrue(result["is_suspicious"])
        self.assertIn("Account has only 5-star reviews across 3 diverse product categories.", result["reasons"])
        self.assertEqual(result["confidence_score"], "Medium")

    def test_only_one_star_reviews(self):
        # Setup mock data for an account with only 1-star reviews
        self.mock_account_repo.get_account.return_value = {"creation_date": datetime.now() - timedelta(days=50)}
        self.mock_review_repo.get_reviews_by_account.return_value = [
            {"rating": 1, "timestamp": datetime.now() - timedelta(days=5), "product_id": "CompA", "product_category": "Electronics"},
            {"rating": 1, "timestamp": datetime.now() - timedelta(days=6), "product_id": "CompB", "product_category": "Electronics"},
        ]
        result = self.service.detect_suspicion("one_star_account")
        self.assertTrue(result["is_suspicious"])
        self.assertIn("Account has only 1-star reviews (2 reviews) suggesting targeted negative campaigning.", result["reasons"])
        self.assertEqual(result["confidence_score"], "Medium")

    def test_legitimate_account(self):
        # Setup mock data for a legitimate account
        self.mock_account_repo.get_account.return_value = {"creation_date": datetime.now() - timedelta(days=200)}
        self.mock_review_repo.get_reviews_by_account.return_value = [
            {"rating": 4, "timestamp": datetime.now() - timedelta(days=10), "product_id": "P1", "product_category": "Electronics"},
            {"rating": 5, "timestamp": datetime.now() - timedelta(days=20), "product_id": "P2", "product_category": "Books"},
            {"rating": 3, "timestamp": datetime.now() - timedelta(days=30), "product_id": "P3", "product_category": "Clothing"},
        ]
        result = self.service.detect_suspicion("legit_account")
        self.assertFalse(result["is_suspicious"])
        self.assertEqual(result["reasons"], [])
        self.assertEqual(result["confidence_score"], "Low")

    def test_non_existent_account(self):
        # Setup mock data for a non-existent account
        self.mock_account_repo.get_account.return_value = None
        result = self.service.detect_suspicion("non_existent_account")
        self.assertFalse(result["is_suspicious"])
        self.assertEqual(result["reasons"], ["Account not found"])
        self.assertEqual(result["confidence_score"], "Low")

    def test_combination_of_heuristics(self):
        # New account with both high volume and only 5-star diverse
        self.mock_account_repo.get_account.return_value = {"creation_date": datetime.now() - timedelta(days=3)} # New
        self.mock_review_repo.get_reviews_by_account.return_value = [
            {"rating": 5, "timestamp": datetime.now() - timedelta(hours=1), "product_id": "P1", "product_category": "Electronics"},
            {"rating": 5, "timestamp": datetime.now() - timedelta(hours=2), "product_id": "P2", "product_category": "Books"},
            {"rating": 5, "timestamp": datetime.now() - timedelta(hours=3), "product_id": "P3", "product_category": "Clothing"},
            {"rating": 5, "timestamp": datetime.now() - timedelta(hours=4), "product_id": "P4", "product_category": "Food"},
            {"rating": 5, "timestamp": datetime.now() - timedelta(hours=5), "product_id": "P5", "product_category": "Toys"},
            {"rating": 5, "timestamp": datetime.now() - timedelta(days=1), "product_id": "P6", "product_category": "Gadgets"},
            {"rating": 5, "timestamp": datetime.now() - timedelta(days=2), "product_id": "P7", "product_category": "Home Decor"},
        ]
        result = self.service.detect_suspicion("combined_suspicion_account")
        self.assertTrue(result["is_suspicious"])
        self.assertIn("Account is new", result["reasons"])
        self.assertIn("High review volume", result["reasons"])
        self.assertIn("Account has only 5-star reviews across", result["reasons"])
        self.assertEqual(result["confidence_score"], "High") # At least two reasons
