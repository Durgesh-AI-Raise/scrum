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
# Placeholder for competitor product IDs - in a real system, this would come from a configuration store
COMPETITOR_PRODUCT_IDS = {"P_COMP_001", "P_COMP_002", "P_COMP_003"} 
GENERIC_NEGATIVE_KEYWORDS = ["terrible product", "waste of money", "horrible", "awful", "don't buy", "regret purchase"]
REVIEW_TEXT_WORD_COUNT_THRESHOLD = 15 # For 'short review' rule

def is_new_account(account_creation_date_str, threshold_days):
    """Checks if an account was created within the last 'threshold_days'."""
    try:
        creation_date = datetime.fromisoformat(account_creation_date_str.replace('Z', '+00:00'))
        return (datetime.now(creation_date.tzinfo) - creation_date).days < threshold_days
    except (ValueError, TypeError):
        return False

def contains_generic_negative_phrases(review_text, keywords):
    """Checks if review text contains generic negative phrases."""
    text_lower = review_text.lower()
    return any(keyword in text_lower for keyword in keywords)

def lambda_handler(event, context):
    """
    Processes Kinesis records to detect fake negative sabotage patterns.
    """
    flagged_items = []
    
    for record in event["Records"]:
        try:
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

            # --- Rule 1: New Account + Low Rating (e.g., 1-star) + Targeting Competitor Product ---
            if rating == 1 and account_creation_date and \
               is_new_account(account_creation_date, ACCOUNT_CREATION_DATE_THRESHOLD_DAYS) and \
               product_id in COMPETITOR_PRODUCT_IDS:
                flagged = True
                detection_rules.append(f"Rule: New Account (<{ACCOUNT_CREATION_DATE_THRESHOLD_DAYS} days) + 1-star rating + Competitor Product")

            # --- Rule 2: Short, Generic Negative Review from a New-ish Account ---
            if not flagged and rating == 1 and len(review_text.split()) < REVIEW_TEXT_WORD_COUNT_THRESHOLD and \
               contains_generic_negative_phrases(review_text, GENERIC_NEGATIVE_KEYWORDS):
                # Add an account age check for context
                if account_creation_date and is_new_account(account_creation_date, ACCOUNT_CREATION_DATE_THRESHOLD_DAYS * 2):
                    flagged = True
                    detection_rules.append(f"Rule: Short, Generic 1-star review from New-ish Account (<{ACCOUNT_CREATION_DATE_THRESHOLD_DAYS * 2} days)")
            
            if flagged:
                flag_timestamp = datetime.utcnow().isoformat() + "Z"
                flag_id = f"FN_{review_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}" 

                flagged_item = {
                    "flag_id": flag_id,
                    "review_id": review_id,
                    "product_id": product_id,
                    "user_id": user_id,
                    "rating": rating,
                    "review_text": review_text,
                    "flag_type": "FakeNegativeSabotage",
                    "detection_rule": "; ".join(detection_rules),
                    "flag_timestamp": flag_timestamp,
                    "status": "PENDING_REVIEW",
                    "metadata": {
                        "account_creation_date": account_creation_date,
                        "review_length_words": len(review_text.split()),
                    }
                }
                flagged_items.append(flagged_item)

        except Exception as e:
            print(f"Error processing Kinesis record: {e}. Record: {record}")
    
    if flagged_items:
        with table.batch_writer() as batch:
            for item in flagged_items:
                batch.put_item(Item=item)
        print(f"Successfully flagged {len(flagged_items)} reviews for fake negative sabotage.")
    
    return {
        "statusCode": 200,
        "body": json.dumps(f"Processed {len(event['Records'])} Kinesis records. Flagged {len(flagged_items)} reviews.")
    }
