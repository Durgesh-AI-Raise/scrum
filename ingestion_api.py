
from flask import Flask, request, jsonify
from datetime import datetime
import psycopg2
import os

app = Flask(__name__)

# Database connection details (replace with actual environment variables/config)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "review_abuse_db")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    return conn

@app.route('/reviews', methods=['POST'])
def ingest_review():
    review_data = request.get_json()

    # Basic validation
    required_fields = ['review_id', 'product_id', 'reviewer_id', 'rating', 'review_text']
    if not all(field in review_data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    if not 1 <= review_data['rating'] <= 5:
        return jsonify({"error": "Rating must be between 1 and 5"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Extract IP address from request (simple example, robust solution needed for production)
        ip_address = request.remote_addr

        cur.execute(
            """
            INSERT INTO reviews (review_id, product_id, reviewer_id, rating, review_text, review_timestamp, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (review_id) DO UPDATE
            SET
                product_id = EXCLUDED.product_id,
                reviewer_id = EXCLUDED.reviewer_id,
                rating = EXCLUDED.rating,
                review_text = EXCLUDED.review_text,
                review_timestamp = EXCLUDED.review_timestamp,
                ip_address = EXCLUDED.ip_address,
                ingestion_timestamp = CURRENT_TIMESTAMP;
            """,
            (
                review_data['review_id'],
                review_data['product_id'],
                review_data['reviewer_id'],
                review_data['rating'],
                review_data['review_text'],
                review_data.get('review_timestamp', datetime.now()), # Use provided timestamp or current
                ip_address
            )
        )
        conn.commit()

        # TODO: Trigger asynchronous sentiment analysis, keyword stuffing detection, and rule engine evaluation
        # Example: send_to_message_queue({'type': 'new_review', 'review_id': review_data['review_id']})

        return jsonify({"message": "Review ingested successfully", "review_id": review_data['review_id']}), 201

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"error": "Review ID already exists"}), 409
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
