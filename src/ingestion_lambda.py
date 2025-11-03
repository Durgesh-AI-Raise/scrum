
import json
import os
import boto3
import psycopg2
import logging
from botocore.exceptions import ClientError # For S3 errors
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO').upper())

s3 = boto3.client('s3')

# Placeholder for database connection details (e.g., from environment variables)
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

def extract_review_data(raw_review_json):
    """
    Extracts and maps raw review JSON data to the target database schema.
    Performs basic data type conversions.
    """
    try:
        review_date_str = raw_review_json.get("review_date")
        review_date_obj = None
        if review_date_str:
            try:
                # Assuming ISO 8601 format for review_date
                review_date_obj = datetime.fromisoformat(review_date_str.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Could not parse review_date: {review_date_str}. Setting to None.")
                review_date_obj = None

        return {
            "review_id": raw_review_json.get("review_id"),
            "product_id": raw_review_json.get("product_id"),
            "reviewer_id": raw_review_json.get("reviewer_id"),
            "review_headline": raw_review_json.get("review_headline"),
            "review_body": raw_review_json.get("review_body"),
            "star_rating": int(raw_review_json.get("star_rating")) if raw_review_json.get("star_rating") is not None else None,
            "review_date": review_date_obj,
            "helpful_votes": int(raw_review_json.get("helpful_votes", 0)) if raw_review_json.get("helpful_votes") is not None else 0,
            "verified_purchase": bool(raw_review_json.get("verified_purchase")) if raw_review_json.get("verified_purchase") is not None else None,
            "product_category": raw_review_json.get("product_category"),
            "reviewer_profile_name": raw_review_json.get("reviewer_profile_name")
        }
    except Exception as e:
        logger.error(f"Error during data extraction for review: {raw_review_json}. Error: {e}", exc_info=True)
        raise # Re-raise to be caught by the main handler's try-except

def insert_review_to_db(cursor, extracted_data):
    """
    Inserts or updates a review record in the database.
    Uses ON CONFLICT to handle potential duplicates based on review_id.
    """
    insert_sql = """
    INSERT INTO reviews (review_id, product_id, reviewer_id, review_headline, review_body,
                         star_rating, review_date, helpful_votes, verified_purchase,
                         product_category, reviewer_profile_name)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (review_id) DO UPDATE SET
        product_id = EXCLUDED.product_id,
        reviewer_id = EXCLUDED.reviewer_id,
        review_headline = EXCLUDED.review_headline,
        review_body = EXCLUDED.review_body,
        star_rating = EXCLUDED.star_rating,
        review_date = EXCLUDED.review_date,
        helpful_votes = EXCLUDED.helpful_votes,
        verified_purchase = EXCLUDED.verified_purchase,
        product_category = EXCLUDED.product_category,
        reviewer_profile_name = EXCLUDED.reviewer_profile_name,
        ingestion_timestamp = CURRENT_TIMESTAMP;
    """
    try:
        cursor.execute(insert_sql, (
            extracted_data.get('review_id'),
            extracted_data.get('product_id'),
            extracted_data.get('reviewer_id'),
            extracted_data.get('review_headline'),
            extracted_data.get('review_body'),
            extracted_data.get('star_rating'),
            extracted_data.get('review_date'), # psycopg2 can handle datetime objects
            extracted_data.get('helpful_votes'),
            extracted_data.get('verified_purchase'),
            extracted_data.get('product_category'),
            extracted_data.get('reviewer_profile_name')
        ))
        logger.info(f"Successfully inserted/updated review: {extracted_data.get('review_id')}")
    except psycopg2.Error as db_error:
        # Log specific database errors
        logger.error(f"Database error inserting review {extracted_data.get('review_id')}: {db_error}", exc_info=True)
        raise
    except Exception as e:
        # Catch any other unexpected errors during insertion
        logger.error(f"Unexpected error inserting review {extracted_data.get('review_id')}: {e}", exc_info=True)
        raise


def lambda_handler(event, context):
    conn = None
    cursor = None
    s3_bucket = None
    s3_key = None
    try:
        # Establish database connection
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()
        logger.info("Database connection established.")

        for record in event['Records']:
            s3_bucket = record['s3']['bucket']['name']
            s3_key = record['s3']['object']['key']
            logger.info(f"Processing s3://{s3_bucket}/{s3_key}")

            try:
                # Retrieve file from S3
                response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
                file_content = response['Body'].read().decode('utf-8')
                reviews_data = json.loads(file_content)

                # Ensure reviews_data is always a list for consistent iteration
                if not isinstance(reviews_data, list):
                    reviews_data = [reviews_data]

                # Process each review within the file
                for raw_review in reviews_data:
                    try:
                        extracted_data = extract_review_data(raw_review)
                        insert_review_to_db(cursor, extracted_data)
                        conn.commit() # Commit after each review for better traceability and smaller transaction units
                    except Exception as review_processing_error:
                        logger.error(f"Failed to process individual review from {s3_key}. Review ID: {raw_review.get('review_id', 'N/A')}. Error: {review_processing_error}", exc_info=True)
                        conn.rollback() # Rollback changes for the current review if it failed
                        # Depending on the desired behavior, you might:
                        # 1. Continue to the next review (if individual failures are acceptable)
                        # 2. Re-raise to terminate the Lambda and send the original message to DLQ
                        # For now, we re-raise to ensure the file processing is marked as failed.
                        raise

            except ClientError as ce:
                # Handle S3 specific errors (e.g., file not found)
                if ce.response['Error']['Code'] == 'NoSuchKey':
                    logger.warning(f"S3 object not found: s3://{s3_bucket}/{s3_key}. It might have been deleted or moved.")
                else:
                    logger.error(f"S3 client error for s3://{s3_bucket}/{s3_key}: {ce}", exc_info=True)
                raise # Re-raise to trigger Lambda retry/DLQ
            except json.JSONDecodeError as jde:
                logger.error(f"JSON decoding error for s3://{s3_bucket}/{s3_key}. File content might be malformed: {jde}", exc_info=True)
                raise # Re-raise
            except Exception as file_processing_error:
                logger.error(f"Unhandled error while processing file s3://{s3_bucket}/{s3_key}: {file_processing_error}", exc_info=True)
                raise # Re-raise to ensure the Lambda invocation fails and potentially goes to DLQ

    except psycopg2.OperationalError as op_error:
        # Critical error related to database connectivity
        logger.critical(f"Database connection failed: {op_error}. Please check DB configuration and accessibility.", exc_info=True)
        raise # Critical error, re-raise to fail the Lambda
    except Exception as e:
        # Catch any other unhandled exceptions at the top level
        logger.critical(f"Unhandled exception in lambda_handler: {e}", exc_info=True)
        if conn:
            conn.rollback() # Ensure transaction is rolled back on any unhandled error
        raise # Re-raise to send to DLQ if configured

    finally:
        # Clean up database resources
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logger.info("Database connection closed.")

    return {
        'statusCode': 200,
        'body': json.dumps('Review data ingestion, extraction, and storage complete.')
    }
