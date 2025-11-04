
import csv
import psycopg2
from datetime import datetime
import os

# Database connection details (replace with actual environment variables/config)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "review_abuse_db")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    return conn

def ingest_historical_reviews(file_path):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Create a temporary table for staging
        cur.execute(
            """
            CREATE TEMPORARY TABLE temp_reviews (
                review_id VARCHAR(255),
                product_id VARCHAR(255),
                reviewer_id VARCHAR(255),
                rating INTEGER,
                review_text TEXT,
                review_timestamp TIMESTAMP WITH TIME ZONE
            ) ON COMMIT DROP;
            """
        )
        conn.commit()

        # Use COPY FROM for efficient bulk insert into the temporary table
        with open(file_path, 'r', encoding='utf-8') as f:
            # Skip header if present
            next(f)
            cur.copy_from(f, 'temp_reviews', sep=',', columns=(
                'review_id', 'product_id', 'reviewer_id', 'rating', 'review_text', 'review_timestamp'
            ))
        conn.commit()

        # Insert from temporary table to main reviews table, handling conflicts
        cur.execute(
            """
            INSERT INTO reviews (review_id, product_id, reviewer_id, rating, review_text, review_timestamp, ingestion_timestamp)
            SELECT
                tr.review_id,
                tr.product_id,
                tr.reviewer_id,
                tr.rating,
                tr.review_text,
                tr.review_timestamp,
                CURRENT_TIMESTAMP
            FROM temp_reviews tr
            ON CONFLICT (review_id) DO UPDATE
            SET
                product_id = EXCLUDED.product_id,
                reviewer_id = EXCLUDED.reviewer_id,
                rating = EXCLUDED.rating,
                review_text = EXCLUDED.review_text,
                review_timestamp = EXCLUDED.review_timestamp,
                ingestion_timestamp = CURRENT_TIMESTAMP;
            """
        )
        conn.commit()
        print(f"Successfully ingested historical reviews from {file_path}")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error during historical ingestion: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == '__main__':
    # Example usage:
    # Create a dummy CSV file for testing
    dummy_csv_content = """review_id,product_id,reviewer_id,rating,review_text,review_timestamp
rev101,prodA,user1,5,"Great product, love it!",2023-01-15 10:00:00+00
rev102,prodB,user2,1,"Terrible experience.",2023-01-16 11:30:00+00
rev103,prodA,user3,4,"Good value for money.",2023-01-17 09:15:00+00
rev101,prodA,user1,5,"Updated review, still love it!",2023-01-15 10:00:00+00
"""
    with open("historical_reviews.csv", "w") as f:
        f.write(dummy_csv_content)

    ingest_historical_reviews("historical_reviews.csv")
