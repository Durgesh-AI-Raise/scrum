import json
import os
import boto3
import base64
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from decimal import Decimal

# Initialize AWS clients
dynamodb_client = boto3.client('dynamodb')

# Environment variables (to be set in Lambda configuration)
REVIEWS_TABLE_NAME = os.environ.get('REVIEWS_TABLE_NAME', 'aris-all-reviews')
ACTIVITY_TABLE_NAME = os.environ.get('ACTIVITY_TABLE_NAME', 'aris-reviewer-activity')

# For MVP, rules are hardcoded. In production, load from S3 or config service.
ACCOUNT_ACTIVITY_RULES = [
    {
        "ruleId": "HIGH_VELOCITY_NEW_ACCOUNT",
        "description": "New account (e.g., < 7 days old) leaving many reviews quickly (e.g., > 5 reviews in 24 hours).",
        "baseScore": 0.8,
        "minAccountAgeDays": 7,          # If account age is less than this, AND...
        "maxReviewsInTimeframe": 5,      # ...reviews in timeframe exceed this
        "timeframeHours": 24             # ...within this many hours
    },
    {
        "ruleId": "DIVERSE_PRODUCT_REVIEWER",
        "description": "Account reviewing unrelated products (e.g., > 3 unique categories in 24 hours).",
        "baseScore": 0.7,
        "minUniqueCategories": 3,
        "timeWindowHours": 24
    }
]

def analyze_account_activity(reviewer_id, review_data, current_activity):
    """
    Analyzes reviewer activity against defined rules.
    Returns a list of detected flags and the updated activity state.
    """
    flags = []
    current_time = datetime.utcnow()
    current_time_iso = current_time.isoformat(timespec='milliseconds') + 'Z'

    # Ensure accountCreationDate exists, if not, use the first review date
    account_creation_date = datetime.fromisoformat(
        current_activity.get('accountCreationDate', review_data['reviewDate']).replace('Z', '+00:00'))

    # Update current activity with the new review
    recent_reviews = current_activity.get('recentReviews', [])
    recent_reviews.append({
        "reviewId": review_data['reviewId'],
        "reviewDate": review_data['reviewDate'],
        "productId": review_data['productId'],
        "productCategory": review_data.get('productCategory', 'UNKNOWN') # Use 'UNKNOWN' if not provided
    })

    # Filter out old reviews outside relevant time windows (e.g., last 24 hours for velocity/diversity)
    max_history_hours = max([rule.get('timeframeHours', 0) for rule in ACCOUNT_ACTIVITY_RULES] + [rule.get('timeWindowHours', 0) for rule in ACCOUNT_ACTIVITY_RULES])
    if max_history_hours > 0:
        cutoff_time = current_time - timedelta(hours=max_history_hours)
        recent_reviews = [
            r for r in recent_reviews
            if datetime.fromisoformat(r['reviewDate'].replace('Z', '+00:00')) > cutoff_time
        ]

    updated_activity = current_activity.copy()
    updated_activity['reviewerId'] = reviewer_id # Ensure PK is always present
    updated_activity['accountCreationDate'] = account_creation_date.isoformat(timespec='milliseconds') + 'Z'
    updated_activity['recentReviews'] = recent_reviews
    updated_activity['totalReviews'] = updated_activity.get('totalReviews', 0) + 1
    updated_activity['lastReviewDate'] = review_data['reviewDate']

    # Apply rules
    for rule in ACCOUNT_ACTIVITY_RULES:
        if rule['ruleId'] == "HIGH_VELOCITY_NEW_ACCOUNT":
            # Check if account is "new"
            if (current_time - account_creation_date).days < rule['minAccountAgeDays']:
                # Check review velocity within the specified timeframe
                velocity_cutoff = current_time - timedelta(hours=rule['timeframeHours'])
                reviews_in_timeframe = [
                    r for r in recent_reviews
                    if datetime.fromisoformat(r['reviewDate'].replace('Z', '+00:00')) > velocity_cutoff
                ]
                if len(reviews_in_timeframe) > rule['maxReviewsInTimeframe']:
                    flags.append({
                        "type": "account_activity",
                        "ruleId": rule['ruleId'],
                        "description": rule['description'],
                        "score": Decimal(str(rule['baseScore'])),
                        "timestamp": current_time_iso
                    })
        elif rule['ruleId'] == "DIVERSE_PRODUCT_REVIEWER":
            diversity_cutoff = current_time - timedelta(hours=rule['timeWindowHours'])
            reviews_for_diversity = [
                r for r in recent_reviews
                if datetime.fromisoformat(r['reviewDate'].replace('Z', '+00:00')) > diversity_cutoff
            ]
            unique_categories = {r['productCategory'] for r in reviews_for_diversity}
            if len(unique_categories) >= rule['minUniqueCategories']:
                flags.append({
                    "type": "account_activity",
                    "ruleId": rule['ruleId'],
                    "description": rule['description'],
                    "score": Decimal(str(rule['baseScore'])),
                    "timestamp": current_time_iso
                })
    return flags, updated_activity

def lambda_handler(event, context):
    for record in event['Records']:
        try:
            payload_str = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            payload = json.loads(payload_str)
            reviewer_id = payload.get('reviewerId')
            review_id = payload.get('reviewId')

            if not reviewer_id or not review_id:
                print(f"Skipping record with missing reviewerId or reviewId: {payload_str}")
                continue

            # 1. Fetch reviewer's current activity state
            current_activity = {}
            try:
                response = dynamodb_client.get_item(
                    TableName=ACTIVITY_TABLE_NAME,
                    Key={'reviewerId': {'S': reviewer_id}}
                )
                if 'Item' in response:
                    # Convert DynamoDB item to a regular Python dictionary
                    current_activity = {k: v['S'] if 'S' in v else (float(v['N']) if 'N' in v else v['BOOL'] if 'BOOL' in v else v['L'] if 'L' in v else v['M']) for k, v in response['Item'].items()}
                    # Deep convert lists of maps
                    if 'recentReviews' in current_activity and isinstance(current_activity['recentReviews'], list):
                        current_activity['recentReviews'] = [{k_inner: v_inner['S'] for k_inner, v_inner in item['M'].items()} for item in current_activity['recentReviews']]

            except ClientError as e:
                print(f"Error fetching activity for reviewer {reviewer_id}: {e}. Initializing new activity state.")
                # Current activity remains {}

            # 2. Analyze activity and get flags, and updated activity state
            detected_flags, updated_activity = analyze_account_activity(reviewer_id, payload, current_activity)

            # 3. Update reviewer's activity state in DynamoDB
            try:
                # Convert updated_activity back to DynamoDB format
                item_to_put = {
                    'reviewerId': {'S': updated_activity['reviewerId']},
                    'accountCreationDate': {'S': updated_activity['accountCreationDate']},
                    'lastReviewDate': {'S': updated_activity['lastReviewDate']},
                    'totalReviews': {'N': str(updated_activity['totalReviews'])},
                    'recentReviews': {'L': [
                        {'M': {
                            'reviewId': {'S': r['reviewId']},
                            'reviewDate': {'S': r['reviewDate']},
                            'productId': {'S': r['productId']},
                            'productCategory': {'S': r['productCategory']}
                        }} for r in updated_activity['recentReviews']
                    ]}
                }
                dynamodb_client.put_item(
                    TableName=ACTIVITY_TABLE_NAME,
                    Item=item_to_put
                )
                print(f"Updated activity for reviewer {reviewer_id}.")
            except ClientError as e:
                print(f"Error updating activity for reviewer {reviewer_id}: {e}")

            # 4. Update the review in aris-all-reviews with flags
            if detected_flags:
                new_flags_score_sum = sum(flag['score'] for flag in detected_flags)

                dynamodb_flags_list = []
                for flag in detected_flags:
                    dynamodb_flags_list.append({
                        'M': {
                            'type': {'S': flag['type']},
                            'ruleId': {'S': flag['ruleId']},
                            'description': {'S': flag['description']},
                            'score': {'N': str(flag['score'])},
                            'timestamp': {'S': flag['timestamp']}
                        }
                    })

                try:
                    # Update with list_append and numeric addition
                    response = dynamodb_client.update_item(
                        TableName=REVIEWS_TABLE_NAME,
                        Key={'reviewId': {'S': review_id}},
                        UpdateExpression="SET isFlagged = :isFlagged, "
                                         "flagDetails = list_append(if_not_exists(flagDetails, :empty_list), :new_flags), "
                                         "abuseScore = abuseScore + :flags_score_sum",
                        ExpressionAttributeValues={
                            ':isFlagged': {'BOOL': True},
                            ':new_flags': {'L': dynamodb_flags_list},
                            ':empty_list': {'L': []},
                            ':flags_score_sum': {'N': str(new_flags_score_sum)}
                        },
                        ReturnValues="UPDATED_NEW"
                    )
                    print(f"Updated review {review_id} with account activity flags. New abuseScore: {response['Attributes']['abuseScore']['N']}")
                except ClientError as e:
                     if e.response['Error']['Code'] == 'ValidationException' and "The provided expression refers to an attribute that does not exist" in e.response['Error']['Message']:
                         print(f"Attempting to initialize abuseScore for review {review_id} and add flags.")
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
                         print(f"Initialized abuseScore and updated review {review_id} with account activity flags.")
                     else:
                        print(f"Error updating DynamoDB for review {review_id}: {e}")
            else:
                print(f"No suspicious account activity patterns found for review {review_id}.")

        except json.JSONDecodeError as e:
            print(f"Skipping malformed JSON record: {record['kinesis']['data']}, Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred processing record: {e}, Record: {record.get('kinesis', {}).get('data', 'N/A')}")

    return {'statusCode': 200, 'body': 'Processed account activity records.'}