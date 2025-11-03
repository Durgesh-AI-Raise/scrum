
import json
import os
import boto3
import base64

# Assuming a function for storage will be available (from Task 1.4)
# from . import storage_handler # This would be in a separate file/module

def validate_review_data(record_data):
    """
    Performs basic validation on the incoming review data.
    Returns True if valid, False otherwise.
    """
    required_fields = ["reviewId", "productId", "reviewerId", "rating", "reviewText", "reviewDate"]
    if not all(field in record_data for field in required_fields):
        print(f"Validation failed: Missing required fields in {record_data}")
        return False
    
    # Basic type checking
    if not isinstance(record_data.get("rating"), int):
        print(f"Validation failed: 'rating' is not an integer in {record_data}")
        return False
    if not (1 <= record_data.get("rating") <= 5):
        print(f"Validation failed: 'rating' is out of range (1-5) in {record_data}")
        return False

    # Further validation (e.g., date format, string length) can be added
    return True

def lambda_handler(event, context):
    """
    AWS Lambda function handler for consuming Kinesis records.
    """
    processed_records = []
    failed_records = []

    for record in event['Records']:
        # Kinesis data is base64 encoded
        payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
        try:
            review_data = json.loads(payload)
            
            if validate_review_data(review_data):
                # In a real scenario, this would call a storage layer/function
                # For now, just simulate processing
                print(f"Successfully processed and validated review: {review_data['reviewId']}")
                processed_records.append(review_data)
                
                # Placeholder for actual storage call from Task 1.4
                # storage_handler.store_review(review_data) 
            else:
                print(f"Failed validation for record: {payload}")
                failed_records.append(payload)

        except json.JSONDecodeError as e:
            print(f"JSON Decode Error for record: {payload}. Error: {e}")
            failed_records.append(payload)
        except Exception as e:
            print(f"An unexpected error occurred for record: {payload}. Error: {e}")
            failed_records.append(payload)
    
    # For demonstration, print counts. In production, metrics/logging would be used.
    print(f"Total records processed: {len(processed_records)}")
    print(f"Total records failed: {len(failed_records)}")

    # Depending on requirements, could return specific error responses for Kinesis retry
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Processing complete', 'failed_count': len(failed_records)})
    }
