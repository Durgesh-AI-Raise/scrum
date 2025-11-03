import json
import boto3
import datetime
import uuid
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def send_review_to_kinesis(review_data):
    kinesis_client = boto3.client('kinesis', region_name='us-east-1') # Example region
    try:
        # Ensure Data is a string
        payload = json.dumps(review_data)
        response = kinesis_client.put_record(
            StreamName='ReviewIngestionStream',
            Data=payload,
            PartitionKey=str(review_data['reviewId']) # Use reviewId for partitioning
        )
        logger.info(f"Successfully sent record: {response}")
        return True
    except Exception as e:
        logger.error(f"Error sending record to Kinesis: {e}", exc_info=True)
        return False

# Example usage (uncomment to test):
# review = {
#     "reviewId": str(uuid.uuid4()),
#     "productId": "B00XXXXXXX",
#     "reviewerId": "R1XXXXXXXXX",
#     "timestamp": datetime.datetime.utcnow().isoformat(),
#     "rating": 5,
#     "title": "Great Product!",
#     "content": "This product is amazing and works perfectly.",
#     "sourceIp": "203.0.113.45",
#     "country": "US"
# }
# send_review_to_kinesis(review)
