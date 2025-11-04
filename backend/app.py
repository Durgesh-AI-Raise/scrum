from flask import Flask, jsonify, send_from_directory
import psycopg2
import os

app = Flask(__name__, static_folder='../static', static_url_path='/static')

# Database connection details
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "aris_db")
DB_USER = os.getenv("DB_USER", "aris_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "aris_password")

def get_flagged_reviews_from_db():
    conn = None
    reviews = []
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        cur.execute(
            "SELECT review_id, product_id, reviewer_id, rating, review_text, timestamp, flagged_reason FROM reviews WHERE is_flagged = TRUE ORDER BY timestamp DESC;"
        )
        rows = cur.fetchall()
        for row in rows:
            reviews.append({
                "review_id": row[0],
                "product_id": row[1],
                "reviewer_id": row[2],
                "rating": row[3],
                "review_text": row[4],
                "timestamp": row[5].isoformat(),
                "flagged_reason": row[6]
            })
        cur.close()
    except Exception as e:
        print(f"Error retrieving flagged reviews: {e}")
    finally:
        if conn:
            conn.close()
    return reviews

@app.route('/api/flagged_reviews', methods=['GET'])
def get_flagged_reviews():
    flagged_reviews = get_flagged_reviews_from_db()
    return jsonify(flagged_reviews)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # For local development, use python app.py
    # In production, use a WSGI server like Gunicorn
    app.run(debug=True, port=5000)
