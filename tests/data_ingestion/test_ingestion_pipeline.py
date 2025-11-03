import unittest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime
import sys
import os

# Add parent directory to path to allow importing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data_ingestion')))

from producer import generate_review, produce_reviews
from consumer_parser import validate_review, run_parser_consumer, EXPECTED_REVIEW_SCHEMA

class TestDataIngestionPipeline(unittest.TestCase):

    def setUp(self):
        # Reset mocks before each test
        pass

    # --- Producer Tests ---
    def test_generate_review_structure_and_types(self):
        review = generate_review()
        self.assertIsInstance(review, dict)
        self.assertIn('reviewId', review)
        self.assertIn('productId', review)
        self.assertIn('userId', review)
        self.assertIn('rating', review)
        self.assertIn('title', review)
        self.assertIn('text', review)
        self.assertIn('reviewDate', review)
        self.assertIn('verifiedPurchase', review)
        self.assertIn('productCategory', review)
        self.assertIn('reviewerAccountAgeDays', review)

        self.assertIsInstance(review['reviewId'], str)
        self.assertIsInstance(review['productId'], str)
        self.assertIsInstance(review['userId'], str)
        self.assertIsInstance(review['rating'], int)
        self.assertTrue(1 <= review['rating'] <= 5)
        self.assertIsInstance(review['title'], str)
        self.assertIsInstance(review['text'], str)
        self.assertIsInstance(review['reviewDate'], str)
        try:
            datetime.fromisoformat(review['reviewDate'])
        except ValueError:
            self.fail("reviewDate is not in ISO 8601 format")
        self.assertIsInstance(review['verifiedPurchase'], bool)
        self.assertIsInstance(review['productCategory'], str)
        self.assertIsInstance(review['reviewerAccountAgeDays'], int)
        self.assertTrue(review['reviewerAccountAgeDays'] >= 1)

    @patch('producer.KafkaProducer')
    def test_produce_reviews(self, MockKafkaProducer):
        mock_producer_instance = MockKafkaProducer.return_value
        mock_producer_instance.send.return_value.get.return_value = MagicMock(topic="test", partition=0, offset=0)

        produce_reviews(num_reviews=2, interval_seconds=0) # Set interval to 0 for faster testing

        self.assertEqual(mock_producer_instance.send.call_count, 2)
        mock_producer_instance.flush.assert_called_once()

    @patch('consumer_parser.KafkaConsumer')
    @patch('consumer_parser.KafkaProducer')
    def test_run_parser_consumer_valid_message(self, MockKafkaProducer, MockKafkaConsumer):
        mock_consumer_instance = MockKafkaConsumer.return_value
        mock_producer_instance = MockKafkaProducer.return_value

        valid_message_value = {
            "reviewId": "r123", "productId": "p456", "userId": "u789", "rating": 4,
            "title": "Good product", "text": "This is a good product.",
            "reviewDate": "2023-01-15T10:30:00", "verifiedPurchase": True,
            "productCategory": "Electronics", "reviewerAccountAgeDays": 100
        }
        mock_message = MagicMock()
        mock_message.value = valid_message_value
        mock_message.offset = 123 

        mock_consumer_instance.__iter__.return_value = [mock_message]

        run_parser_consumer()

        mock_producer_instance.send.assert_called_once_with(
            'amazon_reviews_processed', valid_message_value
        )
        self.assertNotIn('amazon_reviews_dlq', [call.args[0] for call in mock_producer_instance.send.call_args_list])

    @patch('consumer_parser.KafkaConsumer')
    @patch('consumer_parser.KafkaProducer')
    def test_run_parser_consumer_invalid_message(self, MockKafkaProducer, MockKafkaConsumer):
        mock_consumer_instance = MockKafkaConsumer.return_value
        mock_producer_instance = MockKafkaProducer.return_value

        invalid_message_value = {
            "reviewId": "r123", "productId": "p456", "userId": "u789", "rating": 4,
            "title": "Good product", "text": "This is a good product.",
            "reviewDate": "2023-01-15T10:30:00", "verifiedPurchase": True,
            "productCategory": "Electronics"
        }
        mock_message = MagicMock()
        mock_message.value = invalid_message_value
        mock_message.offset = 456

        mock_consumer_instance.__iter__.return_value = [mock_message]

        run_parser_consumer()

        mock_producer_instance.send.assert_called_once()
        sent_topic = mock_producer_instance.send.call_args[0][0]
        self.assertEqual(sent_topic, 'amazon_reviews_dlq')
        dlq_payload = mock_producer_instance.send.call_args[0][1]
        self.assertEqual(dlq_payload['original_message'], invalid_message_value)
        self.assertIn("Missing required field: reviewerAccountAgeDays", dlq_payload['error'])
        self.assertNotIn('amazon_reviews_processed', [call.args[0] for call in mock_producer_instance.send.call_args_list])

    def test_validate_review_valid(self):
        valid_review = {
            "reviewId": "r123",
            "productId": "p456",
            "userId": "u789",
            "rating": 4,
            "title": "Good product",
            "text": "This is a good product.",
            "reviewDate": "2023-01-15T10:30:00",
            "verifiedPurchase": True,
            "productCategory": "Electronics",
            "reviewerAccountAgeDays": 100
        }
        is_valid, data_or_error = validate_review(valid_review)
        self.assertTrue(is_valid)
        self.assertEqual(data_or_error, valid_review)

    def test_validate_review_missing_field(self):
        invalid_review = {
            "reviewId": "r123",
            "productId": "p456",
            "userId": "u789",
            "rating": 4,
            "title": "Good product",
            "text": "This is a good product.",
            "reviewDate": "2023-01-15T10:30:00",
            "verifiedPurchase": True,
            "productCategory": "Electronics"
        }
        is_valid, data_or_error = validate_review(invalid_review)
        self.assertFalse(is_valid)
        self.assertIn("Missing required field: reviewerAccountAgeDays", data_or_error)

    def test_validate_review_incorrect_type(self):
        invalid_review = {
            "reviewId": "r123",
            "productId": "p456",
            "userId": "u789",
            "rating": "4",
            "title": "Good product",
            "text": "This is a good product.",
            "reviewDate": "2023-01-15T10:30:00",
            "verifiedPurchase": True,
            "productCategory": "Electronics",
            "reviewerAccountAgeDays": 100
        }
        is_valid, data_or_error = validate_review(invalid_review)
        self.assertFalse(is_valid)
        self.assertIn("Field rating has incorrect type. Expected int, got str", data_or_error)

    def test_validate_review_invalid_rating_range(self):
        invalid_review = {
            "reviewId": "r123",
            "productId": "p456",
            "userId": "u789",
            "rating": 6,
            "title": "Good product",
            "text": "This is a good product.",
            "reviewDate": "2023-01-15T10:30:00",
            "verifiedPurchase": True,
            "productCategory": "Electronics",
            "reviewerAccountAgeDays": 100
        }
        is_valid, data_or_error = validate_review(invalid_review)
        self.assertFalse(is_valid)
        self.assertIn("Rating must be between 1 and 5, got 6", data_or_error)

    def test_validate_review_invalid_date_format(self):
        invalid_review = {
            "reviewId": "r123",
            "productId": "p456",
            "userId": "u789",
            "rating": 4,
            "title": "Good product",
            "text": "This is a good product.",
            "reviewDate": "15-01-2023",
            "verifiedPurchase": True,
            "productCategory": "Electronics",
            "reviewerAccountAgeDays": 100
        }
        is_valid, data_or_error = validate_review(invalid_review)
        self.assertFalse(is_valid)
        self.assertIn("Invalid date format for reviewDate", data_or_error)

if __name__ == '__main__':
    unittest.main()
