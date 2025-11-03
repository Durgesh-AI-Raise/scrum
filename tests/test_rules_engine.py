import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
import json
import os

# Adjust import path as necessary based on project structure
from src.review_ingestion_service import RulesEngine

class TestRulesEngine(unittest.TestCase):

    def setUp(self):
        # Create a dummy rules.json for testing
        self.test_rules_path = "tests/test_rules.json"
        self.dummy_rules = [
            {
                "rule_id": "velocity_spike_1",
                "description": "Reviews from new accounts for a single product with high velocity.",
                "conditions": {
                    "account_age": {"operator": "<", "value": "7 days"},
                    "review_velocity_per_product": {"operator": ">", "value": "10/hour"}
                },
                "severity": "HIGH",
                "flag_reason": "Suspicious review velocity for new accounts."
            },
            {
                "rule_id": "identical_content_1",
                "description": "Identical review content across multiple reviews.",
                "conditions": {
                    "review_content": {"operator": "duplicates_across_products", "threshold": 3}
                },
                "severity": "MEDIUM",
                "flag_reason": "Identical review content found across multiple reviews."
            },
            {
                "rule_id": "low_rating_new_product",
                "description": "Low rating reviews on newly launched products from new accounts.",
                "conditions": {
                    "product_launch_age": {"operator": "<", "value": "30 days"},
                    "account_age": {"operator": "<", "value": "14 days"},
                    "rating": {"operator": "<=", "value": 2}
                },
                "severity": "MEDIUM",
                "flag_reason": "Low rating from new account on new product."
            }
        ]
        os.makedirs(os.path.dirname(self.test_rules_path), exist_ok=True)
        with open(self.test_rules_path, 'w') as f:
            json.dump(self.dummy_rules, f)
        self.rules_engine = RulesEngine(rules_config_path=self.test_rules_path)

    def tearDown(self):
        # Clean up the dummy rules.json
        if os.path.exists(self.test_rules_path):
            os.remove(self.test_rules_path)

    @patch('src.review_ingestion_service.datetime')
    def test_velocity_spike_rule(self, mock_datetime):
        # Mock datetime.now() for consistent testing
        mock_now = datetime(2023, 10, 27, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw) # Ensure datetime constructor works
        mock_datetime.timedelta = timedelta # Ensure timedelta works

        # Review data that should trigger velocity_spike_1
        review_data = {
            'review_id': 'R1',
            'product_id': 'P1',
            'user_id': 'U1',
            'rating': 5,
            'review_content': 'Good product!',
            'review_timestamp': datetime(2023, 10, 20, 9, 0, 0), # Old review, but account age matters
            'account_age': datetime(2023, 10, 25, 0, 0, 0), # Account created 2 days ago
            'review_velocity_per_product': 12, # 12 reviews/hour
            'current_time': mock_now # Pass current_time for calculation
        }
        result = self.rules_engine.apply_rules(review_data)
        self.assertIsNotNone(result)
        self.assertEqual(result['severity'], 'HIGH')
        self.assertEqual(len(result['reasons']), 1)
        self.assertEqual(result['reasons'][0]['rule_id'], 'velocity_spike_1')

    @patch('src.review_ingestion_service.datetime')
    def test_velocity_spike_rule_not_triggered(self, mock_datetime):
        mock_now = datetime(2023, 10, 27, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        mock_datetime.timedelta = timedelta

        # Review data that should NOT trigger velocity_spike_1 (account too old)
        review_data = {
            'review_id': 'R2',
            'product_id': 'P1',
            'user_id': 'U2',
            'rating': 4,
            'review_content': 'Decent product.',
            'review_timestamp': datetime(2023, 10, 20, 9, 0, 0),
            'account_age': datetime(2023, 9, 1, 0, 0, 0), # Account created almost 2 months ago
            'review_velocity_per_product': 12,
            'current_time': mock_now
        }
        result = self.rules_engine.apply_rules(review_data)
        self.assertIsNone(result)

    def test_identical_content_rule(self):
        # Review data that should trigger identical_content_1
        review_data = {
            'review_id': 'R3',
            'product_id': 'P2',
            'user_id': 'U3',
            'rating': 1,
            'review_content': 'Bad!',
            'review_timestamp': datetime.now(),
            'is_duplicate_content': True,
            'duplicate_count': 4
        }
        result = self.rules_engine.apply_rules(review_data)
        self.assertIsNotNone(result)
        self.assertEqual(result['severity'], 'MEDIUM')
        self.assertEqual(len(result['reasons']), 1)
        self.assertEqual(result['reasons'][0]['rule_id'], 'identical_content_1')

    def test_low_rating_new_product_rule(self):
        # Mock datetime.now() for consistent testing
        mock_now = datetime(2023, 10, 27, 10, 0, 0)
        with patch('src.review_ingestion_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            mock_datetime.timedelta = timedelta

            # Review data that should trigger low_rating_new_product
            review_data = {
                'review_id': 'R4',
                'product_id': 'P_new_1',
                'user_id': 'U4',
                'rating': 1,
                'review_content': 'Product broke quickly.',
                'review_timestamp': datetime(2023, 10, 26, 0, 0, 0), # Review yesterday
                'product_launch_age': datetime(2023, 10, 10, 0, 0, 0), # Product launched 17 days ago
                'account_age': datetime(2023, 10, 20, 0, 0, 0), # Account created 7 days ago
                'current_time': mock_now
            }
            result = self.rules_engine.apply_rules(review_data)
            self.assertIsNotNone(result)
            self.assertEqual(result['severity'], 'MEDIUM')
            self.assertEqual(len(result['reasons']), 1)
            self.assertEqual(result['reasons'][0]['rule_id'], 'low_rating_new_product')

    def test_no_rules_triggered(self):
        # Review data that should not trigger any rules
        mock_now = datetime(2023, 10, 27, 10, 0, 0)
        with patch('src.review_ingestion_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            mock_datetime.timedelta = timedelta

            review_data = {
                'review_id': 'R5',
                'product_id': 'P_old_1',
                'user_id': 'U5',
                'rating': 4,
                'review_content': 'Good product, been using for a while.',
                'review_timestamp': datetime(2023, 1, 1, 0, 0, 0),
                'product_launch_age': datetime(2022, 1, 1, 0, 0, 0), # Old product
                'account_age': datetime(2023, 1, 1, 0, 0, 0), # Old account
                'review_velocity_per_product': 1,
                'is_duplicate_content': False,
                'current_time': mock_now
            }
            result = self.rules_engine.apply_rules(review_data)
            self.assertIsNone(result)

    def test_multiple_rules_triggered(self):
        # Create a rule that would also trigger alongside another
        # For simplicity, let's assume the velocity spike and low rating rules can overlap if conditions meet
        self.dummy_rules.append({
            "rule_id": "another_rule_low_rating",
            "description": "Very low rating from any account.",
            "conditions": {
                "rating": {"operator": "<=", "value": 1}
            },
            "severity": "LOW",
            "flag_reason": "Very low rating."
        })
        with open(self.test_rules_path, 'w') as f:
            json.dump(self.dummy_rules, f)
        self.rules_engine = RulesEngine(rules_config_path=self.test_rules_path) # Reload rules

        mock_now = datetime(2023, 10, 27, 10, 0, 0)
        with patch('src.review_ingestion_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            mock_datetime.timedelta = timedelta

            review_data = {
                'review_id': 'R6',
                'product_id': 'P_new_2',
                'user_id': 'U6',
                'rating': 1,
                'review_content': 'Terrible!',
                'review_timestamp': datetime(2023, 10, 26, 0, 0, 0),
                'product_launch_age': datetime(2023, 10, 15, 0, 0, 0), # Product launched 12 days ago
                'account_age': datetime(2023, 10, 20, 0, 0, 0), # Account created 7 days ago
                'review_velocity_per_product': 15, # High velocity
                'current_time': mock_now
            }
            result = self.rules_engine.apply_rules(review_data)
            self.assertIsNotNone(result)
            # Expecting both velocity_spike_1, low_rating_new_product, and another_rule_low_rating to trigger
            self.assertEqual(result['severity'], 'HIGH') # Highest severity from velocity_spike_1
            self.assertEqual(len(result['reasons']), 3)
            rule_ids = {r['rule_id'] for r in result['reasons']}
            self.assertIn('velocity_spike_1', rule_ids)
            self.assertIn('low_rating_new_product', rule_ids)
            self.assertIn('another_rule_low_rating', rule_ids)

if __name__ == '__main__':
    unittest.main()