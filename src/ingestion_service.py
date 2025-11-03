# src/ingestion_service.py
from flask import Flask, request, jsonify
from datetime import datetime
import json
import logging
from typing import Dict, Any

# Assuming data_models.py is in the same directory or importable path
from data_models import Review, ReviewerMetadata

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# --- Mock Implementations (to be replaced with actual AWS SDK or Kafka client) ---
class MockKinesisClient:
    def put_record(self, StreamName, Data, PartitionKey):
        logging.info(f"Mock Kinesis: Publishing to {StreamName} with PartitionKey {PartitionKey}: {Data}")
        return {"ShardId": "mock-shard-123", "SequenceNumber": "mock-seq-456"}

class MockDynamoDBClient:
    def put_item(self, TableName, Item):
        logging.info(f"Mock DynamoDB: Storing to {TableName}: {Item}")
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

kinesis_client = MockKinesisClient()
dynamodb_client = MockDynamoDBClient()

KINESIS_STREAM_NAME = "amazon-review-events"
DYNAMODB_TABLE_NAME = "amazon-reviews-raw"
# ---------------------------------------------------------------------------------

@app.route('/ingest/review', methods=['POST'])
def ingest_review():
    raw_data: Dict[str, Any] = request.get_json()

    if not raw_data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    try:
        # 1. Basic Validation and Parsing to Data Model
        # This will raise TypeError or ValueError if required fields are missing or types are incorrect
        review_obj = Review(**raw_data)

        # 2. More complex business validation (e.g., check for valid product_id format)
        if not review_obj.product_id or not review_obj.reviewer_id:
            raise ValueError("Product ID and Reviewer ID are required.")

        # 3. Store raw data in DynamoDB
        # Convert the Review object back to a dictionary suitable for storage
        item_to_store = review_obj.to_dict()
        dynamodb_client.put_item(TableName=DYNAMODB_TABLE_NAME, Item=item_to_store)

        # 4. Publish to Kinesis Stream
        # Use review_id or product_id as PartitionKey for even distribution
        kinesis_client.put_record(
            StreamName=KINESIS_STREAM_NAME,
            Data=json.dumps(review_obj.to_dict()).encode('utf-8'),
            PartitionKey=review_obj.review_id
        )

        logging.info(f"Successfully ingested review {review_obj.review_id}")
        return jsonify({"status": "success", "review_id": review_obj.review_id}), 202

    except (TypeError, ValueError) as e:
        logging.error(f"Validation error during ingestion: {e} - Data: {raw_data}")
        # In a real system, push to a DLQ here.
        return jsonify({"status": "error", "message": f"Invalid review data: {e}"}), 400
    except Exception as e:
        logging.error(f"Unexpected error during ingestion: {e} - Data: {raw_data}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == '__main__':
    # This is for local development. In production, use a WSGI server like Gunicorn.
    app.run(debug=True, port=5000)
