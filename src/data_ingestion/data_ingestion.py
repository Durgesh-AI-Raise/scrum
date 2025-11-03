
import json
import datetime
import os
import uuid

def _get_sample_review_data():
    """Simulates fetching review data from a source API."""
    reviews = [
        {
            "review_id": str(uuid.uuid4()),
            "product_id": "PROD001",
            "user_id": "USER001",
            "review_text": "This product is amazing! Highly recommend it to everyone.",
            "review_date": (datetime.datetime.now() - datetime.timedelta(days=5)).isoformat(),
            "rating": 5
        },
        {
            "review_id": str(uuid.uuid4()),
            "product_id": "PROD002",
            "user_id": "USER002",
            "review_text": "A decent product, met my expectations.",
            "review_date": (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat(),
            "rating": 4
        },
        {
            "review_id": str(uuid.uuid4()),
            "product_id": "PROD001",
            "user_id": "USER003",
            "review_text": "I love this item. It works perfectly.",
            "review_date": (datetime.datetime.now() - datetime.timedelta(days=3)).isoformat(),
            "rating": 5
        },
        {
            "review_id": str(uuid.uuid4()),
            "product_id": "PROD003",
            "user_id": "USER001",
            "review_text": "This product is amazing! Highly recommend it to everyone.", # Duplicate content example
            "review_date": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
            "rating": 5
        }
    ]
    return reviews

def ingest_review_data(output_file: str = 'data/raw_reviews.json'):
    """
    Ingests review data from a source and stores it.
    """
    print(f"[{datetime.datetime.now().isoformat()}] Starting review data ingestion...")

    new_reviews = _get_sample_review_data()
    ingested_data = []

    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            try:
                ingested_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: {output_file} is empty or malformed. Starting fresh.")
                ingested_data = []

    for review in new_reviews:
        review["source_timestamp"] = datetime.datetime.now().isoformat()
        ingested_data.append(review)
        print(f"[{datetime.datetime.now().isoformat()}] Ingested review_id: {review['review_id']}")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(ingested_data, f, indent=4)

    print(f"[{datetime.datetime.now().isoformat()}] Finished review data ingestion. Total reviews: {len(ingested_data)}")

if __name__ == "__main__":
    ingest_review_data()
