import psycopg2
import os
from datetime import datetime, timedelta
import json

# Database connection details (replace with actual credentials or env vars)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "review_abuse_db")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

# Configuration for spike detection
BASELINE_PERIOD_DAYS = 7
CURRENT_PERIOD_HOURS = 1
SPIKE_THRESHOLD_FACTOR = 3 # Current rate > SPIKE_THRESHOLD_FACTOR * Baseline Rate
MIN_REVIEWS_FOR_BASELINE = 10 # Minimum reviews in baseline period to calculate

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

def detect_sudden_spikes():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        now = datetime.now()
        current_period_start = now - timedelta(hours=CURRENT_PERIOD_HOURS)
        baseline_period_end = now
        baseline_period_start = now - timedelta(days=BASELINE_PERIOD_DAYS)

        print(f"Running spike detection for current period: {current_period_start} to {now}")
        print(f"Baseline period: {baseline_period_start} to {baseline_period_end}")

        # --- Detection for Reviewer Spikes ---
        cur.execute(
            """
            WITH reviewer_current_activity AS (
                SELECT
                    reviewer_id,
                    COUNT(behavior_id) AS current_reviews_count
                FROM review_behavioral_data
                WHERE submission_timestamp BETWEEN %s AND %s
                GROUP BY reviewer_id
            ),
            reviewer_baseline_activity AS (
                SELECT
                    reviewer_id,
                    COUNT(behavior_id) AS baseline_reviews_total,
                    COUNT(behavior_id) / %s AS avg_baseline_reviews_per_hour
                FROM review_behavioral_data
                WHERE submission_timestamp BETWEEN %s AND %s
                GROUP BY reviewer_id
            )
            SELECT
                rca.reviewer_id,
                rca.current_reviews_count,
                rba.avg_baseline_reviews_per_hour
            FROM reviewer_current_activity rca
            JOIN reviewer_baseline_activity rba ON rca.reviewer_id = rba.reviewer_id
            WHERE rca.current_reviews_count > rba.avg_baseline_reviews_per_hour * %s
              AND rba.baseline_reviews_total >= %s;
            """,
            (current_period_start, now, BASELINE_PERIOD_DAYS * 24, baseline_period_start, baseline_period_end, SPIKE_THRESHOLD_FACTOR, MIN_REVIEWS_FOR_BASELINE)
        )
        reviewer_spikes = cur.fetchall()

        for reviewer_id, current_reviews, avg_baseline_reviews in reviewer_spikes:
            details = {
                "current_reviews_in_period": current_reviews,
                "avg_baseline_reviews_per_hour": avg_baseline_reviews,
                "current_period_hours": CURRENT_PERIOD_HOURS,
                "baseline_period_days": BASELINE_PERIOD_DAYS,
                "spike_threshold_factor": SPIKE_THRESHOLD_FACTOR
            }
            # Get a recent review_id by this reviewer to associate the flag with
            cur.execute("SELECT review_id FROM review_behavioral_data WHERE reviewer_id = %s ORDER BY submission_timestamp DESC LIMIT 1", (reviewer_id,))
            associated_review = cur.fetchone()
            if associated_review:
                review_id_to_flag = associated_review[0]
                print(f"Flagging reviewer_id: {reviewer_id} (review: {review_id_to_flag}) for sudden spike. Current: {current_reviews}, Baseline Avg/Hr: {avg_baseline_reviews:.2f}")
                store_flagged_pattern(cur, review_id_to_flag, 'sudden_reviewer_spike', 'high', details)
            else:
                print(f"Warning: Could not find a review_id for reviewer {reviewer_id} to associate spike flag with.")

            conn.commit()
            cur.close()

        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            print(f"Database error during spike detection: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during spike detection: {e}")
        finally:
            if conn:
                conn.close()

    if __name__ == '__main__':
        detect_sudden_spikes()
