# filename: src/api_endpoints/review_producer.py
import json
import os
import boto3
from datetime import datetime

KINESIS_STREAM_NAME = os.environ.get('KINESIS_STREAM_NAME', 'amazon-review-stream')
kinesis_client = boto3.client('kinesis')

def handler(event, context):
    """
    AWS Lambda handler to receive review data via API Gateway and push it to Kinesis.
    """
    try:
        body = json.loads(event['body'])

        # Add ingestion timestamp
        body['ingestion_timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Validate essential fields (basic validation)
        required_fields = ['id', 'product_id', 'reviewer_id', 'rating', 'text_content', 'review_date']
        if not all(field in body for field in required_fields):
            print(f"WARNING: Missing required fields in request: {body}")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Missing required fields'})
            }

        # Push to Kinesis
        response = kinesis_client.put_record(
            StreamName=KINESIS_STREAM_NAME,
            Data=json.dumps(body),
            PartitionKey=body['product_id'] # Use product_id for partitioning
        )
        print(f"INFO: Successfully put record to Kinesis, SequenceNumber: {response['SequenceNumber']} for review_id: {body['id']}")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Review ingested successfully', 'review_id': body['id']})
        }
    except json.JSONDecodeError as jde:
        print(f"ERROR: Invalid JSON body received: {event['body']}. Error: {jde}")
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid JSON body'})
        }
    except kinesis_client.exceptions.ClientError as kce:
        print(f"ERROR: Kinesis client error: {kce} for review_id: {body.get('id', 'N/A')}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Failed to send to Kinesis', 'error': str(kce)})
        }
    except Exception as e:
        print(f"CRITICAL ERROR: Unexpected error ingesting review: {e} for review_id: {body.get('id', 'N/A')}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }