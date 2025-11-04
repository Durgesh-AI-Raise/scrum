import json
import base64
import os
from datetime import datetime
import boto3

# Initialize DynamoDB client outside the handler for better performance
# The table name will be passed as an environment variable
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'amazon-reviews-raw')
dynamodb_table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    print(f"Received {len(event['Records'])} records from Kinesis.")

    records_to_process = []
    for record in event['Records']:
        try:
            # Kinesis data is base64 encoded and then UTF-8 decoded
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            review_data = json.loads(payload)

            # Add ingestion timestamp
            review_data['ingestion_timestamp'] = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
            records_to_process.append(review_data)
        except Exception as e:
            print(f"Error parsing Kinesis record: {e}. Record data: {record.get('kinesis', {}).get('data')}")
            # Log and skip to avoid failing the entire batch for one bad record
            continue

    if not records_to_process:
        print("No valid records to process.")
        return {
            'statusCode': 200,
            'body': json.dumps('No valid records processed.')
        }

    # Use batch_writer for efficient storage
    # This will automatically handle retries for transient errors
    with dynamodb_table.batch_writer() as batch:
        for review_item in records_to_process:
            try:
                batch.put_item(Item=review_item)
                print(f"Successfully prepared review {review_item.get('review_id')} for batch write.")
            except Exception as e:
                print(f"Error preparing review {review_item.get('review_id')} for batch write: {e}")
                # Log the error. If a DLQ is configured, this record will eventually go there
                # if the Lambda invocation fails after retries due to this item.
                # For batch_writer, individual item failures within the batch are not directly exposed,
                # but the overall batch operation will retry if there are unprocessable items.
                pass # Continue processing other items in the batch

    print(f"Successfully processed and stored {len(records_to_process)} reviews.")

    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully processed {len(records_to_process)} Kinesis records.')
    }
