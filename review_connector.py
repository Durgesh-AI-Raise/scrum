from datetime import datetime, timedelta
from typing import List
from data_models import Review

class ReviewDataConnector:
    """
    Simulates fetching review data from an Amazon Review Database API.
    """
    def fetch_recent_reviews(self, limit: int = 100) -> List[Review]:
        """
        Fetches a specified number of recent reviews.
        In a real scenario, this would make API calls to Amazon's review database.
        For this sprint, it generates mock data.
        """
        mock_reviews = []
        # Simulate some reviews for demonstration
        now = datetime.now()
        for i in range(limit):
            product_id_base = "prod" + str(i % 5 + 1) # 5 products
            user_id_base = "user" + str(i % 20 + 1)   # 20 users
            mock_reviews.append(
                Review(
                    review_id=f"rev{i:03d}",
                    product_id=product_id_base,
                    user_id=user_id_base,
                    timestamp=now - timedelta(days=0, hours=i // 10), # spread out over a few hours
                    rating=(i % 5) + 1,
                    content=f"Review content for {product_id_base} by {user_id_base}."
                )
            )
        # Add some reviews for a burst scenario for a specific product
        # Product "prod1" gets 15 reviews in 1 hour
        for i in range(15):
            mock_reviews.append(
                Review(
                    review_id=f"burst_rev{i:02d}",
                    product_id="prod1",
                    user_id=f"user_burst_{i}",
                    timestamp=now - timedelta(minutes=i*3), # 15 reviews in 45 minutes
                    rating=5,
                    content="Great product!"
                )
            )
        return mock_reviews
