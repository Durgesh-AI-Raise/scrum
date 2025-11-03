import json
import base64
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Re-using the ReviewInput model from Task 1.3
class ReviewInput(BaseModel):
    productId: str
    userId: str
    rating: int = Field(..., ge=1, le=5)
    title: str
    comment: str
    marketplace: str
    reviewId: str # Added in Task 1.3
    reviewDate: str # Added in Task 1.3, ISO 8601 string

def lambda_handler(event, context):
    logger.info(f"Received Kinesis event with {len(event['Records'])} records.")
    processed_records = 0

    for record in event['Records']:
        # Kinesis data is Base64 encoded
        payload_b64 = record['kinesis']['data']
        payload_decoded = base64.b64decode(payload_b64).decode('utf-8')

        try:
            review_data = json.loads(payload_decoded)
            logger.info(f"Parsed Kinesis record: {review_data}")

            # Validate against Pydantic schema
            validated_review = ReviewInput(**review_data)
            logger.info(f"Successfully validated review: {validated_review.dict()}")

            # --- Placeholder for Rule Engine integration (Task 2.5) ---
            # In a real scenario, the validated_review would be passed to the rule engine
            # or another processing component here.
            # For now, we just log its successful parsing.
            print(f"Validated review ready for rule engine: {validated_review.json()}")
            # --------------------------------------------------------

            processed_records += 1

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from Kinesis record: {e}. Payload: {payload_decoded}")
            # Optionally, push to a DLQ for further investigation
        except ValidationError as e:
            logger.error(f"Schema validation failed for Kinesis record: {e}. Payload: {payload_decoded}")
            # Optionally, push to a DLQ for further investigation
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing Kinesis record: {e}. Payload: {payload_decoded}")
            # Catch all other unexpected errors

    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully processed {processed_records} records.')
    }
