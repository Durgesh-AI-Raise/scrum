import boto3
import json
import datetime
import uuid
import random
import time

kinesis_client = boto3.client('kinesis', region_name='us-east-1') # Replace with your AWS region
stream_name = 'ReviewDataStream'

def generate_mock_review_data():
    """Generates a single mock review record conforming to the schema."""
    review_id = str(uuid.uuid4())
    product_id = f"PROD-{random.randint(1000, 9999)}"
    reviewer_id = f"REV-{random.randint(10000, 99999)}"
    rating = random.randint(1, 5)
    review_text = f"This is a mock review for product {product_id}. Rating: {rating} stars. Good product! {uuid.uuid4()}"
    review_date = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds') + 'Z'
    source = random.choice(['amazon', 'ebay', 'walmart'])

    review_data = {
        "reviewId": review_id,
        "productId": product_id,
        "reviewerId": reviewer_id,
        "rating": rating,
        "reviewText": review_text,
        "reviewDate": review_date,
        "source": source,
        "metadata": {
            "helpfulVotes": random.randint(0, 50),
            "isVerifiedPurchase": random.choice([True, False])
        }
    }
    return review_data

def put_record_to_kinesis(record):
    """Puts a single record into Kinesis Data Stream."""
    try:
        response = kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(record),
            PartitionKey=record['reviewerId'] # Use reviewerId for partitioning
        )
        print(f"Successfully put record {record['reviewId']} to Kinesis. ShardId: {response['ShardId']}")
    except Exception as e:
        print(f"Error putting record to Kinesis: {e}")

if __name__ == "__main__":
    print(f"Sending mock review data to Kinesis stream: {stream_name}")
    for i in range(10): # Send 10 mock reviews
        mock_review = generate_mock_review_data()
        put_record_to_kinesis(mock_review)
        time.sleep(1) # Wait a bit between records
    print("Finished sending mock review data.")
