import json
import os
import boto3
from datetime import datetime

# Kinesis client
kinesis_client = boto3.client('kinesis')
STREAM_NAME = os.environ.get('KINESIS_STREAM_NAME', 'amazon-reviews-raw-stream')

def get_amazon_reviews(last_ingested_timestamp=None):
    """
    Placeholder function to simulate fetching new Amazon reviews.
    In a real scenario, this would involve calling Amazon's API
    or processing a data feed.
    """
    # Simulate fetching new reviews since the last timestamp
    # For MVP, returning a fixed set or mock data
    mock_reviews = [
        {
            "review_id": "R1ABCDEFG12345",
            "product_id": "B012345678",
            "customer_id": "CUST98765",
            "star_rating": 5,
            "review_headline": "Great product!",
            "review_body": "I love this product, it works perfectly.",
            "review_date": "2023-10-26T10:00:00Z",
            "verified_purchase": True,
            "product_title": "Example Product A",
            "product_category": "Electronics"
        },
        {
            "review_id": "R2HIJKLMN67890",
            "product_id": "B098765432",
            "customer_id": "CUST12345",
            "star_rating": 1,
            "review_headline": "Terrible experience",
            "review_body": "The product broke after one use. Very disappointed.",
            "review_date": "2023-10-26T10:15:00Z",
            "verified_purchase": False,
            "product_title": "Example Product B",
            "product_category": "Home Goods"
        }
    ]
    return mock_reviews

def lambda_handler(event, context):
    # In a real system, 'last_ingested_timestamp' might be stored in DynamoDB
    # or retrieved from Kinesis stream itself for deduplication/continuation.
    # For this MVP, we'll fetch mock data.
    new_reviews = get_amazon_reviews()

    records_to_put = []
    for review in new_reviews:
        review['ingestion_timestamp'] = datetime.utcnow().isoformat() + "Z"
        records_to_put.append({
            'Data': json.dumps(review).encode('utf-8'),
            'PartitionKey': review['product_id'] # Or customer_id, for even distribution
        })

    if records_to_put:
        try:
            response = kinesis_client.put_records(
                Records=records_to_put,
                StreamName=STREAM_NAME
            )
            print(f"Successfully put {len(records_to_put)} records to Kinesis. Response: {response}")
            # Handle failed records if any
            if response.get('FailedRecordCount', 0) > 0:
                print(f"Warning: Failed to put {response['FailedRecordCount']} records.")
        except Exception as e:
            print(f"Error putting records to Kinesis: {e}")
            raise e

    return {
        'statusCode': 200,
        'body': json.dumps(f'Processed {len(new_reviews)} reviews.')
    }
