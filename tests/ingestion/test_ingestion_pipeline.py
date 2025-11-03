import pytest
import json
import os
import base64
from datetime import datetime, timezone
from unittest.mock import patch

# Import the Lambda handlers for testing
# Assuming the files are in src/ingestion and src/processing
from src.ingestion.review_stream_producer import lambda_handler as producer_lambda_handler
from src.processing.review_data_parser import lambda_handler as parser_lambda_handler

# Mock AWS credentials for moto
@pytest.fixture(scope="session")
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture
def kinesis_mock(aws_credentials):
    from moto import mock_aws
    with mock_aws():
        yield

@pytest.fixture
def s3_mock(aws_credentials):
    from moto import mock_aws
    with mock_aws():
        yield

@pytest.fixture
def create_mock_kinesis_stream(kinesis_mock):
    import boto3
    kinesis_client = boto3.client("kinesis", region_name="us-east-1")
    stream_name = "amazon-review-data-stream"
    try:
        kinesis_client.create_stream(StreamName=stream_name, ShardCount=1)
    except kinesis_client.exceptions.ResourceInUseException:
        pass # Stream already exists (e.g., from a previous test run in the same mock scope)
    os.environ["KINESIS_STREAM_NAME"] = stream_name
    return kinesis_client

@pytest.fixture
def create_mock_s3_bucket(s3_mock):
    import boto3
    s3_client = boto3.client("s3", region_name="us-east-1")
    bucket_name = "amazon-raw-review-data-lake-prod"
    s3_client.create_bucket(Bucket=bucket_name)
    os.environ["S3_BUCKET_NAME"] = bucket_name
    return s3_client

# Mock context object for Lambda functions
class MockLambdaContext:
    def __init__(self):
        self.aws_request_id = "test-request-id-123"
        self.function_name = "test-lambda-function"
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-lambda-function"
        self.memory_limit_in_mb = 128
        self.log_group_name = "/aws/lambda/test-lambda-function"
        self.log_stream_name = "2023/10/26/[/$LATEST]abcdef12345"

# --- Unit Tests for Review Stream Producer (Task 1.2) ---
def test_producer_lambda_handler_sends_to_kinesis(create_mock_kinesis_stream):
    kinesis_client = create_mock_kinesis_stream
    mock_context = MockLambdaContext()

    # Call the producer lambda handler
    response = producer_lambda_handler({}, mock_context)

    assert response["statusCode"] == 200
    assert "Review ingestion process completed." in response["body"]

    # Verify records in Kinesis (mocked)
    stream_name = os.environ["KINESIS_STREAM_NAME"]
    shard_id = kinesis_client.describe_stream(StreamName=stream_name)["StreamDescription"]["Shards"][0]["ShardId"]
    
    shard_iterator = kinesis_client.get_shard_iterator(
        StreamName=stream_name,
        ShardId=shard_id,
        ShardIteratorType="TRIM_HORIZON"
    )["ShardIterator"]

    records_response = kinesis_client.get_records(ShardIterator=shard_iterator, Limit=10)
    records = records_response["Records"]

    assert len(records) > 0
    # Decode and check content of a record
    first_record_data = json.loads(base64.b64decode(records[0]["Data"]).decode("utf-8"))
    assert "reviewId" in first_record_data
    assert "reviewerId" in first_record_data

# --- Unit Tests for Review Data Parser (Task 1.4) ---
def test_parser_lambda_handler_writes_to_s3_parquet(create_mock_s3_bucket):
    s3_client = create_mock_s3_bucket
    mock_context = MockLambdaContext()

    # Simulate a Kinesis event with mock data
    mock_review_data = {
        "reviewId": "RTEST123",
        "reviewerId": "ATESTUSER",
        "productASIN": "B0TEST001",
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "orderId": "OTEST456",
        "reviewTitle": "Test Review",
        "reviewText": "This is a test review for the product.",
        "overallRating": 4
    }
    encoded_data = base64.b64encode(json.dumps(mock_review_data).encode("utf-8")).decode("utf-8")

    mock_event = {
        "Records": [
            {
                "eventSource": "aws:kinesis",
                "eventID": "shardId-000000000000:sequence-1",
                "kinesis": {
                    "data": encoded_data,
                    "partitionKey": "B0TEST001",
                    "approximateArrivalTimestamp": 1678886400.0,
                    "kinesisSchemaVersion": "1.0",
                    "sequenceNumber": "sequence-1"
                },
                "awsRegion": "us-east-1",
                "eventName": "aws:kinesis:record",
                "eventSourceARN": "arn:aws:kinesis:us-east-1:123456789012:stream/amazon-review-data-stream",
                "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda_kinesis_processor_role"
            }
        ]
    }

    # Call the parser lambda handler
    response = parser_lambda_handler(mock_event, mock_context)

    assert response["statusCode"] == 200
    assert "Successfully processed and stored review data." in response["body"]

    # Verify a Parquet file was written to S3 (mocked)
    bucket_name = os.environ["S3_BUCKET_NAME"]
    objects = s3_client.list_objects_v2(Bucket=bucket_name)["Contents"]
    
    assert len(objects) > 0
    parquet_file_key = objects[0]["Key"]
    assert parquet_file_key.endswith(".parquet")
    assert f"reviews/year={datetime.utcnow().year}/month={datetime.utcnow().month:02}/day={datetime.utcnow().day:02}/" in parquet_file_key

    # Optional: Download and verify content of the Parquet file (requires pyarrow locally)
    # obj = s3_client.get_object(Bucket=bucket_name, Key=parquet_file_key)
    # import pyarrow.parquet as pq
    # import io
    # table = pq.read_table(io.BytesIO(obj['Body'].read()))
    # df = table.to_pandas()
    # assert not df.empty
    # assert df['reviewId'].iloc[0] == "RTEST123"
    # assert 'ingestionTimestamp' in df.columns

# --- Integration Test (Producer -> Kinesis -> Parser -> S3) ---
def test_full_ingestion_pipeline_integration(create_mock_kinesis_stream, create_mock_s3_bucket):
    kinesis_client = create_mock_kinesis_stream
    s3_client = create_mock_s3_bucket
    mock_context = MockLambdaContext()

    # 1. Run Producer to put records into Kinesis (mocked)
    producer_response = producer_lambda_handler({}, mock_context)
    assert producer_response["statusCode"] == 200

    # 2. Retrieve records from Kinesis (mocked) to simulate parser's event input
    stream_name = os.environ["KINESIS_STREAM_NAME"]
    shard_id = kinesis_client.describe_stream(StreamName=stream_name)["StreamDescription"]["Shards"][0]["ShardId"]
    
    shard_iterator = kinesis_client.get_shard_iterator(
        StreamName=stream_name,
        ShardId=shard_id,
        ShardIteratorType="TRIM_HORIZON"
    )["ShardIterator"]

    # Get all available records, assuming they're produced quickly for test purposes
    records_response = kinesis_client.get_records(ShardIterator=shard_iterator, Limit=100)
    kinesis_records_for_parser = []
    for record in records_response["Records"]:
        kinesis_records_for_parser.append({
            "eventSource": "aws:kinesis",
            "eventID": f"shardId-000000000000:{record['sequenceNumber']}",
            "kinesis": {
                "data": record["Data"],
                "partitionKey": record["PartitionKey"],
                "approximateArrivalTimestamp": record["ApproximateArrivalTimestamp"],
                "kinesisSchemaVersion": "1.0",
                "sequenceNumber": record["sequenceNumber"]
            },
            "awsRegion": "us-east-1",
            "eventName": "aws:kinesis:record",
            "eventSourceARN": f"arn:aws:kinesis:us-east-1:123456789012:stream/{stream_name}",
            "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda_kinesis_processor_role"
        })
    
    # Ensure some records were produced
    assert len(kinesis_records_for_parser) > 0

    # 3. Simulate parser lambda being triggered by these Kinesis records
    parser_event = {"Records": kinesis_records_for_parser}
    parser_response = parser_lambda_handler(parser_event, mock_context)
    assert parser_response["statusCode"] == 200

    # 4. Verify Parquet files in S3 (mocked)
    bucket_name = os.environ["S3_BUCKET_NAME"]
    objects = s3_client.list_objects_v2(Bucket=bucket_name)["Contents"]
    
    assert len(objects) > 0
    parquet_file_key = objects[0]["Key"]
    assert parquet_file_key.endswith(".parquet")

    # Further validation (optional): Read the Parquet data and compare with expected
    # This part requires pyarrow installed in the test environment.
    # obj = s3_client.get_object(Bucket=bucket_name, Key=parquet_file_key)
    # import pyarrow.parquet as pq
    # import io
    # table = pq.read_table(io.BytesIO(obj['Body'].read()))
    # df = table.to_pandas()
    # assert not df.empty
    # assert len(df) == len(kinesis_records_for_parser) # Should match the number of processed records
    # assert 'reviewId' in df.columns
    # assert 'ingestionTimestamp' in df.columns