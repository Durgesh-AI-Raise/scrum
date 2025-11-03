# ingestion_service/batch_ingestor.py

import pandas as pd
import json
from kafka import KafkaProducer
import datetime
import os

# Configuration
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC_REVIEWS = "amazon_reviews_raw"
BATCH_DATA_SOURCE_PATH = "data/amazon_reviews_historical.csv" # Placeholder for local CSV or S3 path

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def ingest_batch_reviews(file_path):
    """
    Ingests historical review data from a batch source (e.g., CSV) and publishes to Kafka.
    """
    try:
        # Simulate reading from a CSV. In a real scenario, this could be from S3 using boto3
        # or a database dump.
        print(f"Starting batch ingestion from {file_path}")
        # For demonstration, creating a dummy CSV if it doesn't exist
        if not os.path.exists(file_path):
            print(f"Creating dummy batch data file at {file_path}")
            dummy_data = {
                'id': [f'hist_review_{i}' for i in range(10)],
                'product_id': [f'prod_{i%3}' for i in range(10)],
                'reviewer_id': [f'user_{i%5}' for i in range(10)],
                'rating': [5, 4, 1, 3, 5, 2, 4, 5, 3, 1],
                'title': ['Great product', 'Good buy', 'Terrible', 'Okay', 'Love it', 'Bad', 'Worth it', 'Excellent', 'Mediocre', 'Avoid'],
                'text': ['This is a great product.', 'Happy with the purchase.', 'Very disappointed with this item.', 'It\'s alright, nothing special.', 'Absolutely love this!', 'Broken on arrival.', 'Decent quality for the price.', 'Highly recommend to everyone.', 'Could be better.', 'Worst product ever.'],
                'date': [(datetime.datetime.now() - datetime.timedelta(days=i)).isoformat() for i in range(10)],
                'verified_purchase': [True, True, False, True, True, False, True, True, False, True],
                'helpful_votes': [10, 5, 2, 1, 15, 0, 3, 8, 2, 0],
                'product_category': ['Electronics', 'Home', 'Books', 'Electronics', 'Home', 'Books', 'Electronics', 'Home', 'Books', 'Electronics'],
                'product_brand': ['BrandA', 'BrandB', 'BrandC', 'BrandA', 'BrandB', 'BrandC', 'BrandA', 'BrandB', 'BrandC', 'BrandA']
            }
            pd.DataFrame(dummy_data).to_csv(file_path, index=False)
            print("Dummy batch data created.")

        df = pd.read_csv(file_path)

        reviews_ingested_count = 0
        for index, row in df.iterrows():
            review = {
                "reviewId": row.get("id"),
                "productId": row.get("product_id"),
                "reviewerId": row.get("reviewer_id"),
                "rating": int(row.get("rating")),
                "reviewTitle": row.get("title"),
                "reviewText": row.get("text"),
                "reviewDate": row.get("date"), # ISO format assumed
                "verifiedPurchase": bool(row.get("verified_purchase")),
                "helpfulVotes": int(row.get("helpful_votes")),
                "productCategory": row.get("product_category"),
                "productBrand": row.get("product_brand"),
                "reviewSource": "Amazon_Batch",
                "ingestionTimestamp": datetime.datetime.now().isoformat()
            }
            print(f"Ingesting batch review: {review['reviewId']}")
            producer.send(KAFKA_TOPIC_REVIEWS, review)
            reviews_ingested_count += 1

        producer.flush()
        print(f"Successfully ingested {reviews_ingested_count} batch reviews.")

    except FileNotFoundError:
        print(f"Error: Batch data source file not found at {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred during batch ingestion: {e}")

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs(os.path.dirname(BATCH_DATA_SOURCE_PATH), exist_ok=True)
    ingest_batch_reviews(BATCH_DATA_SOURCE_PATH)
