import json
import base64
import os
import logging
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError
import boto3

# Initialize AWS clients
kinesis_client = boto3.client('kinesis', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# Configuration for flagged reviews stream
FLAGGED_REVIEWS_STREAM_NAME = os.environ.get('FLAGGED_REVIEWS_STREAM_NAME', 'flagged-reviews-stream')
RULES_CONFIG_BUCKET = os.environ.get('RULES_CONFIG_BUCKET', 'amazon-review-abuse-detection-config')
RULES_CONFIG_KEY = os.environ.get('RULES_CONFIG_KEY', 'rules_config.json')

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Data models (re-used and extended)
class ReviewInput(BaseModel):
    productId: str
    userId: str
    rating: int = Field(..., ge=1, le=5)
    title: str
    comment: str
    marketplace: str
    reviewId: str
    reviewDate: str

class FlaggedReviewOutput(BaseModel):
    reviewId: str
    productId: str
    userId: str
    comment: str # Including comment for quick glance on dashboard
    flagged: bool
    triggeredHeuristics: list[str]
    flaggingTimestamp: str
    rawReview: dict # Keep original review for full context

# --- Rule Definitions (Placeholders for Task 2.2, 2.3) ---
class RuleEngine:
    def __init__(self, rules_config):
        self.rules_config = rules_config
        # Dynamically load rules if more complex, for now, direct calls.
        self.rules = {
            "keyword_matching_rule": self._keyword_matching_rule,
            "repetitive_posting_rule": self._repetitive_posting_rule
            # Add other rules here
        }

    def _load_config(self):
        try:
            response = s3_client.get_object(Bucket=RULES_CONFIG_BUCKET, Key=RULES_CONFIG_KEY)
            config_data = json.loads(response['Body'].read().decode('utf-8'))
            logger.info("Successfully loaded rules configuration from S3.")
            return config_data
        except Exception as e:
            logger.error(f"Failed to load rules configuration from S3: {e}. Using default/empty config.")
            return {}

    def _keyword_matching_rule(self, review: ReviewInput) -> bool:
        # Placeholder for Task 2.2 logic
        config = self.rules_config.get("keyword_matching_rule", {})
        if not config.get("enabled", False):
            return False

        keywords = config.get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in review.comment.lower() or keyword.lower() in review.title.lower():
                logger.info(f"Keyword '{keyword}' matched in review {review.reviewId}")
                return True
        return False

    def _repetitive_posting_rule(self, review: ReviewInput) -> bool:
        # Placeholder for Task 2.3 logic
        config = self.rules_config.get("repetitive_posting_rule", {})
        if not config.get("enabled", False):
            return False
        
        # This rule would typically require looking up past reviews for the user
        # in a persistent store (e.g., DynamoDB, Redis) within a time window.
        # For now, it's a placeholder.
        logger.debug(f"Executing repetitive posting rule for review {review.reviewId} (placeholder logic).")
        return False # Always return False for now until implemented

    def evaluate_review(self, review: ReviewInput) -> FlaggedReviewOutput:
        triggered_heuristics = []
        is_flagged = False

        for rule_name, rule_func in self.rules.items():
            if self.rules_config.get(rule_name, {}).get("enabled", False):
                try:
                    if rule_func(review):
                        triggered_heuristics.append(rule_name)
                        is_flagged = True
                except Exception as e:
                    logger.error(f"Error executing rule '{rule_name}' for review {review.reviewId}: {e}")

        return FlaggedReviewOutput(
            reviewId=review.reviewId,
            productId=review.productId,
            userId=review.userId,
            comment=review.comment,
            flagged=is_flagged,
            triggeredHeuristics=triggered_heuristics,
            flaggingTimestamp=datetime.utcnow().isoformat(),
            rawReview=review.dict() # Store original review for context
        )

# Global instance of RuleEngine (loaded once per Lambda instance)
rules_config_data = {}
try:
    # Attempt to load configuration at global scope for warm starts
    s3_response = s3_client.get_object(Bucket=RULES_CONFIG_BUCKET, Key=RULES_CONFIG_KEY)
    rules_config_data = json.loads(s3_response['Body'].read().decode('utf-8'))
    logger.info("Initial rules configuration loaded successfully at global scope.")
except Exception as e:
    logger.warning(f"Failed to load initial rules configuration at global scope: {e}. Lambda will attempt to load per invocation if needed.")

rule_engine = RuleEngine(rules_config_data)


def lambda_handler(event, context):
    logger.info(f"Received Kinesis event with {len(event['Records'])} records for rule engine processing.")
    output_records = []

    # Refresh config if it's empty (e.g., cold start failed to load)
    if not rule_engine.rules_config:
        rules_config_data = rule_engine._load_config()
        rule_engine.rules_config = rules_config_data

    for record in event['Records']:
        payload_b64 = record['kinesis']['data']
        payload_decoded = base64.b64decode(payload_b64).decode('utf-8')

        try:
            review_data = json.loads(payload_decoded)
            validated_review = ReviewInput(**review_data)

            flagged_review_output = rule_engine.evaluate_review(validated_review)
            output_records.append(flagged_review_output.dict())

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from Kinesis record in Rule Engine: {e}. Payload: {payload_decoded}")
            # Consider pushing to a DLQ for malformed records
        except ValidationError as e:
            logger.error(f"Schema validation failed for Kinesis record in Rule Engine: {e}. Payload: {payload_decoded}")
            # Consider pushing to a DLQ for invalid schema records
        except Exception as e:
            logger.error(f"An unexpected error occurred during rule engine processing: {e}. Payload: {payload_decoded}")

    if output_records:
        # Batch put records to the flagged reviews Kinesis stream
        kinesis_records = []
        for rec in output_records:
            kinesis_records.append({
                'Data': json.dumps(rec),
                'PartitionKey': rec['userId'] # Maintain partition by userId for consistency
            })
        
        try:
            response = kinesis_client.put_records(
                StreamName=FLAGGED_REVIEWS_STREAM_NAME,
                Records=kinesis_records
            )
            logger.info(f"Successfully put {len(kinesis_records)} records to {FLAGGED_REVIEWS_STREAM_NAME}. Response: {response}")
            if response.get('FailedRecordCount', 0) > 0:
                logger.error(f"Failed to put {response['FailedRecordCount']} records to Kinesis: {response['Records']}")
        except Exception as e:
            logger.error(f"Failed to put records to Kinesis stream {FLAGGED_REVIEWS_STREAM_NAME}: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps(f'Rule engine processed {len(event['Records'])} records, sent {len(output_records)} to output stream.')
    }
