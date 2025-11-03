import json
from datetime import datetime
from src.db_utils import insert_reviews

def parse_review_data(raw_review):
    verified = raw_review.get("verified", False)
    return {
        "asin": raw_review.get("asin"),
        "reviewer_id": raw_review.get("reviewerID"),
        "rating": int(raw_review.get("overall", 0)),
        "review_text": raw_review.get("reviewText"),
        "submission_date": datetime.strptime(raw_review.get("reviewTime", "01 01, 1970"), "%m %d, %Y").isoformat(),
        "verified_purchase": verified
    }

def ingest_reviews_from_mock_source(file_path):
    with open(file_path, 'r') as f:
        raw_data = json.load(f)
    processed_reviews = [parse_review_data(review) for review in raw_data]
    return processed_reviews

if __name__ == "__main__":
    mock_data_path = "mock_reviews.json"
    processed_reviews = ingest_reviews_from_mock_source(mock_data_path)
    insert_reviews(processed_reviews)
    print(f"Ingestion pipeline completed for {len(processed_reviews)} reviews.")