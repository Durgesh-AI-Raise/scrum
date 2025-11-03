import json
import os
import boto3
from datetime import datetime
import base64

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('REVIEWS_TABLE_NAME', 'ReviewsTable')
reviews_table = dynamodb.Table(table_name)
kinesis_client = boto3.client('kinesis')
detection_stream_name = os.environ.get('DETECTION_STREAM_NAME', 'DetectionStream')

def validate_review(review):
    """Performs basic validation on review data."""
    required_fields = ['reviewId', 'productId', 'userId', 'reviewText', 'rating', 'reviewDate']
    for field in required_fields:
        if field not in review or not review[field]:
            return False, f"Missing or empty required field: {field}"

    if not isinstance(review['rating'], (int, float)) or not (1 <= review['rating'] <= 5):
        return False, "Rating must be a number between 1 and 5."
    
    # Basic date format check (can be more robust)
    try:
        datetime.fromisoformat(review['reviewDate'].replace('Z', '+00:00'))
    except ValueError:
        return False, "reviewDate is not in valid ISO 8601 format."

    return True, ""

def lambda_handler(event, context):
    processed_count = 0
    failed_count = 0
    for record in event['Records']:
        payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
        review_data = None
        try:
            review_data = json.loads(payload)
            
            is_valid, error_message = validate_review(review_data)
            if not is_valid:
                print(f"Validation failed for review {review_data.get('reviewId', 'N/A')}: {error_message}")
                failed_count += 1
                continue

            review_data['ingestionTimestamp'] = datetime.utcnow().isoformat() + 'Z'
            
            # Initialize detection related fields if not present
            review_data.setdefault('flagged', False)
            review_data.setdefault('isFlagged', 'FALSE') # For GSI
            review_data.setdefault('detectionReasons', [])
            review_data.setdefault('confidenceScore', 0)
            review_data.setdefault('manualFlagged', False) # For manual flagging

            # Use ConditionExpression for atomic uniqueness check for reviewId
            reviews_table.put_item(
                Item=review_data,
                ConditionExpression='attribute_not_exists(reviewId)'
            )
            print(f"Successfully ingested and validated review: {review_data.get('reviewId')}")
            
            # Push the validated review to the DetectionStream for further processing
            kinesis_client.put_record(
                StreamName=detection_stream_name,
                Data=json.dumps(review_data),
                PartitionKey=review_data['reviewId'] # Use reviewId as partition key
            )
            print(f"Pushed review {review_data.get('reviewId')} to {detection_stream_name}")
            processed_count += 1

        except reviews_table.exceptions.ConditionalCheckFailedException:
            print(f"Duplicate reviewId found, skipping ingestion: {review_data.get('reviewId')}")
            failed_count += 1
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON payload: {e}. Payload: {payload}")
            failed_count += 1
        except Exception as e:
            print(f"Unhandled error processing record: {e}. Payload: {payload}")
            failed_count += 1

    return {
        'statusCode': 200,
        'body': f'Processed {processed_count} records, {failed_count} failed validations/ingestion.'
    }
