import json
import boto3
import os
import uuid
from pydantic import BaseModel, Field
from datetime import datetime

kinesis_client = boto3.client('kinesis', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
STREAM_NAME = os.environ.get('KINESIS_STREAM_NAME', 'real-time-review-stream')

class ReviewInput(BaseModel):
    productId: str
    userId: str
    rating: int = Field(..., ge=1, le=5)
    title: str
    comment: str
    marketplace: str

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        
        # Generate a unique reviewId and set reviewDate
        review_id = str(uuid.uuid4())
        review_date = datetime.utcnow()

        # Validate input using Pydantic
        review_input = ReviewInput(**body)

        # Construct the full review data
        full_review_data = review_input.dict()
        full_review_data['reviewId'] = review_id
        full_review_data['reviewDate'] = review_date.isoformat() # Store as ISO 8601 string

        # Send to Kinesis
        kinesis_client.put_record(
            StreamName=STREAM_NAME,
            Data=json.dumps(full_review_data),
            PartitionKey=full_review_data['userId'] # Using userId for partition to keep user's reviews ordered
        )

        return {
            'statusCode': 202,
            'body': json.dumps({'message': 'Review accepted for processing', 'reviewId': review_id})
        }
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid JSON body'})
        }
    except Exception as e: # Catch Pydantic validation errors and other exceptions
        return {
            'statusCode': 400,
            'body': json.dumps({'message': f'Validation or processing error: {str(e)}'})
        }
