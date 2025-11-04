from kafka import KafkaConsumer
import json
import psycopg2
from abuse_detection.rules import ABUSE_KEYWORDS # Assuming rules.py is in the same package

# Database connection details (same as consumer.py)
DB_HOST = "localhost"
DB_NAME = "aris_db"
DB_USER = "aris_user"
DB_PASSWORD = "aris_password"

def update_review_flag_status(review_id, is_flagged, flagged_reason=None):
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE reviews
            SET is_flagged = %s, flagged_reason = %s
            WHERE review_id = %s;
            """,
            (is_flagged, flagged_reason, review_id)
        )
        conn.commit()
        cur.close()
        if is_flagged:
            print(f"Review {review_id} flagged for reason: {flagged_reason}")
        # else:
        #     print(f"Review {review_id} unflagged.")
    except Exception as e:
        print(f"Error updating flag status for review {review_id}: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    consumer = KafkaConsumer(
        'amazon_reviews',
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='abuse_detection_group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    print("Starting abuse detection service...")
    for message in consumer:
        review_data = message.value
        review_id = review_data['review_id']
        review_text = review_data['review_text'].lower()
        
        flagged = False
        reason = None
        for keyword in ABUSE_KEYWORDS:
            if keyword.lower() in review_text:
                flagged = True
                reason = f"Contains keyword: '{keyword}'"
                break
        
        update_review_flag_status(review_id, flagged, reason)