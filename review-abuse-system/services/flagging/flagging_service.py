from flask import Flask, request, jsonify
import psycopg2
import os
import json

app = Flask(__name__)

# Database connection details
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "review_abuse_db")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    return conn

@app.route('/flag-review', methods=['POST'])
def flag_review():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ["review_id", "flag_type", "severity"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400

    review_id = data.get("review_id")
    flag_type = data.get("flag_type")
    severity = data.get("severity")
    details = data.get("details", {}) # Optional, defaults to empty dict

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
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
        conn.commit()
        cur.close()
        return jsonify({"message": "Review flagged successfully", "flag_id": flag_id}), 201
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        app.logger.error(f"Database error during flagging: {e}")
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred during flagging: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # For local development, install flask and psycopg2-binary
    # pip install Flask psycopg2-binary
    app.run(debug=True, host='0.0.0.0', port=5002)
