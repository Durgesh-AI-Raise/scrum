import json
import os
import boto3
from datetime import datetime

# Environment variables
KINESIS_STREAM_NAME = os.environ.get("KINESIS_STREAM_NAME", "amazon-reviews-raw")
REGION = os.environ.get("AWS_REGION", "us-east-1") # Example region

kinesis_client = boto3.client('kinesis', region_name=REGION)

def fetch_reviews_from_source():
    """
    Placeholder function to simulate fetching new Amazon reviews.
    In a real scenario, this would interact with an external API or data feed.
    """
    print("Fetching reviews from external source...")
    # Simulate new reviews with current timestamp
    current_time = datetime.utcnow().isoformat() + "Z"
    return [
        {"id": f"R_INGEST_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_1", "product": "B07XYZ123", "user": "U98765", "title": "Best gadget ever!", "content": "I am so impressed with this product. It works flawlessly.", "stars": 5, "date": current_time},
        {"id": f"R_INGEST_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_2", "product": "B01ABCDEF", "user": "U12345", "title": "Could be better", "content": "The battery life is not as advertised. Disappointed.", "stars": 2, "date": current_time},
        {"id": f"R_INGEST_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_3", "product": "B07XYZ123", "user": "U98765", "title": "Another great buy!", "content": "Just bought another one for my friend. Highly recommend.", "stars": 5, "date": current_time}
    ]

def preprocess_review(raw_review):
    """
    Transforms raw review data into a standardized format.
    """
    return {
        "reviewId": raw_review["id"],
        "productId": raw_review["product"],
        "userId": raw_review["user"],
        "title": raw_review["title"],
        "text": raw_review["content"],
        "rating": raw_review["stars"],
        "timestamp": raw_review["date"],
        "country": "US", # Placeholder, ideally derived
        "sourceUrl": f"https://www.amazon.com/dp/{raw_review['product']}/reviews/{raw_review['id']}" # Example URL
    }

def lambda_handler(event, context):
    """
    AWS Lambda handler for ingesting Amazon reviews into Kinesis.
    """
    try:
        new_reviews = fetch_reviews_from_source()
        if not new_reviews:
            print("No new reviews to ingest.")
            return {"statusCode": 200, "body": "No new reviews."}

        for raw_review in new_reviews:
            processed_review = preprocess_review(raw_review)
            
            # Use productId as PartitionKey for Kinesis to ensure reviews for the same product go to the same shard
            partition_key = processed_review["productId"] 
            
            kinesis_client.put_record(
                StreamName=KINESIS_STREAM_NAME,
                Data=json.dumps(processed_review).encode('utf-8'),
                PartitionKey=partition_key
            )
            print(f"Ingested review {processed_review['reviewId']} for product {processed_review['productId']} to Kinesis.")

        return {"statusCode": 200, "body": "Reviews ingested successfully."}

    except Exception as e:
        print(f"Error during ingestion: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
