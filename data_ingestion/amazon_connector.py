import json
from typing import Iterator
from common.data_models import Review
from datetime import datetime

class AmazonReviewConnector:
    def __init__(self, data_source_path: str):
        self.data_source_path = data_source_path

    def __iter__(self) -> Iterator[Review]:
        try:
            with open(self.data_source_path, 'r') as f:
                for line in f:
                    try:
                        review_data = json.loads(line)
                        review = Review(
                            review_id=review_data.get('review_id', 'N/A'),
                            product_id=review_data.get('product_id', 'N/A'),
                            reviewer_id=review_data.get('reviewer_id', 'N/A'),
                            review_text=review_data.get('review_text', ''),
                            star_rating=int(review_data.get('star_rating', 0)),
                            review_date=datetime.fromisoformat(review_data['review_date']) if 'review_date' in review_data else datetime.utcnow(),
                            helpfulness_votes=int(review_data.get('helpfulness_votes', 0)),
                            purchase_verified=review_data.get('purchase_verified', False),
                            product_category=review_data.get('product_category'),
                            reviewer_account_age_days=review_data.get('reviewer_account_age_days')
                        )
                        yield review
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e} in line: {line.strip()}")
                        continue
                    except KeyError as e:
                        print(f"Missing key in review data: {e} in line: {line.strip()}")
                        continue
                    except Exception as e:
                        print(f"Unexpected error processing review: {e} in line: {line.strip()}")
                        continue
        except FileNotFoundError:
            print(f"Data source file not found: {self.data_source_path}")
            return # Yield nothing if file not found
