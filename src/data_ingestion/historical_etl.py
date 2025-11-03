
# src/data_ingestion/historical_etl.py
import os
import json
import boto3
import psycopg2
from datetime import datetime
import uuid

# --- Configuration ---
S3_HISTORICAL_BUCKET = os.environ.get('S3_HISTORICAL_BUCKET', 'amazon-review-integrity-guardian-historical')
S3_HISTORICAL_PREFIX = os.environ.get('S3_HISTORICAL_PREFIX', 'raw_reviews/') # e.g., 'raw_reviews/year=YYYY/month=MM/day=DD/'
S3_TEMP_STAGING_BUCKET = os.environ.get('S3_TEMP_STAGING_BUCKET', 'amazon-review-integrity-guardian-staging')
S3_TEMP_STAGING_PREFIX = 'transformed_historical/' # e.g., 'transformed_historical/year=YYYY/month=MM/day=DD/'

REDSHIFT_HOST = os.environ.get('REDSHIFT_HOST')
REDSHIFT_PORT = os.environ.get('REDSHIFT_PORT', '5439')
REDSHIFT_DB = os.environ.get('REDSHIFT_DB')
REDSHIFT_USER = os.environ.get('REDSHIFT_USER')
REDSHIFT_PASSWORD = os.environ.get('REDSHIFT_PASSWORD')
REDSHIFT_ROLE_ARN = os.environ.get('REDSHIFT_ROLE_ARN') # IAM Role for Redshift COPY from S3

s3_client = boto3.client('s3')

def get_redshift_connection():
    """Establishes and returns a Redshift database connection."""
    try:
        conn = psycopg2.connect(
            host=REDSHIFT_HOST,
            port=REDSHIFT_PORT,
            database=REDSHIFT_DB,
            user=REDSHIFT_USER,
            password=REDSHIFT_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Error connecting to Redshift: {e}")
        raise

def extract_from_s3(bucket: str, prefix: str):
    """
    Generates S3 object keys (file paths) for raw historical data.
    Assumes data is partitioned or directly under the prefix.
    """
    print(f"Extracting raw data from s3://{bucket}/{prefix}")
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
    for page in pages:
        if "Contents" in page:
            for obj in page['Contents']:
                # Filter for files, ignore directories (objects ending with /)
                if not obj['Key'].endswith('/'):
                    yield obj['Key']

def transform_record(raw_record: dict) -> dict:
    """
    Applies transformations to a single raw review record to match the Redshift schema.
    Handles data type conversions, renaming, and adds ingestion metadata.
    """
    transformed_record = {
        'review_id': raw_record.get('review_id') or str(uuid.uuid4()), # Generate if missing
        'user_id': raw_record.get('user_id'),
        'product_id': raw_record.get('product_id'),
        'seller_id': raw_record.get('seller_id', 'unknown'), # Default seller_id if not present
        'rating': int(raw_record.get('rating')) if raw_record.get('rating') is not None else None,
        'title': raw_record.get('title'),
        'content': raw_record.get('review_text') or raw_record.get('content'), # Handle potential varied field names
        'review_date': None,
        'is_verified_purchase': bool(raw_record.get('verified_purchase')) if raw_record.get('verified_purchase') is not None else None,
        'upvotes': int(raw_record.get('helpful_votes', 0)),
        'downvotes': int(raw_record.get('unhelpful_votes', 0)), # Assuming some historical might have this
        'source_ip': 'historical_batch_load', # Indicates source of ingestion
        'metadata': json.dumps(raw_record) # Store original raw record for auditing/flexibility
    }

    # Date parsing and formatting
    if raw_record.get('review_date'):
        try:
            # Handle common date formats, try ISO first, then others
            dt_obj = datetime.fromisoformat(raw_record['review_date'].replace('Z', '+00:00'))
            transformed_record['review_date'] = dt_obj.isoformat()
        except ValueError:
            print(f"Warning: Could not parse review_date '{raw_record['review_date']}' for review_id {transformed_record['review_id']}. Skipping date for this record.")
            transformed_record['review_date'] = None

    transformed_record['ingestion_timestamp'] = datetime.utcnow().isoformat()

    return transformed_record

def validate_transformed_record(record: dict) -> bool:
    """Performs basic validation on a transformed record."""
    required_fields = ['review_id', 'user_id', 'product_id', 'rating', 'content', 'review_date']
    if not all(record.get(field) is not None for field in required_fields):
        print(f"Validation Error: Missing required fields in record {record.get('review_id')}. Required: {required_fields}. Record: {record}")
        return False
    # Add more specific validation rules here if needed (e.g., rating range, content length)
    if not (1 <= record.get('rating') <= 5):
        print(f"Validation Error: Invalid rating {record.get('rating')} for review_id {record.get('review_id')}.")
        return False
    return True

def process_and_stage_data(raw_file_key: str):
    """
    Reads a raw file from S3, transforms its records, and stages the
    transformed data back to an S3 staging bucket.
    """
    print(f"Processing raw S3 file: s3://{S3_HISTORICAL_BUCKET}/{raw_file_key}")
    obj = s3_client.get_object(Bucket=S3_HISTORICAL_BUCKET, Key=raw_file_key)
    lines = obj['Body'].read().decode('utf-8').splitlines()

    transformed_records_batch = []
    for line_num, line in enumerate(lines):
        try:
            raw_record = json.loads(line)
            transformed = transform_record(raw_record)
            if validate_transformed_record(transformed):
                transformed_records_batch.append(transformed)
            else:
                print(f"Skipping invalid record from line {line_num+1} in {raw_file_key}")
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error in {raw_file_key}, line {line_num+1}: {e} - Line content: {line[:100]}...")
        except Exception as e:
            print(f"Unexpected error processing record from line {line_num+1} in {raw_file_key}: {e}")

    if not transformed_records_batch:
        print(f"No valid records to stage from {raw_file_key}.")
        return None

    # Write transformed data to a temporary S3 staging location
    # Partition by date for better Redshift COPY performance and management
    current_date_path = datetime.utcnow().strftime('%Y/%m/%d')
    staging_filename = f"part-{uuid.uuid4()}.json"
    s3_staging_key = f"{S3_TEMP_STAGING_PREFIX}{current_date_path}/{staging_filename}"

    s3_client.put_object(
        Bucket=S3_TEMP_STAGING_BUCKET,
        Key=s3_staging_key,
        Body='\n'.join(json.dumps(record) for record in transformed_records_batch).encode('utf-8')
    )
    print(f"Staged {len(transformed_records_batch)} records to s3://{S3_TEMP_STAGING_BUCKET}/{s3_staging_key}")
    return s3_staging_key, len(transformed_records_batch)


def load_to_redshift_via_s3_copy(s3_staging_key: str):
    """
    Loads data from an S3 staging file into the Redshift 'reviews' table
    using the efficient COPY command.
    """
    conn = None
    try:
        conn = get_redshift_connection()
        cursor = conn.cursor()
        print(f"Loading data from s3://{S3_TEMP_STAGING_BUCKET}/{s3_staging_key} into Redshift 'reviews' table.")

        # Ensure the Redshift table columns match the JSON keys in the staged data
        # Redshift's COPY FROM JSON 'auto' can map JSON keys to column names.
        copy_command = f"""
            COPY reviews FROM 's3://{S3_TEMP_STAGING_BUCKET}/{s3_staging_key}'
            IAM_ROLE '{REDSHIFT_ROLE_ARN}'
            FORMAT AS JSON 'auto' -- Assumes data is JSONL (one JSON per line)
            TIMEFORMAT 'auto'
            TRUNCATECOLUMNS
            ACCEPTINVCHARS;
        """
        cursor.execute(copy_command)
        conn.commit()
        print("Data loaded successfully into Redshift.")
    except Exception as e:
        print(f"Error loading data to Redshift for {s3_staging_key}: {e}")
        if conn:
            conn.rollback() # Rollback on error
        raise # Re-raise to indicate failure
    finally:
        if conn:
            conn.close()

def main_historical_etl_pipeline():
    """Main function to orchestrate the historical ETL process."""
    print("Starting historical data ETL pipeline...")
    total_files_processed = 0
    total_records_ingested = 0

    for raw_file_key in extract_from_s3(S3_HISTORICAL_BUCKET, S3_HISTORICAL_PREFIX):
        if not raw_file_key.lower().endswith(('.json', '.jsonl')):
            print(f"Skipping non-JSON/JSONL file: {raw_file_key}")
            continue

        try:
            staging_result = process_and_stage_data(raw_file_key)
            if staging_result:
                s3_staging_key, num_records = staging_result
                load_to_redshift_via_s3_copy(s3_staging_key)
                total_files_processed += 1
                total_records_ingested += num_records
        except Exception as e:
            print(f"Pipeline failed for raw file {raw_file_key}: {e}. Moving to next file (if configured for resilience).")
            # In a real system, more robust error handling (e.g., DLQ, retry mechanism) would be here.

    print(f"\nHistorical ETL pipeline completed.")
    print(f"Total files processed: {total_files_processed}")
    print(f"Total records ingested into Redshift: {total_records_ingested}")

if __name__ == "__main__":
    main_historical_etl_pipeline()
