import json
import re
from datetime import datetime
from src.data_models.review_data_models import ProcessedReview

class DataProcessor:
    def __init__(self):
        pass

    def _clean_text(self, text: str) -> str:
        """Performs basic text cleaning."""
        if not isinstance(text, str):
            return ""
        text = text.strip()
        text = re.sub(r'\s+', ' ', text) # Replace multiple spaces with a single space
        return text.lower() # Convert to lowercase

    def parse_and_clean_review(self, raw_review_data: dict) -> ProcessedReview:
        """
        Parses and cleans raw review data into a ProcessedReview object.
        """
        original_review_id = raw_review_data.get('review_id')
        product_id = raw_review_data.get('product_id')
        reviewer_id = raw_review_data.get('reviewer_id')
        rating = raw_review_data.get('rating')
        timestamp = raw_review_data.get('timestamp')
        review_text = raw_review_data.get('text', '')

        # Basic validation and type conversion
        if not all([original_review_id, product_id, reviewer_id, rating, timestamp]):
            print(f"Warning: Missing critical fields in review data: {raw_review_data.keys()}")
            # In a real system, we'd log this and potentially send to a dead-letter queue
            raise ValueError("Missing critical review data fields.")

        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                raise ValueError("Rating out of expected range (1-5).")
        except (ValueError, TypeError):
            print(f"Warning: Invalid rating value: {rating}. Defaulting to 0.")
            rating = 0 # Defaulting for now, in production this would be handled more robustly

        try:
            # Assuming timestamp is epoch milliseconds
            timestamp = int(timestamp)
        except (ValueError, TypeError):
            print(f"Warning: Invalid timestamp value: {timestamp}. Defaulting to current time.")
            timestamp = int(datetime.now().timestamp() * 1000)

        cleaned_text = self._clean_text(review_text)

        processed_review = ProcessedReview(
            original_review_id=original_review_id,
            product_id=product_id,
            reviewer_id=reviewer_id,
            rating=rating,
            timestamp=timestamp,
            cleaned_text=cleaned_text
        )
        return processed_review

# Example Usage (for testing)
if __name__ == "__main__":
    processor = DataProcessor()
    
    sample_raw_review = {
        "review_id": "r12345",
        "product_id": "p67890",
        "reviewer_id": "u11223",
        "rating": 5,
        "timestamp": 1678886400000, # Example timestamp (March 15, 2023 00:00:00 GMT)
        "text": "  This is an AMAZING product! Highly recommend.   "
    }

    try:
        processed_review = processor.parse_and_clean_review(sample_raw_review)
        print("Processed Review:")
        print(json.dumps(processed_review.to_dict(), indent=2))
    except ValueError as e:
        print(f"Error processing review: {e}")

    sample_bad_review = {
        "review_id": "r12346",
        "product_id": "p67890",
        "reviewer_id": "u11223",
        "rating": "invalid",
        "timestamp": "bad_time",
        "text": "Another review"
    }
    try:
        processed_review = processor.parse_and_clean_review(sample_bad_review)
        print("Processed Review (bad data):")
        print(json.dumps(processed_review.to_dict(), indent=2))
    except ValueError as e:
        print(f"Error processing bad review: {e}")
