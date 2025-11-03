
import unittest
import json
import boto3
from moto import mock_aws
from unittest.mock import patch, MagicMock
from src.ingestion.review_producer import generate_mock_review, put_record_to_kinesis, KINESIS_STREAM_NAME, AWS_REGION

class TestReviewProducer(unittest.TestCase):

    def test_generate_mock_review(self):
        """Test that generate_mock_review produces a well-formed review."""
        review = generate_mock_review()
        self.assertIsInstance(review, dict)
        self.assertIn("review_id", review)
        self.assertIn("product_id", review)
        self.assertIn("reviewer_id", review)
        self.assertIn("stars", review)
        self.assertIn("review_text", review)
        self.assertIn("review_date", review)
        self.assertIn("extracted_at", review)
        self.assertIsInstance(review["stars"], int)
        self.assertTrue(1 <= review["stars"] <= 5)
        self.assertIsInstance(review["review_id"], str)
        self.assertIsInstance(review["product_id"], str)

    @mock_aws
    @patch('src.ingestion.review_producer.boto3.client')
    def test_put_record_to_kinesis_success(self, mock_boto_client):
        """Test successful record insertion into Kinesis."""
        # Mock the Kinesis client and its put_record method
        mock_kinesis_client = MagicMock()
        mock_boto_client.return_value = mock_kinesis_client
        mock_kinesis_client.put_record.return_value = {
            'ShardId': 'shardId-000000000000',
            'SequenceNumber': '495903382714902179612903107149022068007412781491238947'
        }

        review_data = generate_mock_review()
        partition_key = review_data["product_id"]

        response = put_record_to_kinesis(KINESIS_STREAM_NAME, review_data, partition_key)

        mock_boto_client.assert_called_once_with('kinesis', region_name=AWS_REGION)
        mock_kinesis_client.put_record.assert_called_once_with(
            StreamName=KINESIS_STREAM_NAME,
            Data=json.dumps(review_data),
            PartitionKey=partition_key
        )
        self.assertIsNotNone(response)
        self.assertIn('SequenceNumber', response)

    @mock_aws
    @patch('src.ingestion.review_producer.boto3.client')
    def test_put_record_to_kinesis_failure(self, mock_boto_client):
        """Test error handling during record insertion into Kinesis."""
        mock_kinesis_client = MagicMock()
        mock_boto_client.return_value = mock_kinesis_client
        mock_kinesis_client.put_record.side_effect = Exception("Kinesis error")

        review_data = generate_mock_review()
        partition_key = review_data["product_id"]

        with self.assertRaises(Exception):
            put_record_to_kinesis(KINESIS_STREAM_NAME, review_data, partition_key)

        mock_kinesis_client.put_record.assert_called_once()

if __name__ == '__main__':
    unittest.main()
