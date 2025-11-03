import json
import os
import boto3
from datetime import datetime, timedelta

kinesis_client = boto3.client('kinesis')
KINESIS_STREAM_NAME = os.environ.get('KINESIS_STREAM_NAME', 'amazon-reviews-stream')
# Placeholder for actual API details or scraping logic
# REVIEW_API_ENDPOINT = os.environ.get('REVIEW_API_ENDPOINT', 'https://api.amazon.com/reviews/latest')
# API_KEY = os.environ.get('API_KEY', 'YOUR_API_KEY')

def fetch_reviews_from_source(last_fetched_time=None):
    """
    Simulates fetching new Amazon product reviews from an API or scraping source.
    In a real scenario, this would involve API calls, pagination, and error handling.
    """
    # Mock data for demonstration purposes
    # In a real system, 'last_fetched_time' would be used to query for newer reviews.
    print(f"Simulating fetching reviews since: {last_fetched_time}")

    mock_reviews = [
        {
            "review_id": "R001",
            "product_id": "B001",
            "user_id": "U101",
            "stars": 5,
            "review_title": "Absolutely fantastic!",
            "review_body": "This product exceeded my expectations. Highly recommend it to everyone. Great quality and superb features.",
            "review_date": (datetime.now() - timedelta(minutes=5)).isoformat() + 'Z',
            "verified_purchase": True,
            "helpful_votes": 10,
            "reviewer_name": "HappyCustomer",
            "source_metadata": {"source": "amazon-mock", "version": "1.0"}
        },
        {
            "review_id": "R002",
            "product_id": "B002",
            "user_id": "U102",
            "stars": 1,
            "review_title": "Disappointing product",
            "review_body": "It broke after just a week of use. Very bad quality and a complete scam. Do not buy this garbage.",
            "review_date": (datetime.now() - timedelta(minutes=3)).isoformat() + 'Z',
            "verified_purchase": False,
            "helpful_votes": 2,
            "reviewer_name": "UpsetUser",
            "source_metadata": {"source": "amazon-mock", "version": "1.0"}
        },
        {
            "review_id": "R003",
            "product_id": "B001",
            "user_id": "U103",
            "stars": 4,
            "review_title": "Good, but could be better",
            "review_body": "Overall a good experience. The delivery was fast and the packaging was excellent. One minor flaw with the battery life.",
            "review_date": (datetime.now() - timedelta(minutes=1)).isoformat() + 'Z',
            "verified_purchase": True,
            "helpful_votes": 5,
            "reviewer_name": "NeutralReviewer",
            "source_metadata": {"source": "amazon-mock", "version": "1.0"}
        }
    ]
    return mock_reviews

def lambda_handler(event, context):
    # In a real system, you might store and retrieve the last_fetched_timestamp
    # from a persistent store like DynamoDB to ensure no data is missed.
    last_fetched_timestamp = None 
    
    new_reviews = fetch_reviews_from_source(last_fetched_timestamp)
    
    if not new_reviews:
        print("No new reviews to ingest.")
        return {'statusCode': 200, 'body': 'No new reviews'}

    records_to_put = []
    for review in new_reviews:
        records_to_put.append({
            'Data': json.dumps(review).encode('utf-8'),
            'PartitionKey': review['product_id'] # Use product_id for even distribution across Kinesis shards
        })
    
    try:
        response = kinesis_client.put_records(
            Records=records_to_put,
            StreamName=KINESIS_STREAM_NAME
        )
        print(f"Successfully put {len(new_reviews)} records to Kinesis. Response: {response}")
        # Check for failed records within the response if any
        if response.get('FailedRecordCount', 0) > 0:
            print(f"Warning: {response['FailedRecordCount']} records failed to put.")
    except Exception as e:
        print(f"Error putting records to Kinesis: {e}")
        raise # Re-raise to trigger Lambda retries

    return {
        'statusCode': 200,
        'body': json.dumps(f'Ingested {len(new_reviews)} reviews')
    }