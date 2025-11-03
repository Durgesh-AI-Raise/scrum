import psycopg2
import os
import json
import requests # For calling the flagging service
from datetime import datetime, timedelta
import re # For regular expressions to find links

from flask import Flask

app = Flask(__name__) # Minimal Flask app if this module needs to be triggered via an endpoint or scheduler

# Database connection details
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "review_abuse_db")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

# Flagging Service URL
FLAGGING_SERVICE_URL = os.environ.get("FLAGGING_SERVICE_URL", "http://localhost:5002/flag-review")

# Regex for detecting URLs (simplified for MVP)
# This regex looks for http:// or https:// or www. followed by at least one word character and a dot.
URL_REGEX = r'(https?://|www\.)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[a-zA-Z0-9_.-/?=&%]*)?'
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

def detect_external_links():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        now = datetime.now()
        detection_start_time = now - timedelta(hours=DETECTION_WINDOW_HOURS)

        print(f"Running external link detection for reviews between {detection_start_time} and {now}")

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
            found_links = re.findall(URL_REGEX, review_text, re.IGNORECASE)

            if found_links:
                details = {
                    "found_links": list(set(found_links)), # Store unique links
                    "detection_window_hours": DETECTION_WINDOW_HOURS
                }
                print(f"Flagging review {review_id} for external links. Details: {details}")
                flag_review_via_service(review_id, 'external_link', 'medium', details)

        cur.close()
        conn.commit()

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print(f"Database error during external link detection: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during external link detection: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    detect_external_links()
