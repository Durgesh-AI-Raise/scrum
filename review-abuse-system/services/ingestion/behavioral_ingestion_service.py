from flask import Flask, request, jsonify
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

# Database connection details (replace with actual credentials or env vars)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "review_abuse_db")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    return conn

@app.route('/ingest-behavioral-data', methods=['POST'])
def ingest_behavioral_data():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ["review_id", "reviewer_id", "submission_timestamp"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400

    review_id = data.get("review_id")
    reviewer_id = data.get("reviewer_id")
    device_id = data.get("device_id")
    ip_address = data.get("ip_address")
    submission_timestamp_str = data.get("submission_timestamp")

    try:
        submission_timestamp = datetime.fromisoformat(submission_timestamp_str.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": "Invalid submission_timestamp format. Use ISO 8601."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO review_behavioral_data (review_id, reviewer_id, device_id, ip_address, submission_timestamp)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (review_id) DO UPDATE SET
                reviewer_id = EXCLUDED.reviewer_id,
                device_id = EXCLUDED.device_id,
                ip_address = EXCLUDED.ip_address,
                submission_timestamp = EXCLUDED.submission_timestamp,
                updated_at = CURRENT_TIMESTAMP
            RETURNING behavior_id;
            """,
            (review_id, reviewer_id, device_id, ip_address, submission_timestamp)
        )
        behavior_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return jsonify({"message": "Behavioral data ingested successfully", "behavior_id": behavior_id}), 201
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        app.logger.error(f"Database error during ingestion: {e}")
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # For local development, install flask and psycopg2-binary
    # pip install Flask psycopg2-binary
    app.run(debug=True, host='0.0.0.0', port=5001)
