from flask import Flask, request, jsonify
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

# In-memory store for seller suspicion profiles
# { 'seller_id': { 'total_reviews_count': int, 'suspicious_reviews_count': int,
#                  'suspicious_reviewers_linked_count': int, 'reviews_by_suspicious_reviewers_count': int,
#                  'last_updated': datetime, 'seller_suspicion_score': float, 'flagged_reasons': list[str] } }
seller_suspicion_profiles = defaultdict(lambda: {
    'total_reviews_count': 0,
    'suspicious_reviews_count': 0,
    'suspicious_reviewers_linked_count': 0,
    'reviews_by_suspicious_reviewers_count': 0,
    'last_updated': None,
    'seller_suspicion_score': 0.0,
    'flagged_reasons': []
})

CONFIG = {
    "suspicious_review_ratio_threshold": 0.3, # 30% or more reviews are suspicious
    "reviews_by_suspicious_reviewers_ratio_threshold": 0.2, # 20% or more reviews from suspicious reviewers
    "min_reviews_for_seller_analysis": 10 # Minimum number of reviews for a seller to be analyzed
}

def calculate_seller_suspicion_score(seller_profile):
    score = 0
    flagged_reasons = []

    total_reviews = seller_profile['total_reviews_count']
    suspicious_reviews = seller_profile['suspicious_reviews_count']
    reviews_by_suspicious_reviewers = seller_profile['reviews_by_suspicious_reviewers_count']

    if total_reviews >= CONFIG["min_reviews_for_seller_analysis"]:
        # Rule 1: High ratio of suspicious reviews
        if (suspicious_reviews / total_reviews) >= CONFIG["suspicious_review_ratio_threshold"]:
            score += 40
            flagged_reasons.append("high_suspicious_review_ratio")

        # Rule 2: High ratio of reviews by suspicious reviewers
        if (reviews_by_suspicious_reviewers / total_reviews) >= CONFIG["reviews_by_suspicious_reviewers_ratio_threshold"]:
            score += 30
            flagged_reasons.append("high_reviews_by_suspicious_reviewers_ratio")

        # Rule 3: Direct link to many suspicious reviewers
        if seller_profile['suspicious_reviewers_linked_count'] >= 3:
            score += 20
            flagged_reasons.append("linked_to_multiple_suspicious_reviewers")

    return score, flagged_reasons

@app.route('/ingest_suspicious_review', methods=['POST'])
def ingest_suspicious_review():
    data = request.json
    review_id = data.get('review_id')
    product_id = data.get('product_id')
    seller_id = data.get('seller_id')
    suspicion_score = data.get('suspicion_score', 0)

    if not all([review_id, product_id, seller_id]):
        return jsonify({"error": "Missing required fields"}), 400

    profile = seller_suspicion_profiles[seller_id]
    profile['total_reviews_count'] += 1 # Assuming all reviews, even non-suspicious, pass through here for total count
    if suspicion_score > 0: # Only count reviews with a score > 0 as suspicious
        profile['suspicious_reviews_count'] += 1
    profile['last_updated'] = datetime.now()

    # Recalculate suspicion score and reasons
    profile['seller_suspicion_score'], profile['flagged_reasons'] = calculate_seller_suspicion_score(profile)

    return jsonify({"status": "success", "message": "Suspicious review ingested and seller profile updated"}), 200

@app.route('/ingest_suspicious_reviewer_link', methods=['POST'])
def ingest_suspicious_reviewer_link():
    data = request.json
    reviewer_id = data.get('reviewer_id')
    reviewed_seller_ids = data.get('reviewed_seller_ids', []) # List of seller_ids the suspicious reviewer reviewed
    reviewer_suspicion_score = data.get('suspicion_score', 0)

    if not reviewer_id or not reviewed_seller_ids or reviewer_suspicion_score == 0:
        return jsonify({"error": "Missing reviewer_id, reviewed_seller_ids, or reviewer_suspicion_score is zero"}), 400

    for seller_id in reviewed_seller_ids:
        profile = seller_suspicion_profiles[seller_id]
        # Only increment if this is the first time linking *this* suspicious reviewer to *this* seller
        # For simplicity in Sprint 1, we'll just count distinct suspicious reviewers linked.
        # In a real system, we'd need a more robust way to track unique links.
        if 'linked_reviewers' not in profile:
            profile['linked_reviewers'] = set()
        if reviewer_id not in profile['linked_reviewers']:
            profile['suspicious_reviewers_linked_count'] += 1
            profile['linked_reviewers'].add(reviewer_id)

        profile['reviews_by_suspicious_reviewers_count'] += 1 # Increment for each review by a suspicious reviewer for this seller
        profile['last_updated'] = datetime.now()

        # Recalculate suspicion score and reasons
        profile['seller_suspicion_score'], profile['flagged_reasons'] = calculate_seller_suspicion_score(profile)

    return jsonify({"status": "success", "message": "Suspicious reviewer link ingested and seller profiles updated"}), 200

@app.route('/analyze_seller_suspicion/<string:seller_id>', methods=['GET'])
def analyze_seller_suspicion(seller_id):
    profile = seller_suspicion_profiles.get(seller_id)
    if not profile:
        return jsonify({"seller_id": seller_id, "seller_suspicion_score": 0.0, "flagged_reasons": []}), 200

    # Remove the internal 'linked_reviewers' set before sending the response
    response_profile = profile.copy()
    response_profile.pop('linked_reviewers', None)
    response_profile['last_updated'] = response_profile['last_updated'].isoformat() if response_profile['last_updated'] else None

    return jsonify({
        "seller_id": seller_id,
        "total_reviews_count": response_profile['total_reviews_count'],
        "suspicious_reviews_count": response_profile['suspicious_reviews_count'],
        "suspicious_reviewers_linked_count": response_profile['suspicious_reviewers_linked_count'],
        "reviews_by_suspicious_reviewers_count": response_profile['reviews_by_suspicious_reviewers_count'],
        "seller_suspicion_score": response_profile['seller_suspicion_score'],
        "flagged_reasons": response_profile['flagged_reasons'],
        "last_updated": response_profile['last_updated']
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5003)
