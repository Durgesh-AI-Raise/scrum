import json
import boto3
import time
import uuid

kinesis_client = boto3.client('kinesis')
STREAM_NAME = 'amazon-review-raw-stream'

def send_review_to_kinesis(review_data):
    try:
        # Ensure review_id is present and unique
        if "review_id" not in review_data:
            review_data["review_id"] = str(uuid.uuid4())
        
        response = kinesis_client.put_record(
            StreamName=STREAM_NAME,
            Data=json.dumps(review_data),
            PartitionKey=review_data['review_id'] # Use review_id for even distribution
        )
        print(f"Successfully sent review {review_data['review_id']} to Kinesis.")
    except Exception as e:
        print(f"Error sending record to Kinesis: {e}")

if __name__ == "__main__":
    sample_review = {
        "product_id": "B08PV7T29W",
        "reviewer_id": "ABCDEFG",
        "marketplace": "US",
        "review_title": "Great Product!",
        "review_text": "This is an amazing product. Highly recommend it.",
        "overall_rating": 5,
        "verified_purchase": True,
        "review_timestamp": int(time.time()),
        "image_urls": [],
        "video_urls": [],
        "helpful_votes": 0
    }
    send_review_to_kinesis(sample_review)