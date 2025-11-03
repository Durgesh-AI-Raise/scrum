### Task 1.4: Develop data parsing and initial schema definition.

*   **Implementation Plan:** Develop an AWS Lambda function that consumes records from the Kinesis Data Stream, parses the raw JSON review data, performs basic data validation, and then stores the structured data into the S3 data lake in a more query-optimized format (e.g., Parquet). This Lambda will be triggered by the Kinesis stream.

*   **Data Models and Architecture:**
    *   **Consumer/Parser:** AWS Lambda function (`ReviewDataParser`) triggered by `amazon-review-data-stream`.
    *   **Input:** Kinesis Data Stream (`amazon-review-data-stream`) with raw JSON review data.
    *   **Output:** AWS S3 (`amazon-raw-review-data-lake-prod`) storing data in Parquet format, organized by date (e.g., `s3://amazon-raw-review-data-lake-prod/reviews/year=YYYY/month=MM/day=DD/`).
    *   **Schema Definition (Parquet/Glue Table):**
        ```sql
        CREATE EXTERNAL TABLE IF NOT EXISTS reviews (
            reviewId STRING,
            reviewerId STRING,
            productASIN STRING,
            timestamp TIMESTAMP,
            orderId STRING,
            reviewTitle STRING,
            reviewText STRING,
            overallRating INT,
            ingestionTimestamp TIMESTAMP -- Add a timestamp for when the record was ingested into the data lake
        )
        PARTITIONED BY (
            year INT,
            month INT,
            day INT
        )
        ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
        STORED AS PARQUET
        LOCATION 's3://amazon-raw-review-data-lake-prod/reviews/';
        ```
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** The raw JSON review data from Kinesis will be consistent with the structure defined in Task 1.2.
    *   **Decision:** Parquet format is chosen for structured storage due to its columnar nature, which is efficient for analytical queries and storage compression.
    *   **Decision:** Data will be partitioned by `year`, `month`, and `day` in S3 to optimize query performance and reduce scan costs.
    *   **Decision:** AWS Glue Data Catalog will be used to manage the schema for the Parquet data in S3, making it discoverable and queryable by services like Athena.
    *   **Decision:** Python with `pyarrow` (or `pandas` with `pyarrow` engine) will be used within the Lambda to handle Parquet writing. Since `pyarrow` can add to Lambda deployment size, consider using AWS Glue for more complex transformations later, but for initial parsing, Lambda with `pyarrow` can be viable.
*   **Code Snippets/Pseudocode (AWS Lambda - `review_data_parser.py`):**
    ```python
    import json
    import os
    import base64
    import boto3
    from datetime import datetime
    import pyarrow as pa
    import pyarrow.parquet as pq

    s3_client = boto3.client('s3')
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'amazon-raw-review-data-lake-prod')

    def lambda_handler(event, context):
        """
        Lambda function entry point for parsing Kinesis records and storing them in S3 as Parquet.
        """
        processed_records = []
        errors = []

        for record in event['Records']:
            # Kinesis data is base64 encoded
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            try:
                review_data = json.loads(payload)
                # Add ingestion timestamp
                review_data['ingestionTimestamp'] = datetime.utcnow().isoformat() + "Z"
                processed_records.append(review_data)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from Kinesis record: {e} - Payload: {payload}")
                errors.append({'payload': payload, 'error': str(e)})
            except Exception as e:
                print(f"Unexpected error processing Kinesis record: {e} - Payload: {payload}")
                errors.append({'payload': payload, 'error': str(e)})

        if processed_records:
            # Prepare data for Parquet
            # Define schema explicitly to ensure types are correct
            schema = pa.schema([
                ('reviewId', pa.string()),
                ('reviewerId', pa.string()),
                ('productASIN', pa.string()),
                ('timestamp', pa.timestamp('us')), # Use 'us' for microsecond precision
                ('orderId', pa.string()),
                ('reviewTitle', pa.string()),
                ('reviewText', pa.string()),
                ('overallRating', pa.int32()),
                ('ingestionTimestamp', pa.timestamp('us'))
            ])

            # Convert Python list of dicts to PyArrow Table
            # Handle potential missing keys by ensuring all fields exist, possibly with nulls
            # For simplicity, assuming all keys are present based on producer.
            table_data = {key: [d.get(key) for d in processed_records] for key in schema.names}
            table = pa.Table.from_pydict(table_data, schema=schema)

            # Determine S3 path with partitioning
            now = datetime.utcnow()
            year = now.year
            month = now.month
            day = now.day
            s3_key_prefix = f"reviews/year={year}/month={month:02}/day={day:02}/"
            file_name = f"reviews-{context.aws_request_id}-{now.strftime('%H%M%S%f')}.parquet"
            s3_path = f"{s3_key_prefix}{file_name}"

            # Write to a buffer and then upload to S3
            try:
                buf = pa.BufferOutputStream()
                pq.write_table(table, buf)
                s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=s3_path, Body=buf.getvalue())
                print(f"Successfully wrote {len(processed_records)} records to s3://{S3_BUCKET_NAME}/{s3_path}")
            except Exception as e:
                print(f"Error writing Parquet to S3: {e}")
                errors.append({'s3_path': s3_path, 'error': str(e)})
                raise

        if errors:
            print(f"Encountered {len(errors)} errors during processing.")
            # Depending on policy, you might want to send these to a Dead Letter Queue (DLQ)
            # For now, we'll just log and potentially re-raise if fatal.
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Errors occurred during processing.', 'errors': errors})
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps('Successfully processed and stored review data.')
            }

    # This part would be for local testing/development
    if __name__ == '__main__':
        # Example Kinesis event structure
        mock_event = {
            'Records': [
                {
                    'eventSource': 'aws:kinesis',
                    'eventID': 'shardId-000000000000:49540000000000000000000000000000000000000000000000000000',
                    'invokeIdentityArn': 'arn:aws:iam::123456789012:role/lambda_kinesis_processor_role',
                    'eventName': 'aws:kinesis:record',
                    'eventVersion': '1.0',
                    'eventSourceARN': 'arn:aws:kinesis:us-east-1:123456789012:stream/amazon-review-data-stream',
                    'awsRegion': 'us-east-1',
                    'kinesis': {
                        'kinesisSchemaVersion': '1.0',
                        'partitionKey': 'B08ABCD123',
                        'sequenceNumber': '49540000000000000000000000000000000000000000000000000000',
                        'data': base64.b64encode(json.dumps({
                            "reviewId": "R1234567890",
                            "reviewerId": "A1B2C3D4E5",
                            "productASIN": "B08ABCD123",
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "orderId": "O987654321",
                            "reviewTitle": "Great Product!",
                            "reviewText": "I really enjoyed using this product. It exceeded my expectations.",
                            "overallRating": 5
                        }).encode('utf-8')).decode('utf-8'),
                        'approximateArrivalTimestamp': 1678886400
                    }
                },
                {
                    'eventSource': 'aws:kinesis',
                    'eventID': 'shardId-000000000000:49540000000000000000000000000000000000000000000000000001',
                    'invokeIdentityArn': 'arn:aws:iam::123456789012:role/lambda_kinesis_processor_role',
                    'eventName': 'aws:kinesis:record',
                    'eventVersion': '1.0',
                    'eventSourceARN': 'arn:aws:kinesis:us-east-1:123456789012:stream/amazon-review-data-stream',
                    'awsRegion': 'us-east-1',
                    'kinesis': {
                        'kinesisSchemaVersion': '1.0',
                        'partitionKey': 'B09EFGH456',
                        'sequenceNumber': '49540000000000000000000000000000000000000000000000000001',
                        'data': base64.b64encode(json.dumps({
                            "reviewId": "R0987654321",
                            "reviewerId": "F6G7H8I9J0",
                            "productASIN": "B09EFGH456",
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "orderId": "O123456789",
                            "reviewTitle": "Disappointing",
                            "reviewText": "The quality was not what I expected. Would not recommend.",
                            "overallRating": 2
                        }).encode('utf-8')).decode('utf-8'),
                        'approximateArrivalTimestamp': 1678886401
                    }
                }
            ]
        }
        # Mock context object for local testing
        class MockContext:\n            def __init__(self):\n                self.aws_request_id = 'test-request-id'\n                self.function_name = 'test-function'\n
        # lambda_handler(mock_event, MockContext())\n        pass
    ```