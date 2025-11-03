import psycopg2
import os
import json
import requests # For calling the flagging service
from datetime import datetime, timedelta
import re # For regular expressions to find keywords

from flask import Flask

app = Flask(__name__) # Minimal Flask app if this module needs to be triggered via an endpoint or scheduler

# Database connection details
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "review_abuse_db")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

# Flagging Service URL
FLAGGING_SERVICE_URL = os.environ.get("FLAGGING_SERVICE_URL", "http://localhost:5002/flag-review")

# Keyword Stuffing Configuration
SUSPICIOUS_KEYWORDS = os.environ.get("SUSPICIOUS_KEYWORDS", "buy now, free offer, discount code, limited time, click here").split(',')
KEYWORD_COUNT_THRESHOLD = int(os.environ.get("KEYWORD_COUNT_THRESHOLD", "5"))
KEYWORD_DENSITY_THRESHOLD = float(os.environ.get("KEYWORD_DENSITY_THRESHOLD", "0.15")) # 15% of words are keywords
DETECTION_WINDOW_HOURS = int(os.environ.get("DETECTION_WINDOW_HOURS", "24"))

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    return conn

def flag_review_via_service(review_id, flag_type, severity, details):
    payload = {
        "review_id": review_id,
        "flag_type": flag_type,
        "severity": severity,
        "details": details
    }
    try:
        response = requests.post(FLAGGING_SERVICE_URL, json=payload)
        response.raise_for_status() # Raise an exception for HTTP errors
        print(f"Successfully flagged review {review_id} via service: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error flagging review {review_id} via service: {e}")

def detect_keyword_stuffing():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        now = datetime.now()
        detection_start_time = now - timedelta(hours=DETECTION_WINDOW_HOURS)

        print(f"Running keyword stuffing detection for reviews between {detection_start_time} and {now}")

        cur.execute(
            """
            SELECT
                review_id,
                review_text
            FROM review_content_data
            WHERE submission_timestamp BETWEEN %s AND %s;
            """,
            (detection_start_time, now)
        )
        reviews = cur.fetchall()

        for review_id, review_text in reviews:
            words = review_text.lower().split()
            total_words = len(words)
            if total_words == 0:
                continue

            found_keywords = []
            keyword_count = 0

            for keyword in SUSPICIOUS_KEYWORDS:
                # Use regex to find whole words to avoid partial matches
                matches = re.findall(r'\b' + re.escape(keyword.strip().lower()) + r'\b', review_text.lower())
                keyword_count += len(matches)
                if matches:
                    found_keywords.append(keyword.strip())

            keyword_density = keyword_count / total_words

            if keyword_count >= KEYWORD_COUNT_THRESHOLD or keyword_density >= KEYWORD_DENSITY_THRESHOLD:
                details = {
                    "keyword_count": keyword_count,
                    "keyword_density": keyword_density,
                    "found_keywords": list(set(found_keywords)), # Unique keywords
                    "total_words": total_words,
                    "threshold_count": KEYWORD_COUNT_THRESHOLD,
                    "threshold_density": KEYWORD_DENSITY_THRESHOLD
                }
                print(f"Flagging review {review_id} for keyword stuffing. Details: {details}")
                flag_review_via_service(review_id, 'keyword_stuffing', 'high', details)

        cur.close()
        conn.commit() # Commit any changes if the flagging service somehow fails and we need to retry or log

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print(f"Database error during keyword stuffing detection: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during keyword stuffing detection: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    detect_keyword_stuffing()
