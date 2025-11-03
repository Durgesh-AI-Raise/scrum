from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)

# In-memory store for reviewer activity for the current sprint
# { 'reviewer_id': [ { 'review_id': '...', 'timestamp': datetime_obj, 'rating': 5, 'product_id': '...', 'brand_id': '...', 'category_id': '...', 'is_verified_purchase': True }, ... ] }
reviewer_activities_store = defaultdict(list)

# Configuration for detection thresholds
CONFIG = {
    "short_time_window_hours": 24,
    "high_volume_reviews_threshold": 6, # More than 5 reviews in 24 hours
    "unverified_purchase_ratio_threshold": 0.7, # 70% unverified purchases
    "min_product_diversity_categories": 3, # Reviewer reviewed less than 3 categories
    "extreme_rating_percentage_threshold": 0.9, # 90% of reviews are 1 or 5 star
}

@app.route('/ingest_reviewer_activity', methods=['POST'])
def ingest_reviewer_activity():
    data = request.json
    required_fields = ['reviewer_id', 'review_id', 'timestamp', 'rating', 'product_id', 'brand_id', 'category_id', 'is_verified_purchase']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
    except ValueError:
        return jsonify({"error": "Invalid timestamp format. Use ISO format."}), 400

    reviewer_activities_store[data['reviewer_id']].append(data)
    # Optionally, implement a cleanup for old activities to prevent memory bloat
    # For now, assuming in-memory is fine for sprint goals.

    return jsonify({"status": "success", "message": "Reviewer activity ingested"}), 200

@app.route('/analyze_reviewer_activity/<string:reviewer_id>', methods=['GET'])
def analyze_reviewer_activity(reviewer_id):
    activities = reviewer_activities_store.get(reviewer_id, [])
    if not activities:
        return jsonify({"reviewer_id": reviewer_id, "detected_behaviors": [], "initial_score_contribution": 0}), 200

    detected_behaviors = []
    score_contribution = 0

    # Rule 1: High volume of reviews in a short time
    reviews_in_short_time_count = 0
    now = datetime.now()
    for activity in activities:
        if now - activity['timestamp'] < timedelta(hours=CONFIG["short_time_window_hours"]):
            reviews_in_short_time_count += 1
    if reviews_in_short_time_count >= CONFIG["high_volume_reviews_threshold"]:
        detected_behaviors.append("high_volume_reviews_short_time")
        score_contribution += 20

    # Rule 2: Unverified purchase ratio
    total_reviews = len(activities)
    unverified_count = sum(1 for activity in activities if not activity['is_verified_purchase'])
    if total_reviews > 0 and (unverified_count / total_reviews) >= CONFIG["unverified_purchase_ratio_threshold"]:
        detected_behaviors.append("high_unverified_purchase_ratio")
        score_contribution += 30

    # Rule 3: Low product diversity
    product_categories = set(activity['category_id'] for activity in activities)
    if len(product_categories) < CONFIG["min_product_diversity_categories"] and total_reviews >= CONFIG["min_product_diversity_categories"]:
        detected_behaviors.append("low_product_diversity")
        score_contribution += 15

    # Rule 4: Consistent extreme ratings (e.g., all 5-star or all 1-star)
    if total_reviews > 0:
        five_star_count = sum(1 for activity in activities if activity['rating'] == 5)
        one_star_count = sum(1 for activity in activities if activity['rating'] == 1)

        if (five_star_count / total_reviews >= CONFIG["extreme_rating_percentage_threshold"]) or \
           (one_star_count / total_reviews >= CONFIG["extreme_rating_percentage_threshold"]):
            detected_behaviors.append("consistent_extreme_ratings")
            score_contribution += 25

    return jsonify({
        "reviewer_id": reviewer_id,
        "detected_behaviors": detected_behaviors,
        "initial_score_contribution": score_contribution
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5002)
