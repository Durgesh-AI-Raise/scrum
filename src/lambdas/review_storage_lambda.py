
import json
import boto3
import base64
import datetime

dynamodb = boto3.client('dynamodb', region_name='us-east-1')
reviews_table_name = 'Reviews' # Ensure this table is created in DynamoDB

def lambda_handler(event, context):
    """
    AWS Lambda function to consume records from a Kinesis Data Stream
    and store them into a DynamoDB table.
    This function also initializes fields for abuse detection and moderation.
    """
    print(f"Received {len(event['Records'])} records from Kinesis.")
    processed_count = 0
    
    for record in event['Records']:
        try:
            # Kinesis data is base64 encoded
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            review_data = json.loads(payload)

            # Add foundational fields for abuse detection and moderation workflow
            # These will be updated by subsequent detection steps (e.g., keyword, high-volume)
            review_data['isFlagged'] = False
            review_data['flaggedReasons'] = [] # Store reasons as a list of strings
            review_data['detectionTimestamp'] = None # Timestamp when abuse was first detected
            review_data['moderationStatus'] = 'PENDING_REVIEW' # Initial status for all reviews

            # Prepare item for DynamoDB put_item
            dynamodb_item = {
                'reviewId': {'S': review_data['reviewId']},
                'productId': {'S': review_data['productId']},
                'reviewerId': {'S': review_data['reviewerId']},
                'rating': {'N': str(review_data['rating'])}, # Store rating as Number type
                'title': {'S': review_data['title']},
                'content': {'S': review_data['content']},
                'reviewDate': {'S': review_data['reviewDate']},
                'ipAddress': {'S': review_data.get('ipAddress', 'N/A')}, # Use .get() for optional fields
                'source': {'S': review_data.get('source', 'Amazon.com')},
                'isFlagged': {'BOOL': review_data['isFlagged']},
                'moderationStatus': {'S': review_data['moderationStatus']}
            }
            
            # DynamoDB cannot store empty lists for 'L' type if not present.
            # Add 'flaggedReasons' only if it has elements.
            if review_data['flaggedReasons']:
                dynamodb_item['flaggedReasons'] = {'L': [{'S': r} for r in review_data['flaggedReasons']]}

            # Add 'detectionTimestamp' only if it's not None.
            if review_data['detectionTimestamp'] is not None:
                dynamodb_item['detectionTimestamp'] = {'S': review_data['detectionTimestamp']}
            else:
                dynamodb_item['detectionTimestamp'] = {'NULL': True} # Explicitly set NULL if not present

            dynamodb.put_item(
                TableName=reviews_table_name,
                Item=dynamodb_item
            )
            print(f"Successfully stored review {review_data['reviewId']} in DynamoDB.")
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing record: {e}. Record data: {record.get('kinesis', {}).get('data', '')}")
            # Re-raise the exception to allow Kinesis to retry the batch
            raise

    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully processed {processed_count} records.')
    }

# IAM Permissions required for this Lambda:
# - kinesis:GetRecords, kinesis:GetShardIterator, kinesis:DescribeStream (for reading from Kinesis)
# - dynamodb:PutItem (for writing to DynamoDB)

# DynamoDB Table 'Reviews' Configuration:
# - Primary Key: reviewId (String)
# - Global Secondary Indexes (GSIs) recommended:
#   - reviewerId-reviewDate-index: Partition Key: reviewerId (String), Sort Key: reviewDate (String)
#   - productId-reviewDate-index: Partition Key: productId (String), Sort Key: reviewDate (String)
#   - isFlagged-detectionTimestamp-index: Partition Key: isFlagged (Boolean), Sort Key: detectionTimestamp (String)
