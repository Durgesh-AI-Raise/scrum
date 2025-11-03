from flask import Flask, request, jsonify
from datetime import datetime
import os

from backend.db_models import DBClient
from backend.flagging_logic import flag_review

app = Flask(__name__)
db_client = DBClient() 

@app.route('/ingest-review', methods=['POST'])
def ingest_review():
    review_data = request.get_json()
    if not review_data:
        return jsonify({"error": "No review data provided"}), 400

    # Basic validation (can be expanded)
    required_fields = ["review_id", "product_id", "user_id", "review_text", "rating", "submission_date"]
    if not all(field in review_data for field in required_fields):
        return jsonify({"error": "Missing required review fields"}), 400

    flagged_review_data = flag_review(review_data, db_client)
    db_client.save_review(flagged_review_data)

    print(f"Processed review: {review_data['review_id']} - Flagged: {flagged_review_data['is_flagged']}")
    return jsonify({"status": "Review processed", "review_id": review_data['review_id'], "is_flagged": flagged_review_data['is_flagged']}), 200

@app.route('/flagged-reviews', methods=['GET'])
def get_flagged_reviews():
    flagged_reviews = db_client.get_flagged_reviews()
    return jsonify(flagged_reviews), 200


if __name__ == '__main__':
    # In a production environment, use a proper WSGI server like Gunicorn
    app.run(debug=True, host='0.0.0.0', port=5000)
