import csv
import psycopg2
from datetime import datetime
import os

# Configuration (replace with actual connection details or environment variables)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "abuse_detection_db"),
    "user": os.getenv("DB_USER", "abuse_admin"),
    "password": os.getenv("DB_PASSWORD", "your_secure_password") # IMPORTANT: Use environment variable in production
}
HISTORICAL_DATA_PATH = "data/historical_reviews_subset.csv"

def load_historical_reviews(csv_filepath, db_config):
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        print(f"Loading data from {csv_filepath}...")

        with open(csv_filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                try:
                    # Basic Transformation and Validation
                    review_id = row.get('review_id')
                    product_id = row.get('product_id')
                    reviewer_id = row.get('reviewer_id')
                    review_text = row.get('review_text')
                    rating = int(row.get('rating')) if row.get('rating') else None
                    review_date_str = row.get('review_date')
                    review_date = datetime.strptime(review_date_str, '%Y-%m-%d %H:%M:%S') if review_date_str else None
                    verified_purchase = row.get('verified_purchase', 'FALSE').upper() == 'TRUE'

                    if not all([review_id, product_id, reviewer_id, review_date]):
                        print(f"Skipping record {i+1} due to missing critical fields: {row}")
                        continue
                    if rating is None or not (1 <= rating <= 5):
                        print(f"Skipping record {i+1} due to invalid rating: {row.get('rating')}")
                        continue

                    # Insert into reviews table, handling conflicts (e.g., duplicate review_id)
                    insert_sql = """
                    INSERT INTO reviews (review_id, product_id, reviewer_id, review_text, rating, review_date, verified_purchase)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (review_id) DO NOTHING;
                    """
                    cur.execute(insert_sql, (review_id, product_id, reviewer_id, review_text, rating, review_date, verified_purchase))

                except ValueError as ve:
                    print(f"Data type error in record {i+1}: {ve} - {row}")
                except Exception as e:
                    print(f"Error processing record {i+1}: {e} - {row}")

        conn.commit()
        print("Historical data ingestion complete.")

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    except FileNotFoundError:
        print(f"Error: Historical data file not found at {csv_filepath}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    # This part is for local testing and demonstration
    # In a real scenario, the CSV would be provided by an external source.
    dummy_csv_content = """review_id,product_id,reviewer_id,review_text,rating,review_date,verified_purchase
rev1001,prodA,userX,"Great product, very happy!",5,2023-01-15 10:30:00,TRUE
rev1002,prodB,userY,"Decent, but could be better.",3,2023-01-16 11:00:00,FALSE
rev1003,prodA,userZ,"Absolutely love it!",5,2023-01-15 10:45:00,TRUE
rev1004,prodC,userX,"Didn't work for me.",1,2023-01-17 09:15:00,TRUE
rev1005,prodA,userY,"Buyer beware, terrible quality.",2,2023-01-16 12:00:00,FALSE
"""
    os.makedirs('data', exist_ok=True)
    with open(HISTORICAL_DATA_PATH, 'w', encoding='utf-8') as f:
        f.write(dummy_csv_content)

    print("Dummy historical data created for testing.")
    load_historical_reviews(HISTORICAL_DATA_PATH, DB_CONFIG)
