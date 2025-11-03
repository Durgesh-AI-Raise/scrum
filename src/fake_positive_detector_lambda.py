import json
import os
import boto3
import base64
from datetime import datetime, timedelta

# Environment variables for configuration
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "ARIS_FlaggedReviews")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

ACCOUNT_CREATION_DATE_THRESHOLD_DAYS = 30 # For 'new account' rule
GENERIC_POSITIVE_KEYWORDS = ["great product", "love it", "highly recommend", "amazing", "fantastic", "best ever"]
REVIEW_TEXT_WORD_COUNT_THRESHOLD = 15 # For 'short review' rule

def is_new_account(account_creation_date_str, threshold_days):
    """Checks if an account was created within the last 'threshold_days'."""
    try:
        # Handle different ISO format variations, especially 'Z' for UTC
        creation_date = datetime.fromisoformat(account_creation_date_str.replace('Z', '+00:00'))
        # Compare with current UTC time
        return (datetime.now(creation_date.tzinfo) - creation_date).days < threshold_days
    except (ValueError, TypeError):
        print(f"Invalid account_creation_date format: {account_creation_date_str}")
        return False # Treat as not a new account if date is invalid

def contains_generic_positive_phrases(review_text, keywords):
    """Checks if review text contains generic positive phrases."""
    text_lower = review_text.lower()
    return any(keyword in text_lower for keyword in keywords)

def lambda_handler(event, context):
    """
    Processes Kinesis records to detect fake positive amplification patterns.
    """
    flagged_items = []
    
    for record in event["Records"]:
        try:
            # Kinesis data is base64 encoded
            payload = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            review = json.loads(payload)

            review_id = review.get("review_id")
            product_id = review.get("product_id")
            user_id = review.get("user_id")
            rating = review.get("rating")
            review_text = review.get("review_text", "")
            account_creation_date = review.get("account_creation_date")
            
            flagged = False
            detection_rules = []

            # --- Rule 1: New Account + High Rating (e.g., 5-star) ---
            if rating == 5 and account_creation_date and \
               is_new_account(account_creation_date, ACCOUNT_CREATION_DATE_THRESHOLD_DAYS):
                flagged = True
                detection_rules.append(f"Rule: New Account (<{ACCOUNT_CREATION_DATE_THRESHOLD_DAYS} days) + 5-star rating")

            # --- Rule 2: Short, Generic Positive Review from a New-ish Account ---
            # This rule aims to catch low-effort positive reviews often associated with manipulation.
            # We use a slightly broader window for 'new-ish' account here for potential overlap.
            if not flagged and rating == 5 and len(review_text.split()) < REVIEW_TEXT_WORD_COUNT_THRESHOLD and \
               contains_generic_positive_phrases(review_text, GENERIC_POSITIVE_KEYWORDS):
                # Add an account age check to make this more specific to amplification context
                if account_creation_date and is_new_account(account_creation_date, ACCOUNT_CREATION_DATE_THRESHOLD_DAYS * 2): # e.g., <60 days
                    flagged = True
                    detection_rules.append(f"Rule: Short, Generic 5-star review from New-ish Account (<{ACCOUNT_CREATION_DATE_THRESHOLD_DAYS * 2} days)")
            
            if flagged:
                flag_timestamp = datetime.utcnow().isoformat() + "Z"
                # Create a unique flag_id using review_id and timestamp for potential multiple flags per review
                flag_id = f"FP_{review_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}" 

                flagged_item = {
                    "flag_id": flag_id,
                    "review_id": review_id,
                    "product_id": product_id,
                    "user_id": user_id,
                    "rating": rating,
                    "review_text": review_text,
                    "flag_type": "FakePositiveAmplification",
                    "detection_rule": "; ".join(detection_rules),
                    "flag_timestamp": flag_timestamp,
                    "status": "PENDING_REVIEW", # Initial status for analyst review
                    "metadata": { # Store additional context for analysts
                        "account_creation_date": account_creation_date,
                        "review_length_words": len(review_text.split()),
                    }
                }
                flagged_items.append(flagged_item)

        except Exception as e:
            print(f"Error processing Kinesis record: {e}. Record: {record}")
    
    if flagged_items:
        # Use DynamoDB's batch_writer for efficient writing of multiple items
        with table.batch_writer() as batch:
            for item in flagged_items:
                batch.put_item(Item=item)
        print(f"Successfully flagged {len(flagged_items)} reviews for fake positive amplification.")
    
    return {
        "statusCode": 200,
        "body": json.dumps(f"Processed {len(event['Records'])} Kinesis records. Flagged {len(flagged_items)} reviews.")
    }
