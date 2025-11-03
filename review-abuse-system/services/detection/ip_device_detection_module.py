import psycopg2
import os
from datetime import datetime, timedelta
import json

# Database connection details (replace with actual credentials or env vars)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "review_abuse_db")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

# Configuration for IP/Device detection
DETECTION_WINDOW_HOURS = 24
IP_REVIEW_THRESHOLD = 5
DEVICE_REVIEW_THRESHOLD = 5

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    return conn

def store_flagged_pattern(cur, review_id, flag_type, severity, details):
    details_json = json.dumps(details)
    cur.execute(
        """
        INSERT INTO flagged_behavioral_patterns (review_id, flag_type, severity, details)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (review_id, flag_type) DO UPDATE SET
            severity = EXCLUDED.severity,
            details = EXCLUDED.details,
            detection_timestamp = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        RETURNING flag_id;
        """,
        (review_id, flag_type, severity, details_json)
    )
    flag_id = cur.fetchone()[0]
    print(f"Stored flag {flag_id} for review {review_id} of type {flag_type}")

def detect_multiple_reviews_ip_device():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        now = datetime.now()
        detection_start_time = now - timedelta(hours=DETECTION_WINDOW_HOURS)

        print(f"Running IP/Device detection for reviews between {detection_start_time} and {now}")

        # --- Detection for Multiple Reviews from Same IP ---
        cur.execute(
            """
            SELECT
                ip_address,
                COUNT(behavior_id) AS review_count,
                ARRAY_AGG(review_id ORDER BY submission_timestamp DESC) AS review_ids
            FROM review_behavioral_data
            WHERE submission_timestamp BETWEEN %s AND %s AND ip_address IS NOT NULL
            GROUP BY ip_address
            HAVING COUNT(behavior_id) >= %s;
            """,
            (detection_start_time, now, IP_REVIEW_THRESHOLD)
        )
        ip_flags = cur.fetchall()

        for ip_address, review_count, review_ids in ip_flags:
            details = {
                "ip_address": str(ip_address),
                "review_count": review_count,
                "detection_window_hours": DETECTION_WINDOW_HOURS,
                "threshold": IP_REVIEW_THRESHOLD,
                "sample_review_ids": review_ids[:5] # Store a few sample review IDs
            }
            # Use the most recent review_id from the aggregated list to associate the flag
            review_id_to_flag = review_ids[0] if review_ids else None
            if review_id_to_flag:
                print(f"Flagging IP: {ip_address} (review: {review_id_to_flag}) for multiple reviews. Count: {review_count}")
                store_flagged_pattern(cur, review_id_to_flag, 'multiple_reviews_ip', 'medium', details)
            else:
                print(f"Warning: No review_id found for IP {ip_address} to associate flag with.")

        # --- Detection for Multiple Reviews from Same Device ID ---
        cur.execute(
            """
            SELECT
                device_id,
                COUNT(behavior_id) AS review_count,
                ARRAY_AGG(review_id ORDER BY submission_timestamp DESC) AS review_ids
            FROM review_behavioral_data
            WHERE submission_timestamp BETWEEN %s AND %s AND device_id IS NOT NULL
            GROUP BY device_id
            HAVING COUNT(behavior_id) >= %s;
            """,
            (detection_start_time, now, DEVICE_REVIEW_THRESHOLD)
        )
        device_flags = cur.fetchall()

        for device_id, review_count, review_ids in device_flags:
            details = {
                "device_id": device_id,
                "review_count": review_count,
                "detection_window_hours": DETECTION_WINDOW_HOURS,
                "threshold": DEVICE_REVIEW_THRESHOLD,
                "sample_review_ids": review_ids[:5] # Store a few sample review IDs
            }
            # Use the most recent review_id from the aggregated list to associate the flag
            review_id_to_flag = review_ids[0] if review_ids else None
            if review_id_to_flag:
                print(f"Flagging Device ID: {device_id} (review: {review_id_to_flag}) for multiple reviews. Count: {review_count}")
                store_flagged_pattern(cur, review_id_to_flag, 'multiple_reviews_device', 'medium', details)
            else:
                print(f"Warning: No review_id found for device ID {device_id} to associate flag with.")

        conn.commit()
        cur.close()

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print(f"Database error during IP/Device detection: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during IP/Device detection: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    detect_multiple_reviews_ip_device()
