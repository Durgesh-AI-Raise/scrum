from kafka import KafkaConsumer
import json
import psycopg2

# Database connection details
DB_HOST = "localhost"
DB_NAME = "aris_db"
DB_USER = "aris_user"
DB_PASSWORD = "aris_password"

def create_table_if_not_exists():
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id VARCHAR(255) PRIMARY KEY,
                product_id VARCHAR(255) NOT NULL,
                reviewer_id VARCHAR(255) NOT NULL,
                rating INTEGER NOT NULL,
                review_text TEXT NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                is_flagged BOOLEAN DEFAULT FALSE,
                flagged_reason TEXT
            );
        """)
        conn.commit()
        cur.close()
        print("Reviews table checked/created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        if conn:
            conn.close()

def insert_review(review_data):
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reviews (review_id, product_id, reviewer_id, rating, review_text, timestamp, is_flagged, flagged_reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (review_id) DO UPDATE SET
                product_id = EXCLUDED.product_id,
                reviewer_id = EXCLUDED.reviewer_id,
                rating = EXCLUDED.rating,
                review_text = EXCLUDED.review_text,
                timestamp = EXCLUDED.timestamp,
                is_flagged = EXCLUDED.is_flagged,
                flagged_reason = EXCLUDED.flagged_reason;
        """, (
            review_data['review_id'],
            review_data['product_id'],
            review_data['reviewer_id'],
            review_data['rating'],
            review_data['review_text'],
            review_data['timestamp'],
            review_data.get('is_flagged', False),
            review_data.get('flagged_reason', None)
        ))
        conn.commit()
        cur.close()
        # print(f"Review {review_data['review_id']} inserted/updated.")
    except Exception as e:
        print(f"Error inserting review {review_data.get('review_id', 'N/A')}: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_table_if_not_exists()
    consumer = KafkaConsumer(
        'amazon_reviews',
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='review_persister_group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    print("Starting review data consumer/persister...")
    for message in consumer:
        review_data = message.value
        print(f"Received review: {review_data['review_id']}")
        insert_review(review_data)