import json
import os
import boto3
import base64
from datetime import datetime
from botocore.exceptions import ClientError

# Initialize AWS clients
kinesis_client = boto3.client('kinesis')
dynamodb_client = boto3.client('dynamodb')

# Environment variables (to be set in Lambda configuration)
PROCESSED_STREAM_NAME = os.environ.get('PROCESSED_STREAM_NAME', 'aris-processed-reviews')
REVIEWS_TABLE_NAME = os.environ.get('REVIEWS_TABLE_NAME', 'aris-all-reviews')

# For MVP, a simple mapping for product category. In a real system, this would be a lookup service.
PRODUCT_CATEGORY_MAP = {
    "p67890": "Electronics",
    "p11223": "Books",
    "p44556": "Home & Kitchen",
    # Add more product-to-category mappings
}

def get_product_category(product_id):
    """
    Placeholder for a function to get product category.
    In a real system, this would query a product catalog service.
    """
    return PRODUCT_CATEGORY_MAP.get(product_id, "UNKNOWN")

def lambda_handler(event, context):
    records_to_put_kinesis = []
    processed_count = 0

    for record in event['Records']:
        try:
            # Kinesis data is base64 encoded
            payload_str = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            payload = json.loads(payload_str)

            # Basic validation
            required_keys = ['reviewId', 'productId', 'reviewerId', 'reviewText', 'rating', 'reviewDate', 'marketplace']
            if not all(k in payload for k in required_keys):
                print(f"Skipping invalid review (missing required keys): {payload_str}")
                continue

            # Enrich with productCategory (MVP: simple lookup)
            payload['productCategory'] = get_product_category(payload['productId'])
            payload['processedTimestamp'] = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'

            # Initialize flags and scores for DynamoDB
            payload['isFlagged'] = False
            payload['abuseScore'] = 0.0
            payload['flagDetails'] = []

            # Prepare item for DynamoDB (DynamoDB-specific types)
            item_for_dynamodb = {
                'reviewId': {'S': payload['reviewId']},
                'productId': {'S': payload['productId']},
                'reviewerId': {'S': payload['reviewerId']},
                'reviewText': {'S': payload['reviewText']},
                'rating': {'N': str(payload['rating'])},
                'reviewDate': {'S': payload['reviewDate']},
                'marketplace': {'S': payload['marketplace']},
                'productCategory': {'S': payload['productCategory']},
                'processedTimestamp': {'S': payload['processedTimestamp']},
                'isFlagged': {'BOOL': payload['isFlagged']},
                'abuseScore': {'N': str(payload['abuseScore'])},
                'flagDetails': {'L': []} # Empty list for initial state
            }

            # 1. Write to DynamoDB (aris-all-reviews)
            try:
                dynamodb_client.put_item(
                    TableName=REVIEWS_TABLE_NAME,
                    Item=item_for_dynamodb
                )
                print(f"Successfully stored review {payload['reviewId']} in DynamoDB.")
            except ClientError as e:
                print(f"Error storing review {payload['reviewId']} in DynamoDB: {e}")
                continue # Skip to next record if DynamoDB write fails

            # 2. Prepare for pushing to processed Kinesis stream
            records_to_put_kinesis.append({
                'Data': json.dumps(payload),
                'PartitionKey': payload['reviewId'] # Use reviewId for partitioning
            })
            processed_count += 1

        except json.JSONDecodeError as e:
            print(f"Skipping malformed JSON record: {record['kinesis']['data']}, Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred processing record: {e}, Record: {record.get('kinesis', {}).get('data', 'N/A')}")

    # 3. Publish to processed Kinesis stream (batch operation)
    if records_to_put_kinesis:
        try:
            response = kinesis_client.put_records(
                Records=records_to_put_kinesis,
                StreamName=PROCESSED_STREAM_NAME
            )
            print(f"Successfully put {len(records_to_put_kinesis)} records to {PROCESSED_STREAM_NAME}.")
            # Check for failed records within the batch
            if response.get('FailedRecordCount', 0) > 0:
                print(f"Warning: {response['FailedRecordCount']} records failed to put to Kinesis.")
        except ClientError as e:
            print(f"Error putting records to Kinesis stream {PROCESSED_STREAM_NAME}: {e}")
    else:
        print("No valid records to put to processed Kinesis stream.")

    return {'statusCode': 200, 'body': f'Processed {processed_count} Kinesis records.'}