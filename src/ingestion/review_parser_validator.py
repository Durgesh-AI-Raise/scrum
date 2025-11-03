
import json
import os
import base64
from datetime import datetime
import boto3

# Kinesis client
kinesis_client = boto3.client('kinesis')

# Environment variables
VALIDATED_REVIEWS_STREAM_NAME = os.environ.get('VALIDATED_REVIEWS_STREAM_NAME', 'ValidatedReviewsStream')

def validate_review(review):
    """
    Performs basic validation on a review record.
    Returns (is_valid: boolean, errors: list of strings).
    """
    errors = []

    # Required fields check
    required_fields = ["review_id", "product_id", "reviewer_id", "stars", "review_text", "review_date", "extracted_at"]
    for field in required_fields:
        if field not in review or not review[field]:
            errors.append(f"Missing or empty required field: {field}")

    # Stars validation
    if "stars" in review:
        try:
            stars = int(review["stars"])
            if not (1 <= stars <= 5):
                errors.append("Field 'stars' must be an integer between 1 and 5.")
        except (ValueError, TypeError):
            errors.append("Field 'stars' must be an integer.")
    
    # Review Date validation
    if "review_date" in review and review["review_date"]:
        try:
            # Attempt to parse date to ensure it's a valid format
            datetime.strptime(review["review_date"], "%Y-%m-%d")
        except ValueError:
            errors.append("Field 'review_date' must be in YYYY-MM-DD format.")
            
    # Extracted At validation
    if "extracted_at" in review and review["extracted_at"]:
        try:
            # Attempt to parse ISO timestamp
            datetime.fromisoformat(review["extracted_at"].replace('Z', '+00:00'))
        except ValueError:
            errors.append("Field 'extracted_at' must be in ISO 8601 format.")


    return len(errors) == 0, errors

def parse_and_enrich_review(review):
    """
    Parses and enriches the review data, converting types where necessary.
    """
    parsed_review = review.copy() # Create a mutable copy

    # Convert stars to integer
    if "stars" in parsed_review and isinstance(parsed_review["stars"], (str, int)):
        try:
            parsed_review["stars"] = int(parsed_review["stars"])
        except (ValueError, TypeError):
            pass # Validation will catch this, keep original for error reporting

    # Convert review_date to a standardized date format (or keep as string if invalid)
    if "review_date" in parsed_review and isinstance(parsed_review["review_date"], str):
        try:
            parsed_review["review_date"] = datetime.strptime(parsed_review["review_date"], "%Y-%m-%d").date().isoformat()
        except ValueError:
            pass # Validation will catch this

    # Convert extracted_at to timestamp (or keep as string if invalid)
    if "extracted_at" in parsed_review and isinstance(parsed_review["extracted_at"], str):
        try:
            parsed_review["extracted_at"] = datetime.fromisoformat(parsed_review["extracted_at"].replace('Z', '+00:00')).isoformat(timespec='milliseconds') + 'Z'
        except ValueError:
            pass # Validation will catch this

    return parsed_review


def lambda_handler(event, context):
    output_records = []

    for record in event['Records']:
        # Kinesis data is base64 encoded
        payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
        
        try:
            raw_review = json.loads(payload)
            print(f"Processing review_id: {raw_review.get('review_id', 'N/A')}")

            is_valid, errors = validate_review(raw_review)
            
            # Parse and enrich even if invalid, to standardize structure
            processed_review = parse_and_enrich_review(raw_review)
            
            processed_review["is_valid"] = is_valid
            processed_review["validation_errors"] = errors

            output_records.append({
                'Data': json.dumps(processed_review),
                'PartitionKey': processed_review.get('product_id', 'unknown_product') 
            })

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Kinesis record: {payload}. Error: {e}")
            # Optionally, send malformed JSON to a dead-letter queue or log more explicitly
        except Exception as e:
            print(f"An unexpected error occurred while processing record: {payload}. Error: {e}")
            # Depending on the error, could re-raise or send to dead-letter

    if output_records:
        try:
            kinesis_client.put_records(
                Records=output_records,
                StreamName=VALIDATED_REVIEWS_STREAM_NAME
            )
            print(f"Successfully put {len(output_records)} records to {VALIDATED_REVIEWS_STREAM_NAME}")
        except Exception as e:
            print(f"Error putting records to Kinesis stream {VALIDATED_REVIEWS_STREAM_NAME}: {e}")
            # Potentially implement retry logic or alert
            raise e # Re-raise to indicate failure to Kinesis, which will retry the batch

    return {'statusCode': 200, 'body': f'Processed {len(event["Records"])} records.'}
