import psycopg2
import csv
from datetime import datetime

def ingest_review_data(db_connection_string, csv_filepath):
    """
    Ingests review data from a CSV file into the PostgreSQL database.
    Assumes the CSV has the following columns in order:
    review_id, reviewer_id, product_id, rating, review_text, review_timestamp
    """
    conn = None
    try:
        conn = psycopg2.connect(db_connection_string)
        cur = conn.cursor()

        # Create a temporary table for bulk loading
        cur.execute("""
            CREATE TEMPORARY TABLE temp_reviews (
                review_id VARCHAR(255),
                reviewer_id VARCHAR(255),
                product_id VARCHAR(255),
                rating INT,
                review_text TEXT,
                review_timestamp TIMESTAMP WITH TIME ZONE
            ) ON COMMIT DROP;
        """)

        with open(csv_filepath, 'r', encoding='utf-8') as f:
            # Skip header row if present
            # For this example, let's assume the CSV might have a header,
            # but the copy_from function will expect data directly
            # If your CSV always has a header, you might need next(f) here.
            # For robust production, consider a CSV reader to parse and then insert.
            cur.copy_from(f, 'temp_reviews', sep=',', columns=(
                'review_id', 'reviewer_id', 'product_id', 'rating', 'review_text', 'review_timestamp'
            ))

        # Insert data from temporary table into actual reviews table
        # ON CONFLICT (review_id) DO UPDATE handles updates for existing reviews
        cur.execute("""
            INSERT INTO reviews (review_id, reviewer_id, product_id, rating, review_text, review_timestamp)
            SELECT review_id, reviewer_id, product_id, rating, review_text, review_timestamp
            FROM temp_reviews
            ON CONFLICT (review_id) DO UPDATE
            SET
                reviewer_id = EXCLUDED.reviewer_id,
                product_id = EXCLUDED.product_id,
                rating = EXCLUDED.rating,
                review_text = EXCLUDED.review_text,
                review_timestamp = EXCLUDED.review_timestamp,
                ingestion_timestamp = NOW(); -- Update ingestion timestamp on modification
        """)

        conn.commit()
        print("Review data ingested successfully.")

    except (Exception, psycopg2.Error) as error:
        print(f"Error while ingesting review data: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    # Example usage:
    # In a real application, these would come from environment variables or a configuration management system
    DB_CONNECTION_STRING = "dbname=abuse_detection user=admin password=password host=localhost port=5432"
    SAMPLE_CSV_PATH = "data/sample_reviews.csv" # Path to your simulated review data

    print(f"Attempting to ingest data from {SAMPLE_CSV_PATH}")
    ingest_review_data(DB_CONNECTION_STRING, SAMPLE_CSV_PATH)
