import json
import os
import boto3
import base64
from datetime import datetime, timedelta

# Environment variables for configuration
KINESIS_STREAM_NAME = os.environ.get("KINESIS_STREAM_NAME", "ARIS_ReviewStream")
kinesis_client = boto3.client("kinesis")

def lambda_handler(event, context):
    """
    Handles incoming review data, performs basic validation, and pushes to Kinesis.
    Event structure is assumed to be a dictionary with a 'reviews' key (list of review dicts)
    or a single review dictionary directly.
    """
    records_to_put = []
    
    # Adapt to various potential input event structures (e.g., single record vs batch)
    reviews_payload = event.get("reviews", []) 
    if not reviews_payload and isinstance(event, dict) and "review_id" in event:
        reviews_payload = [event] # Handle a single review directly if not in a 'reviews' list

    for review in reviews_payload:
        # Basic input validation: check for essential fields
        if not all(key in review for key in ["review_id", "product_id", "user_id", "rating", "review_text"]):
            print(f"Skipping invalid review due to missing essential fields: {review.get('review_id', 'N/A')}")
            continue
        
        # Standardize date formats if present, add current time if missing for processing
        if "review_date" not in review:
            review["review_date"] = datetime.utcnow().isoformat() + "Z"
        if "account_creation_date" not in review:
             # For new accounts without creation date, assume recent (e.g., for testing new account rules)
             review["account_creation_date"] = (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z" 
        
        # Use product_id as PartitionKey for Kinesis to ensure related reviews go to the same shard
        # This can be beneficial for future stateful processing needs.
        partition_key = review.get("product_id", "default_partition_key") 
        
        records_to_put.append({
            "Data": json.dumps(review).encode("utf-8"), # Kinesis Data must be bytes
            "PartitionKey": partition_key
        })

    if records_to_put:
        try:
            # put_records supports sending multiple records in one API call
            response = kinesis_client.put_records(
                Records=records_to_put,
                StreamName=KINESIS_STREAM_NAME
            )
            print(f"Successfully put {len(records_to_put)} records to Kinesis. Response: {response}")
            
            # Handle potential partial failures (e.g., throttling on specific shards)
            if response.get("FailedRecordCount", 0) > 0:
                print(f"Warning: {response['FailedRecordCount']} records failed to put to Kinesis.")
                # Detailed logging of failed records for debugging/retries in a real system
            
            return {
                "statusCode": 200,
                "body": json.dumps({"message": f"Processed {len(reviews_payload)} reviews. Put {len(records_to_put)} to Kinesis."}) 
            }
        except Exception as e:
            print(f"Error putting records to Kinesis: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"message": f"Error putting records to Kinesis: {str(e)}"})
            }
    else:
        print("No valid records received to put to Kinesis.")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No valid reviews received."})
        }
