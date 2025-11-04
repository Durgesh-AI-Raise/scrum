
import boto3
import json
import time
from datetime import datetime

kinesis_client = boto3.client('kinesis', region_name='us-east-1') # Assuming us-east-1
STREAM_NAME = 'aris-raw-review-data-stream'

def send_review_to_kinesis(review_data):
    """Sends a single review record to the Kinesis Data Stream."""
    try:
        # Ensure review_data contains a reviewId for partitioning
        if 'reviewId' not in review_data:
            raise ValueError("Review data must contain 'reviewId' for partitioning.")

        response = kinesis_client.put_record(
            StreamName=STREAM_NAME,
            Data=json.dumps(review_data),
            PartitionKey=review_data['reviewId'] # Use reviewId for partitioning
        )
        print(f"Successfully sent review {review_data['reviewId']} to Kinesis. ShardId: {response['ShardId']}")
        return response
    except Exception as e:
        print(f"Error sending review to Kinesis: {e}")
        return None

# Example Usage (uncomment to run in a test environment):
# if __name__ == "__main__":
#     sample_review_1 = {
#         "reviewId": "R1234567890ABCDEF",
#         "productId": "B07XXXXXXX",
#         "userId": "U0987654321ZYXWVU",
#         "starRating": 4,
#         "reviewTitle": "Good, but could be better",
#         "reviewText": "The product works as advertised, but the battery life is a bit short. Delivery was fast.",
#         "reviewDate": datetime.now().isoformat() + "Z",
#         "helpfulVotes": 5,
#         "totalVotes": 7,
#         "verifiedPurchase": True,
#         "productCategory": "Electronics",
#         "reviewerAccountAgeDays": 730,
#         "ipAddress": "203.0.113.45",
#         "deviceType": "Android"
#     }
#     send_review_to_kinesis(sample_review_1)
#
#     sample_review_2 = {
#         "reviewId": "R987654321FEDCBA",
#         "productId": "B01YYYYYYY",
#         "userId": "U1122334455ABCDEF",
#         "starRating": 5,
#         "reviewTitle": "Absolutely amazing!",
#         "reviewText": "This is the best product I've ever bought. Highly recommend to everyone!",
#         "reviewDate": datetime.now().isoformat() + "Z",
#         "helpfulVotes": 100,
#         "totalVotes": 100,
#         "verifiedPurchase": False, # Suspicious detail
#         "productCategory": "Home & Kitchen",
#         "reviewerAccountAgeDays": 10, # Suspicious detail
#         "ipAddress": "198.51.100.10",
#         "deviceType": "Web"
#     }
#     send_review_to_kinesis(sample_review_2)
