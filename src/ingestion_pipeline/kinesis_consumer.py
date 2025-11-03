# filename: src/ingestion_pipeline/kinesis_consumer.py
import json
import os
from datetime import datetime
import psycopg2 # Assuming PostgreSQL

# Environment variables for database connection
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

def handler(event, context):
    """
    AWS Lambda handler function to process records from a Kinesis stream.
    Each record is expected to be a JSON string representing a review.
    """
    conn = None
    cur = None # Initialize cursor outside try block
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()

        for record in event['Records']:
            payload_data = record['kinesis']['data']
            # Kinesis data is base64 encoded
            decoded_payload = json.loads(payload_data.decode('utf-8'))
            print(f"Processing review: {decoded_payload.get('id')}")

            try:
                # Store in database
                insert_query = """
                INSERT INTO reviews (
                    id, product_id, reviewer_id, rating, title, text_content, review_date, ingestion_timestamp,
                    is_flagged, flag_reasons, severity, is_processed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING; -- Prevents re-inserting if processed multiple times
                """
                # Initialize default values for flagging
                cur.execute(insert_query, (
                    decoded_payload['id'],
                    decoded_payload['product_id'],
                    decoded_payload['reviewer_id'],
                    decoded_payload['rating'],
                    decoded_payload.get('title', ''), # Handle potential missing title
                    decoded_payload['text_content'],
                    decoded_payload['review_date'],
                    decoded_payload['ingestion_timestamp'],
                    False, # is_flagged
                    [],    # flag_reasons (as JSONB array in Postgres)
                    0,     # severity
                    False  # is_processed
                ))
                print(f"Review {decoded_payload['id']} ingested successfully.")

            except Exception as e:
                # Log the error for specific record, but continue processing others
                print(f"Error processing individual review {decoded_payload.get('id')}: {e}")
                # In a real system, send to Dead Letter Queue (DLQ)
        conn.commit()

    except Exception as e:
        print(f"Database connection or general processing error: {e}")
        # This will cause the Lambda to fail and retry the batch if configured

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return {'statusCode': 200, 'body': 'Processed Kinesis records'}

# Example Kinesis event structure (for local testing/understanding)
# event = {
#   "Records": [
#     {
#       "kinesis": {
#         "kinesisSchemaVersion": "1.0",
#         "partitionKey": "B00XXXXXXX",
#         "sequenceNumber": "49590338271714902568840241029897451313576092794038446082",
#         "data": "eyJpZCI6ICJhYmMtMTIzIiwgInByb2R1Y3RfaWQiOiAiQjAwWFhYWFhYWCIsICJyZXZpZXdlcl9pZCI6ICJSWFhYWFhYWFgiLCAicmF0aW5nIjogNSwgInRpdGxlIjogIkdyZWF0IFByb2R1Y3QhIiwgInRleHRfY29udGVudCI6ICJUaGlzIHByb2R1Y3QgaXMgYW1hemluZyBhbmQgd29ya3MgcGVyZmVjdGx5LiIsICJyZXZpZXdfZGF0ZSI6ICIyMDIzLTEwLTI2VDEwOjAwOjAwWiIsICJpbmdlc3Rpb25fdGltZXN0YW1wIjogIjIwMjMtMTAtMjZUMTA6MzA6MDYuMjU4ODk5In0=",
#         "approximateArrivalTimestamp": 1545084650.987
#       },
#       "eventSource": "aws:kinesis",
#       "eventVersion": "1.0",
#       "eventID": "shardId-000000000000:49590338271714902568840241029897451313576092794038446082",
#       "eventName": "aws:kinesis:record",
#       "invokeIdentityArn": "arn:aws:iam::EXAMPLE",
#       "awsRegion": "us-east-1",
#       "eventSourceARN": "arn:aws:kinesis:us-east-1:EXAMPLE:stream/amazon-review-stream"
#     }
#   ]
# }
