import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.data_models.review_model import Review, DetectionResults, ReviewMetadata
from src.api_clients.amazon_review_client import AmazonReviewAPIClient
from src.repositories.review_repository import InMemoryReviewRepository
from src.services.ingestion_service import IngestionService

class TestIngestionPipeline(unittest.TestCase):

    def setUp(self):
        self.mock_api_client = AmazonReviewAPIClient() # Use the mock client
        self.mock_repository = InMemoryReviewRepository() # Use the in-memory repository
        self.ingestion_service = IngestionService(self.mock_api_client, self.mock_repository)

    def test_amazon_review_api_client_get_reviews(self):
        # Test if the mock client returns reviews as expected
        reviews = self.mock_api_client.get_reviews(batch_size=3)
        self.assertEqual(len(reviews), 3)
        self.assertTrue(all(isinstance(r, Review) for r in reviews))
        self.assertEqual(reviews[0].reviewId, "R_mock_1")

        # Test subsequent calls
        reviews2 = self.mock_api_client.get_reviews(batch_size=3)
        self.assertEqual(len(reviews2), 3)
        self.assertEqual(reviews2[0].reviewId, "R_mock_4")

        # Test exhaustion
        self.mock_api_client._current_index = len(self.mock_api_client._reviews_data)
        reviews_empty = self.mock_api_client.get_reviews(batch_size=3)
        self.assertEqual(len(reviews_empty), 0)

    def test_ingestion_service_ingest_reviews_batch(self):
        # Test successful ingestion
        ingested_count = self.ingestion_service.ingest_reviews_batch(batch_size=2)
        self.assertEqual(ingested_count, 2)
        self.assertEqual(len(self.mock_repository.get_all_reviews()), 2)
        self.assertIsNotNone(self.mock_repository.get_review_by_id("R_mock_1"))

        # Test ingesting an empty batch (e.g., no new reviews)
        # Reset client index to simulate no more reviews
        self.mock_api_client._current_index = len(self.mock_api_client._reviews_data)
        ingested_count_empty = self.ingestion_service.ingest_reviews_batch(batch_size=2)
        self.assertEqual(ingested_count_empty, 0)
        self.assertEqual(len(self.mock_repository.get_all_reviews()), 2) # Should still be 2 from previous ingestion

    @patch('src.api_clients.amazon_review_client.AmazonReviewAPIClient.get_reviews')
    def test_ingestion_service_error_handling(self, mock_get_reviews):
        # Test error handling during API client call
        mock_get_reviews.side_effect = Exception("API Error")
        ingested_count = self.ingestion_service.ingest_reviews_batch(batch_size=1)
        self.assertEqual(ingested_count, 0)
        self.assertEqual(len(self.mock_repository.get_all_reviews()), 0) # No reviews should be saved

    def test_full_ingestion_pipeline_integration(self):
        # Simulate multiple batches and ensure all reviews are ingested
        total_ingested = 0
        while True:
            count = self.ingestion_service.ingest_reviews_batch(batch_size=3)
            if count == 0:
                break
            total_ingested += count
            if total_ingested >= len(self.mock_api_client._reviews_data):
                break

        self.assertEqual(len(self.mock_repository.get_all_reviews()), len(self.mock_api_client._reviews_data))
        # Verify a specific review content
        review_5 = self.mock_repository.get_review_by_id("R_mock_5")
        self.assertIsNotNone(review_5)
        self.assertEqual(review_5.reviewText, "This product is absolutely wonderful. Highly recommend!")

if __name__ == '__main__':
    unittest.main()
