# detection_service/frequency_detector.py

from kafka import KafkaConsumer
import json
import psycopg2
import datetime

# Configuration
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC_REVIEWS = "amazon_reviews_raw"
DB_HOST = "localhost"
DB_NAME = "review_abuse_db"
DB_USER = "user"
DB_PASSWORD = "password"

# Frequency thresholds (example values, these would be configurable)
REVIEWER_MAX_REVIEWS_PER_DAY = 5
PRODUCT_MAX_REVIEWS_PER_HOUR = 20

consumer = KafkaConsumer(
    KAFKA_TOPIC_REVIEWS,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='latest',
    enable_auto_commit=True,
    group_id='frequency-detector-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)

def detect_unusual_frequency(review):
    """
    Detects unusual frequency patterns for a given review.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        reviewer_id = review['reviewerId']
        product_id = review['productId']
        review_date_str = review['reviewDate']
        review_id = review['reviewId']

        # Ensure review_date is a datetime object for comparison
        review_date = datetime.datetime.fromisoformat(review_date_str)

        flagged = False
        reasons = []
        abuse_score_increment = 0.0

        # Check reviewer's review frequency (e.g., reviews in the last 24 hours)
        time_window_start_reviewer = review_date - datetime.timedelta(days=1)
        cur.execute(
            "SELECT COUNT(*) FROM reviews WHERE reviewer_id = %s AND review_date >= %s;",
            (reviewer_id, time_window_start_reviewer)
        )
        reviewer_recent_reviews_count = cur.fetchone()[0]

        if reviewer_recent_reviews_count >= REVIEWER_MAX_REVIEWS_PER_DAY:
            flagged = True
            reasons.append("Unusual_Reviewer_Frequency")
            abuse_score_increment += 0.3

        # Check product's review frequency (e.g., reviews in the last 1 hour)
        time_window_start_product = review_date - datetime.timedelta(hours=1)
        cur.execute(
            "SELECT COUNT(*) FROM reviews WHERE product_id = %s AND review_date >= %s;",
            (product_id, time_window_start_product)
        )
        product_recent_reviews_count = cur.fetchone()[0]

        if product_recent_reviews_count >= PRODUCT_MAX_REVIEWS_PER_HOUR:
            flagged = True
            reasons.append("Unusual_Product_Review_Spike")
            abuse_score_increment += 0.2

        if flagged:
            print(f"Flagging review {review_id} for unusual frequency. Reasons: {reasons}")
            # Update the review in the database
            cur.execute(
                """
                UPDATE reviews
                SET is_flagged = TRUE,
                    flagging_reason = array_append(flagging_reason, %s),
                    flagging_timestamp = %s,
                    abuse_score = abuse_score + %s
                WHERE review_id = %s;
                """,
                (reasons[0], datetime.datetime.now(), abuse_score_increment, review_id)
            )
            conn.commit()
        else:
            print(f"Review {review_id} passed frequency checks.")

    except psycopg2.Error as e:
        print(f"Database error in frequency detection for review {review.get('reviewId')}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in frequency detection: {e}")
    finally:
        if conn:
            conn.close()

def run_frequency_detector():
    print("Starting frequency detection module...")
    for message in consumer:
        review = message.value
        print(f"Processing review for frequency detection: {review.get('reviewId')}")
        detect_unusual_frequency(review)

if __name__ == "__main__":
    run_frequency_detector()