import requests
import json
import os
import boto3
import datetime
import logging
import time

# Configure structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log_json(level, message, details=None):
    log_entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "level": level.upper(),
        "service": "api_ingester",
        "message": message,
    }
    if details:
        log_entry['details'] = details
    logger.info(json.dumps(log_entry))

KINESIS_STREAM_NAME = os.environ.get('KINESIS_STREAM_NAME', 'AmazonReviewStream')
AMAZON_API_BASE_URL = os.environ.get('AMAZON_API_BASE_URL', 'https://api.amazonreviews.com') # Hypothetical API
AMAZON_API_KEY = os.environ.get('AMAZON_API_KEY', 'your_api_key') # Replace with secure management (e.g., Secrets Manager)
API_DLQ_URL = os.environ.get('API_DLQ_URL') # SQS URL for API ingestion errors

kinesis_client = boto3.client('kinesis')
sqs_client = boto3.client('sqs') if API_DLQ_URL else None

def fetch_reviews_from_api(last_fetched_timestamp=None, next_token=None, retries=3):
    headers = {
        'Authorization': f'Bearer {AMAZON_API_KEY}',
        'Content-Type': 'application/json'
    }
    params = {
        'limit': 100, # Max reviews per page
        'sortBy': 'date_desc' # Assuming API supports this for fetching new reviews
    }
    if last_fetched_timestamp:
        params['since'] = last_fetched_timestamp # Hypothetical API parameter
    if next_token:
        params['nextToken'] = next_token

    for attempt in range(retries + 1):
        try:
            log_json("INFO", f"Attempting to fetch reviews from API (attempt {attempt + 1})", {"url": f"{AMAZON_API_BASE_URL}/reviews", "params": params})
            response = requests.get(f"{AMAZON_API_BASE_URL}/reviews", headers=headers, params=params, timeout=10)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            log_json("INFO", "API call successful", {"url": response.url, "status_code": response.status_code})
            return response.json()
        except requests.exceptions.HTTPError as e:
            if 400 <= e.response.status_code < 500 and e.response.status_code not in [429]: # Client error (e.g., 401, 403, 404), usually not retriable
                log_json("ERROR", "Client error from API, not retrying", {
                    "status_code": e.response.status_code, "response_text": e.response.text,
                    "url": e.request.url, "attempt": attempt + 1
                })
                break # Exit retry loop for unretriable errors
            log_json("WARN", "HTTP error from API, retrying", {
                "status_code": e.response.status_code, "response_text": e.response.text,
                "url": e.request.url, "attempt": attempt + 1
            })
        except requests.exceptions.RequestException as e: # Network error, connection timeout, etc.
            log_json("WARN", "Network or connection error, retrying", {
                "error": str(e), "url": f"{AMAZON_API_BASE_URL}/reviews", "attempt": attempt + 1
            })

        if attempt < retries:
            sleep_time = 2 ** attempt # Exponential backoff
            time.sleep(sleep_time)
    
    final_error_msg = f"API call failed after {retries + 1} attempts."
    log_json("ERROR", final_error_msg, {"url": f"{AMAZON_API_BASE_URL}/reviews", "params": params})
    if sqs_client and API_DLQ_URL:
        try:
            sqs_client.send_message(
                QueueUrl=API_DLQ_URL,
                MessageBody=json.dumps({
                    "failureReason": "API_CALL_FAILED_AFTER_RETRIES",
                    "requestDetails": {"url": f"{AMAZON_API_BASE_URL}/reviews", "params": params},
                    "errorMessage": final_error_msg,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                })
            )
            log_json("INFO", "Sent failed API request details to DLQ.", {"dlq_url": API_DLQ_URL})
        except Exception as sqs_e:
            log_json("ERROR", f"Failed to send message to DLQ: {sqs_e}", {"dlq_url": API_DLQ_URL})
    return None

def transform_and_publish_review(api_review_data):
    # Map API response to our internal Kinesis message model
    review_id = api_review_data.get('id')
    if not review_id:
        log_json("WARN", "Skipping review with no ID found", {"raw_data_preview": str(api_review_data)[:200]})
        return

    transformed_review = {
        "reviewId": review_id,
        "reviewerId": api_review_data.get('reviewer', {}).get('id'),
        "productASIN": api_review_data.get('product', {}).get('asin'),
        "timestamp": api_review_data.get('date'), # Assuming ISO 8601 format from API
        "reviewTitle": api_review_data.get('title'),
        "reviewText": api_review_data.get('text'),
        "rating": api_review_data.get('stars'),
        "purchaseVerificationStatus": api_review_data.get('verifiedPurchase'),
        "sourceSystem": "Amazon"
    }

    try:
        kinesis_client.put_record(
            StreamName=KINESIS_STREAM_NAME,
            Data=json.dumps(transformed_review),
            PartitionKey=transformed_review['productASIN'] # Use productASIN for even distribution across shards
        )
        log_json("INFO", "Published review to Kinesis", {"reviewId": transformed_review['reviewId']})
    except Exception as e:
        log_json("ERROR", f"Failed to publish review to Kinesis: {e}", {
            "reviewId": transformed_review.get('reviewId'),
            "error": str(e)
        })
        # Consider sending to a DLQ if Kinesis writes consistently fail, though Kinesis/Lambda often handle retries for these.

def lambda_handler(event, context):
    # In a real system, last_fetched_timestamp or next_token would be persisted (e.g., in S3, DynamoDB)
    # For this sprint, we'll simulate fetching from a starting point.
    # last_fetched_timestamp = get_last_timestamp_from_persistent_store()
    last_fetched_timestamp = None
    current_next_token = None
    has_more_pages = True
    processed_count = 0

    log_json("INFO", "API Ingestion Lambda triggered.")

    while has_more_pages:
        api_response = fetch_reviews_from_api(last_fetched_timestamp, current_next_token)
        if not api_response:
            log_json("ERROR", "No API response or API call failed, stopping ingestion for this run.")
            break

        reviews = api_response.get('reviews', [])
        if not reviews:
            log_json("INFO", "No new reviews found in this API page.", {"next_token": current_next_token})
            has_more_pages = False
            continue

        for review in reviews:
            transform_and_publish_review(review)
            processed_count += 1

        current_next_token = api_response.get('nextToken')
        if not current_next_token:
            has_more_pages = False
            log_json("INFO", "No further pages (nextToken) from API.")
        else:
            log_json("INFO", "Fetching next page of reviews.", {"next_token": current_next_token})
        
        # Prevent infinite loops in case API always returns a nextToken but no new data
        if processed_count >= 5000: # Arbitrary limit for a single Lambda invocation
            log_json("WARN", "Reached maximum reviews to process in single invocation, will continue on next trigger.")
            has_more_pages = False # Break to allow next Lambda invocation
            # update_last_timestamp_in_persistent_store(latest_timestamp_from_processed_reviews)

    log_json("INFO", f"Finished ingestion run. Total reviews processed: {processed_count}")
    # update_last_timestamp_in_persistent_store(...) # If we were tracking state

    return {
        'statusCode': 200,
        'body': json.dumps(f"Ingested {processed_count} reviews.")
    }