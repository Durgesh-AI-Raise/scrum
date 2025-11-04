from flask import Flask, jsonify, request
from services.data_ingestion.mock_db import mock_db
from datetime import datetime

app = Flask(__name__)

@app.route('/api/flagged_reviews/summary', methods=['GET'])
def get_flagged_reviews_summary():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    filtered_flagged_reviews = mock_db.flagged_reviews

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        filtered_flagged_reviews = [r for r in filtered_flagged_reviews if r['flag_timestamp'] >= start_date]
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        filtered_flagged_reviews = [r for r in filtered_flagged_reviews if r['flag_timestamp'] <= end_date]

    # Convert datetime objects to string for JSON serialization
    serializable_flagged_reviews = [
        {k: v.isoformat() if isinstance(v, datetime) else v for k, v in review.items()}
        for review in filtered_flagged_reviews
    ]

    return jsonify({
        'total_flagged_reviews': len(serializable_flagged_reviews),
        'flagged_reviews': serializable_flagged_reviews
    })

@app.route('/api/reviews/<review_id>', methods=['GET'])
def get_review_details(review_id):
    review = mock_db.get_review(review_id)
    if review:
        serializable_review = {k: v.isoformat() if isinstance(v, datetime) else v for k, v in review.items()}
        return jsonify(serializable_review)
    return jsonify({'message': 'Review not found'}), 404

@app.route('/api/suspicious_accounts', methods=['GET'])
def get_suspicious_accounts():
    # Convert datetime objects to string for JSON serialization
    serializable_accounts = [
        {k: v.isoformat() if isinstance(v, datetime) else v for k, v in account.items()}
        for account in mock_db.suspicious_accounts
    ]
    return jsonify({
        'total_suspicious_accounts': len(serializable_accounts),
        'suspicious_accounts': serializable_accounts
    })

if __name__ == '__main__':
    # For demonstration, let's ingest some data and flag some reviews/accounts
    # This would typically happen via the ingestion pipeline, not in the API startup
    from services.data_ingestion.ingest_reviews import ingest_review_data
    from services.detection.review_flagging_service import review_flagging_service
    from services.detection.account_flagging_service import account_flagging_service
    
    # Clear mock_db for clean test runs
    mock_db.reviews = []
    mock_db.flagged_reviews = []
    mock_db.suspicious_accounts = []

    print("Ingesting sample review data...")
    ingest_review_data(filepath='data/sample_reviews.csv')

    print("Flagging reviews...")
    for review in mock_db.reviews:
        review_flagging_service.flag_review(review)

    print("Detecting suspicious accounts...")
    account_flagging_service.detect_suspicious_accounts()

    print("Starting Flask API...")
    app.run(debug=True, port=5000)