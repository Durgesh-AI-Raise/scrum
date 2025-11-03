# US1: Real-time Review Data Ingestion Architecture

## Implementation Plan:
1.  **Architecture Design:** Hybrid ingestion (streaming for real-time, batch for historical/bulk).
2.  **Data Connector Implementation:** Develop a service/lambda to pull Amazon review data (API/file feed).
3.  **Data Storage Setup:** Provision a NoSQL database (e.g., AWS DynamoDB) for raw reviews.
4.  **Parsing & Validation:** Implement a service to parse, validate, and structure review data from the stream.
5.  **Testing:** Unit and integration tests for all components.

## Data Models:

### `RawReview` (NoSQL Document/Item)
```json
{
    "reviewId": "STRING (PK)",
    "productId": "STRING",
    "reviewerId": "STRING",
    "reviewText": "STRING",
    "overallRating": "NUMBER (1-5)",
    "reviewTime": "TIMESTAMP",
    "verifiedPurchase": "BOOLEAN",
    "title": "STRING",
    "imageUrl": "LIST<STRING>",
    "source": "STRING (e.g., 'amazon')",
    "ingestionTimestamp": "TIMESTAMP"
}
```

## Architecture Diagram:
```mermaid
graph TD
    A[Amazon Review Feed] --> B{Ingestion Service};
    B --&gt;|Real-time| C[Kinesis/Kafka Stream];
    B --&gt;|Batch/Historical| C;
    C --> D[Processing Service (Parsing & Validation)];
    D --> E[NoSQL DB (Raw Reviews)];
```

## Assumptions & Technical Decisions:
*   **Assumption:** Access to Amazon review data is available via an authorized API or S3 data dump.
*   **Decision:** Use AWS Kinesis Data Streams for real-time ingestion.
*   **Decision:** Use AWS DynamoDB for raw review storage due to its serverless nature, high throughput, and flexible schema.
*   **Decision:** Python will be the primary language for Lambda functions and processing services.

## Code Snippets (Conceptual Python Pseudocode):

### `amazon_connector.py` (Lambda for data pulling and pushing to Kinesis)
```python
import json
import boto3
import datetime

kinesis_client = boto3.client('kinesis')
STREAM_NAME = 'review-ingestion-stream'

def get_amazon_reviews_data():
    """
    Simulates fetching new Amazon review data from an API or file feed.
    """
    sample_review = {
        "reviewId": "R1ABCDEFGH12345",
        "productId": "B07XXXXXXX",
        "reviewerId": "A1B2C3D4E5F6G7H8",
        "reviewText": "This product is absolutely amazing! Highly recommend.",
        "overallRating": 5,
        "reviewTime": "2023-10-26T10:00:00Z",
        "verifiedPurchase": True,
        "title": "Fantastic Product!",
        "imageUrl": ["http://example.com/image1.jpg"],
        "source": "amazon"
    }
    return [sample_review] # In reality, a list of many reviews

def put_record_to_kinesis(record_data):
    """
    Puts a single record into the Kinesis Data Stream.
    """
    partition_key = record_data.get('reviewId', 'default_partition_key')
    kinesis_client.put_record(
        StreamName=STREAM_NAME,
        Data=json.dumps(record_data),
        PartitionKey=partition_key
    )
    print(f"Pushed review {partition_key} to Kinesis.")

def handler(event, context):
    """
    Lambda handler to fetch and ingest reviews.
    Triggered periodically or by new file uploads (S3 event).
    """
    reviews = get_amazon_reviews_data()
    for review in reviews:
        review['ingestionTimestamp'] = datetime.datetime.utcnow().isoformat() + 'Z'
        put_record_to_kinesis(review)
    return {
        'statusCode': 200,
        'body': f'{len(reviews)} reviews processed and pushed to Kinesis.'
    }
```

### `review_processor.py` (Lambda for Kinesis Consumer, Parsing & Validation)
```python
import json
import boto3
import datetime
import base64

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('RawReviewsTable')

def parse_and_validate_review(raw_review_data):
    """
    Parses and performs basic validation on a raw review.
    Returns a validated dictionary or raises an error.
    """
    parsed_review = json.loads(raw_review_data)

    required_fields = ["reviewId", "productId", "reviewerId", "reviewText", "overallRating", "reviewTime", "source"]
    for field in required_fields:
        if field not in parsed_review or not parsed_review[field]:
            raise ValueError(f"Missing or empty required field: {field}")

    if not isinstance(parsed_review.get("overallRating"), (int, float)) or not (1 <= parsed_review["overallRating"] <= 5):
        raise ValueError("overallRating must be a number between 1 and 5.")

    if 'reviewTime' in parsed_review:
        try:
            if isinstance(parsed_review['reviewTime'], str):
                dt_obj = datetime.datetime.fromisoformat(parsed_review['reviewTime'].replace('Z', '+00:00'))
                parsed_review['reviewTime'] = dt_obj.isoformat(timespec='seconds') + 'Z'
        except ValueError:
            print(f"Warning: Could not parse reviewTime for {parsed_review.get('reviewId')}. Keeping as is.")

    parsed_review.setdefault('verifiedPurchase', False)
    
    return parsed_review

def store_review_in_db(review_data):
    """
    Stores a validated review in the DynamoDB table.
    """
    table.put_item(Item=review_data)
    print(f"Stored review {review_data['reviewId']} in DynamoDB.")

def handler(event, context):
    """
    Lambda handler for Kinesis stream processing.
    Processes batches of records from the stream.
    """
    for record in event['Records']:
        payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
        try:
            validated_review = parse_and_validate_review(payload)
            store_review_in_db(validated_review)
        except ValueError as e:
            print(f"Validation error for record: {payload}. Error: {e}")
        except Exception as e:
            print(f"Error processing record {payload}: {e}")
    return {'statusCode': 200, 'body': 'Records processed.'}
```
