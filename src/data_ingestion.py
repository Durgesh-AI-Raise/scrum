import json
from datetime import datetime

class Review:
    """
    Represents a standardized review object within the ARIG system.
    """
    def __init__(self, review_id: str, product_id: str, reviewer_id: str, rating: int,
                 review_text: str, review_date: str, reviewer_account_creation_date: str):
        self.review_id = review_id
        self.product_id = product_id
        self.reviewer_id = reviewer_id
        self.rating = rating
        self.review_text = review_text
        self.review_date = review_date # Stored as ISO format string for simplicity
        self.reviewer_account_creation_date = reviewer_account_creation_date # ISO format string

    def __repr__(self):
        return (f"Review(id={self.review_id}, product={self.product_id}, "
                f"reviewer={self.reviewer_id}, rating={self.rating})")

class ReviewDataIngestionModule:
    """
    Module responsible for extracting, transforming, and loading review data
    into the ARIG system.
    """
    def __init__(self, data_source_path: str):
        self.data_source_path = data_source_path

    def _extract_data(self) -> list:
        """
        Simulates extracting raw review data from a source (e.g., a JSON file).
        In a real system, this would connect to databases, APIs, etc.
        """
        print(f"Extracting raw data from: {self.data_source_path}")
        try:
            with open(self.data_source_path, 'r') as f:
                raw_reviews = json.load(f)
            return raw_reviews
        except FileNotFoundError:
            print(f"Error: Data source file not found at {self.data_source_path}")
            return []
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {self.data_source_path}")
            return []

    def _transform_data(self, raw_reviews: list) -> list[Review]:
        """
        Transforms raw review data into standardized Review objects.
        Includes basic validation and type conversion.
        """
        processed_reviews = []
        for raw_review in raw_reviews:
            try:
                # Basic validation and type conversion
                review_id = str(raw_review.get('review_id'))
                product_id = str(raw_review.get('product_id'))
                reviewer_id = str(raw_review.get('reviewer_id'))
                rating = int(raw_review.get('rating'))
                review_text = str(raw_review.get('review_text'))
                
                # Ensure date formats are consistent (e.g., ISO 8601)
                review_date_str = raw_review.get('review_date')
                reviewer_account_creation_date_str = raw_review.get('reviewer_account_creation_date')

                # Minimal date validation and standardization
                try:
                    datetime.fromisoformat(review_date_str.replace('Z', '+00:00')) # Handle 'Z' for UTC
                    datetime.fromisoformat(reviewer_account_creation_date_str.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    print(f"Warning: Invalid date format for review_id {review_id}. Skipping or using default.")
                    continue # Skip this review if dates are malformed

                processed_reviews.append(
                    Review(
                        review_id=review_id,
                        product_id=product_id,
                        reviewer_id=reviewer_id,
                        rating=rating,
                        review_text=review_text,
                        review_date=review_date_str,
                        reviewer_account_creation_date=reviewer_account_creation_date_str
                    )
                )
            except (ValueError, TypeError, KeyError) as e:
                print(f"Error transforming review: {raw_review}. Reason: {e}. Skipping.")
        return processed_reviews

    def ingest_data(self) -> list[Review]:
        """
        Orchestrates the data ingestion process: extract -> transform -> load.
        """
        raw_data = self._extract_data()
        if not raw_data:
            print("No raw data extracted. Ingestion halted.")
            return []
        processed_data = self._transform_data(raw_data)
        print(f"Successfully ingested {len(processed_data)} reviews.")
        return processed_data

# Example Usage (for testing purposes) - This block would typically be in a separate test file or script.
if __name__ == "__main__":
    # In a real application, the data source path would be configured.
    # For this example, we assume 'data/dummy_reviews.json' exists.
    # To run this example, create 'data' directory and 'dummy_reviews.json' inside it.
    
    # Example of creating a dummy JSON file if it doesn't exist for direct running
    dummy_data = [
        {
            "review_id": "r101",
            "product_id": "p2001",
            "reviewer_id": "u5001",
            "rating": 5,
            "review_text": "Excellent product, highly recommend!",
            "review_date": "2023-10-26T10:00:00Z",
            "reviewer_account_creation_date": "2023-01-15T00:00:00Z"
        },
        {
            "review_id": "r102",
            "product_id": "p2002",
            "reviewer_id": "u5002",
            "rating": 1,
            "review_text": "Worst purchase ever, completely useless.",
            "review_date": "2023-10-25T14:30:00Z",
            "reviewer_account_creation_date": "2022-05-20T00:00:00Z"
        },
        {
            "review_id": "r103",
            "product_id": "p2001",
            "reviewer_id": "u5001", # Same reviewer
            "rating": 4,
            "review_text": "Pretty good, but could be better.",
            "review_date": "2023-10-26T11:00:00Z", # Rapid review
            "reviewer_account_creation_date": "2023-01-15T00:00:00Z"
        },
        {
            "review_id": "r104",
            "product_id": "p2003",
            "reviewer_id": "u5003", # New account
            "rating": 5,
            "review_text": "Amazing!",
            "review_date": "2023-10-26T15:00:00Z",
            "reviewer_account_creation_date": "2023-10-20T00:00:00Z" # Very recent
        },
        {
            "review_id": "r105",
            "product_id": "p2004",
            "reviewer_id": "u5003", # New account, rapid review
            "rating": 5,
            "review_text": "Love it!",
            "review_date": "2023-10-26T15:05:00Z",
            "reviewer_account_creation_date": "2023-10-20T00:00:00Z"
        },
        {
            "review_id": "r106",
            "product_id": "p2005",
            "reviewer_id": "u5004",
            "rating": 3,
            "review_text": "Good",
            "review_date": "2023-10-26T16:00:00Z",
            "reviewer_account_creation_date": "2023-01-01T00:00:00Z"
        }
    ]
    
    # Ensure the 'data' directory exists for this example to run
    import os
    os.makedirs('data', exist_ok=True)
    dummy_data_path = "data/dummy_reviews.json"
    with open(dummy_data_path, "w") as f:
        json.dump(dummy_data, f, indent=4)

    ingestion_module = ReviewDataIngestionModule(data_source_path=dummy_data_path)
    ingested_reviews = ingestion_module.ingest_data()

    for review in ingested_reviews:
        print(review)