import json
import os
import datetime

# Mock SQS client
class MockSQSClient:
    def send_message(self, QueueUrl, MessageBody):
        print(f"Sending message to SQS QueueUrl: {QueueUrl}")
        print(f"MessageBody: {MessageBody}")
        return {"MessageId": "mock-message-id-123"}

# Mock data source function
def fetch_raw_review_data():
    # In a real scenario, this would connect to a data lake, database, or streaming service
    return [
        {
            "id": "R123",
            "productId": "P001",
            "reviewerId": "U987",
            "text": "This product is absolutely amazing! Highly recommend.",
            "stars": 5,
            "date": "2023-10-26T10:00:00Z"
        },
        {
            "id": "R124",
            "productId": "P002",
            "reviewerId": "U988",
            "text": "Worst purchase ever. A complete scam.",
            "stars": 1,
            "date": "2023-10-26T10:05:00Z"
        }
    ]

def lambda_handler(event, context):
    sqs_client = MockSQSClient() # In a real scenario: boto3.client('sqs')
    sqs_queue_url = os.environ.get('SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/aris-review-ingestion-queue')

    raw_reviews = fetch_raw_review_data()
    processed_count = 0

    for review in raw_reviews:
        try:
            # Basic transformation and standardization
            processed_review = {
                "review_id": review["id"],
                "product_id": review["productId"],
                "reviewer_id": review["reviewerId"],
                "review_text": review["text"],
                "rating": review["stars"],
                "review_date": datetime.datetime.fromisoformat(review["date"].replace('Z', '+00:00')).isoformat(),
                "source_system": "mock_source",
                "ingestion_timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
            sqs_client.send_message(
                QueueUrl=sqs_queue_url,
                MessageBody=json.dumps(processed_review)
            )
            processed_count += 1
        except Exception as e:
            print(f"Error processing review {review.get('id', 'N/A')}: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully ingested {processed_count} reviews.')
    }

# Example of how the lambda_handler would be invoked (for local testing)
if __name__ == '__main__':
    lambda_handler(None, None)