import os
import psycopg2
from psycopg2 import sql
from datetime import datetime

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "amazon_reviews"),
        user=os.getenv("DB_USER", "user"),
        password=os.getenv("DB_PASSWORD", "password")
    )
    return conn

def insert_reviews(reviews_data):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        insert_query = sql.SQL("""
            INSERT INTO reviews (asin, reviewer_id, rating, review_text, submission_date, verified_purchase)
            VALUES (%s, %s, %s, %s, %s, %s)
        """)
        for review in reviews_data:
            cur.execute(insert_query, (
                review["asin"],
                review["reviewer_id"],
                review["rating"],
                review["review_text"],
                review["submission_date"],
                review["verified_purchase"]
            ))
        conn.commit()
        print(f"Successfully inserted {len(reviews_data)} reviews.")
    except Exception as e:
        print(f"Error inserting reviews: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()