import logging
from typing import List
from src.api_clients.amazon_review_client import AmazonReviewAPIClient
from src.repositories.review_repository import ReviewRepository
from src.data_models.review_model import Review

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class IngestionService:
    def __init__(self, api_client: AmazonReviewAPIClient, review_repository: ReviewRepository):
        self.api_client = api_client
        self.review_repository = review_repository

    def ingest_reviews_batch(self, batch_size: int = 5) -> int:
        """
        Pulls a batch of reviews from the Amazon API client and saves them to the repository.
        Returns the number of reviews ingested.
        """
        logging.info(f"Attempting to ingest {batch_size} reviews...")
        try:
            reviews: List[Review] = self.api_client.get_reviews(batch_size=batch_size)
            if not reviews:
                logging.info("No new reviews found in this batch.")
                return 0

            for review in reviews:
                self.review_repository.save_review(review)
            logging.info(f"Successfully ingested {len(reviews)} reviews.")
            return len(reviews)
        except Exception as e:
            logging.error(f"Error during review ingestion: {e}")
            return 0

# Example Usage (for local testing, not part of the service itself)
# if __name__ == "__main__":
#     mock_api_client = AmazonReviewAPIClient()
#     in_memory_repo = InMemoryReviewRepository()
#     ingestion_service = IngestionService(mock_api_client, in_memory_repo)

#     # Simulate continuous ingestion
#     print("--- Starting simulated ingestion ---")
#     for _ in range(3): # Run 3 batches
#         ingested_count = ingestion_service.ingest_reviews_batch(batch_size=2)
#         print(f"Batch completed. Ingested {ingested_count} reviews.")
#         import time
#         time.sleep(1) # Simulate delay

#     print("\n--- All reviews in repository after ingestion ---")
#     all_reviews = in_memory_repo.get_all_reviews()
#     if all_reviews:
#         for review in all_reviews:
#             print(f"  ID: {review.reviewId}, Product: {review.productId}, Reviewer: {review.reviewerId}, Text: {review.reviewText[:50]}...")
#     else:
#         print("No reviews found in the repository.")
#     print("--- Simulated ingestion finished ---")
