
import json
import time
from datetime import datetime, timedelta

class RawReview:
    def __init__(self, review_id, product_id, reviewer_id, stars, review_text, review_date, verified_purchase):
        self.review_id = review_id
        self.product_id = product_id
        self.reviewer_id = reviewer_id
        self.stars = stars
        self.review_text = review_text
        self.review_date = review_date
        self.verified_purchase = verified_purchase

    def to_json(self):
        return json.dumps(self.__dict__)

# Mock function for publishing to a message queue
def publish_to_queue(queue_name, message):
    print(f"[{queue_name}] Published: {message}")

def fetch_amazon_reviews(last_fetched_timestamp=None):
    # In a real scenario, this would call an external API or read from a data source
    # For this sprint, we'll return some mock data
    mock_reviews = [
        {"review_id": "R001", "product_id": "P001", "reviewer_id": "U001", "stars": 5, "review_text": "Great product!", "review_date": "2023-01-01T10:00:00Z", "verified_purchase": True},
        {"review_id": "R002", "product_id": "P002", "reviewer_id": "U002", "stars": 1, "review_text": "Terrible experience.", "review_date": "2023-01-01T11:00:00Z", "verified_purchase": False},
        {"review_id": "R003", "product_id": "P001", "reviewer_id": "U001", "stars": 4, "review_text": "Good, but could be better.", "review_date": "2023-01-01T12:00:00Z", "verified_purchase": True},
        {"review_id": "R004", "product_id": "P003", "reviewer_id": "U003", "stars": 5, "review_text": "Highly recommend!", "review_date": "2023-01-02T09:00:00Z", "verified_purchase": True}
    ]
    # Filter by last_fetched_timestamp if provided, converting string to datetime for comparison
    if last_fetched_timestamp:
        last_dt = datetime.strptime(last_fetched_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        return [r for r in mock_reviews if datetime.strptime(r['review_date'], "%Y-%m-%dT%H:%M:%SZ") > last_dt]
    return mock_reviews

def run_extraction_module():
    last_timestamp = None
    # In production, this would be a scheduled job or triggered by an event, not an infinite loop without exit
    print("Starting Review Data Extraction Module...")
    while True:
        reviews = fetch_amazon_reviews(last_timestamp)
        if reviews:
            for review_data in reviews:
                raw_review = RawReview(**review_data)
                publish_to_queue("raw_reviews_queue", raw_review.to_json())
                last_timestamp = review_data['review_date'] # Update last fetched timestamp
        else:
            print("No new reviews to extract.")
        time.sleep(60) # Poll every 60 seconds

if __name__ == "__main__":
    # Example usage:
    # run_extraction_module()
    print("Run `run_extraction_module()` to start the mock extraction process.")
