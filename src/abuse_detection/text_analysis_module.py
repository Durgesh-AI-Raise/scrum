import json
import os
import boto3
import re
import base64
from datetime import datetime
from botocore.exceptions import ClientError
from decimal import Decimal

# Initialize AWS clients
dynamodb_client = boto3.client('dynamodb')

# Environment variables (to be set in Lambda configuration)
REVIEWS_TABLE_NAME = os.environ.get('REVIEWS_TABLE_NAME', 'aris-all-reviews')

# For MVP, patterns are hardcoded. In production, load from S3 or config service.
SUSPICIOUS_PATTERNS = [
    {
        "ruleId": "GENERIC_PRAISE",
        "pattern": r".*(absolutely amazing|love it so much|best product ever|highly recommend|superb quality).*",
        "type": "regex",
        "description": "Generic positive phrases often used by bots or paid reviewers.",
        "baseScore": 0.6
    },
    {
        "ruleId": "REPETITIVE_WORDS",
        "pattern": r"(\b\w{3,}\b(?:[']\w+)?\s*)\1{2,}", # Detects a word (3+ chars) repeating 3+ times
        "type": "regex",
        "description": "Detects highly repetitive words/phrases indicating spam.",
        "baseScore": 0.7
    },
    {
        "ruleId": "KEYWORD_STUFFING_COMMERCIAL",
        "keywords": ["buy now", "discount code", "free shipping", "promo code", "click here"],
        "type": "keywords_count",
        "description": "Commercial keywords indicating paid reviews or spam.",
        "baseScore": 0.9,
        "min_occurrences": 2
    },
    {
        "ruleId": "GENERIC_CRITICISM",
        "pattern": r".*(terrible product|waste of money|highly disappointed|never again).*",
        "type": "regex",
        "description": "Generic negative phrases often used by bots or competitors.",
        "baseScore": 0.5
    }
]

def analyze_text(review_text):
    """
    Analyzes review text against defined suspicious language patterns.
    Returns a list of detected flags.
    """
    flags = []
    current_time_iso = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'

    for pattern_def in SUSPICIOUS_PATTERNS:
        if pattern_def['type'] == 'regex':
            if re.search(pattern_def['pattern'], review_text, re.IGNORECASE):
                flags.append({
                    "type": "text_pattern",
                    "ruleId": pattern_def['ruleId'],
                    "description": pattern_def['description'],
                    "score": Decimal(str(pattern_def['baseScore'])), # Store as Decimal
                    "timestamp": current_time_iso
                })
        elif pattern_def['type'] == 'keywords_count':
            count = 0
            # Ensure review_text is lowercase for case-insensitive matching
            lower_review_text = review_text.lower()
            for keyword in pattern_def['keywords']:
                count += lower_review_text.count(keyword.lower())
            if count >= pattern_def.get('min_occurrences', 1):
                flags.append({
                    "type": "text_pattern",
                    "ruleId": pattern_def['ruleId'],
                    "description": pattern_def['description'],
                    "score": Decimal(str(pattern_def['baseScore'])), # Store as Decimal
                    "timestamp": current_time_iso
                })
    return flags

def lambda_handler(event, context):
    for record in event['Records']:
        try:
            payload_str = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            payload = json.loads(payload_str)
            review_id = payload.get('reviewId')
            review_text = payload.get('reviewText', '')

            if not review_id:
                print(f"Skipping record with no reviewId: {payload_str}")
                continue

            detected_flags = analyze_text(review_text)

            if detected_flags:
                # Calculate the sum of scores from newly detected flags
                new_flags_score_sum = sum(flag['score'] for flag in detected_flags)

                # Convert flags for DynamoDB list append (List of Map type)
                dynamodb_flags_list = []
                for flag in detected_flags:
                    # Manually prepare the map for DynamoDB
                    dynamodb_flags_list.append({
                        'M': {
                            'type': {'S': flag['type']},
                            'ruleId': {'S': flag['ruleId']},
                            'description': {'S': flag['description']},
                            'score': {'N': str(flag['score'])},
                            'timestamp': {'S': flag['timestamp']}
                        }
                    })

                # Update DynamoDB with flags and abuseScore
                try:
                    # Use update_item with list_append and numeric addition
                    response = dynamodb_client.update_item(
                        TableName=REVIEWS_TABLE_NAME,
                        Key={'reviewId': {'S': review_id}},
                        UpdateExpression="SET isFlagged = :isFlagged, "
                                         "flagDetails = list_append(if_not_exists(flagDetails, :empty_list), :new_flags), "
                                         "abuseScore = abuseScore + :flags_score_sum",
                        ExpressionAttributeValues={
                            ':isFlagged': {'BOOL': True},
                            ':new_flags': {'L': dynamodb_flags_list},
                            ':empty_list': {'L': []}, # Used if flagDetails does not exist
                            ':flags_score_sum': {'N': str(new_flags_score_sum)}
                        },
                        ReturnValues="UPDATED_NEW"
                    )
                    print(f"Updated review {review_id} with text analysis flags. New abuseScore: {response['Attributes']['abuseScore']['N']}")
                except ClientError as e:
                    # Handle cases where abuseScore might not exist initially (though ingestion should set it to 0.0)
                    if e.response['Error']['Code'] == 'ValidationException' and "The provided expression refers to an attribute that does not exist" in e.response['Error']['Message']:
                         print(f"Attempting to initialize abuseScore for review {review_id} and add flags.")
                         # This case should ideally not happen if ingestion sets abuseScore to 0.0,
                         # but included for robustness if item was created without it.
                         dynamodb_client.update_item(
                            TableName=REVIEWS_TABLE_NAME,
                            Key={'reviewId': {'S': review_id}},
                            UpdateExpression="SET isFlagged = :isFlagged, "
                                             "flagDetails = list_append(if_not_exists(flagDetails, :empty_list), :new_flags), "
                                             "abuseScore = :initial_score + :flags_score_sum",
                            ExpressionAttributeValues={
                                ':isFlagged': {'BOOL': True},
                                ':new_flags': {'L': dynamodb_flags_list},
                                ':empty_list': {'L': []},
                                ':initial_score': {'N': '0.0'},
                                ':flags_score_sum': {'N': str(new_flags_score_sum)}
                            },
                            ReturnValues="UPDATED_NEW"
                        )
                         print(f"Initialized abuseScore and updated review {review_id} with text analysis flags.")
                    else:
                        print(f"Error updating DynamoDB for review {review_id}: {e}")
            else:
                print(f"No suspicious text patterns found for review {review_id}.")

        except json.JSONDecodeError as e:
            print(f"Skipping malformed JSON record: {record['kinesis']['data']}, Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred processing record: {e}, Record: {record.get('kinesis', {}).get('data', 'N/A')}")

    return {'statusCode': 200, 'body': 'Processed text analysis records.'}