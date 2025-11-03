from flask import Flask, request, jsonify
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

# In-memory stores for final suspicion scores
# { 'entity_id': { 'score': float, 'reasons': list[str], 'last_updated': datetime } }
review_scores = defaultdict(lambda: {'score': 0.0, 'reasons': [], 'last_updated': None})
reviewer_scores = defaultdict(lambda: {'score': 0.0, 'reasons': [], 'last_updated': None})
seller_scores = defaultdict(lambda: {'score': 0.0, 'reasons': [], 'last_updated': None})

@app.route('/score/review', methods=['POST'])
def score_review():
    data = request.json
    review_id = data.get('review_id')
    detected_patterns = data.get('detected_patterns', [])
    initial_score_contribution = data.get('initial_score_contribution', 0)

    if not review_id:
        return jsonify({"error": "Missing review_id"}), 400

    current_score_profile = review_scores[review_id]
    current_score_profile['score'] = initial_score_contribution
    current_score_profile['reasons'] = detected_patterns
    current_score_profile['last_updated'] = datetime.now()

    return jsonify({
        "review_id": review_id,
        "final_score": current_score_profile['score'],
        "reasons": current_score_profile['reasons']
    }), 200

@app.route('/score/reviewer', methods=['POST'])
def score_reviewer():
    data = request.json
    reviewer_id = data.get('reviewer_id')
    detected_behaviors = data.get('detected_behaviors', [])
    initial_score_contribution = data.get('initial_score_contribution', 0)

    if not reviewer_id:
        return jsonify({"error": "Missing reviewer_id"}), 400

    current_score_profile = reviewer_scores[reviewer_id]
    current_score_profile['score'] = initial_score_contribution
    current_score_profile['reasons'] = detected_behaviors
    current_score_profile['last_updated'] = datetime.now()

    return jsonify({
        "reviewer_id": reviewer_id,
        "final_score": current_score_profile['score'],
        "reasons": current_score_profile['reasons']
    }), 200

@app.route('/score/seller', methods=['POST'])
def score_seller():
    data = request.json
    seller_id = data.get('seller_id')
    seller_suspicion_score = data.get('seller_suspicion_score', 0)
    flagged_reasons = data.get('flagged_reasons', [])

    if not seller_id:
        return jsonify({"error": "Missing seller_id"}), 400

    current_score_profile = seller_scores[seller_id]
    current_score_profile['score'] = seller_suspicion_score
    current_score_profile['reasons'] = flagged_reasons
    current_score_profile['last_updated'] = datetime.now()

    return jsonify({
        "seller_id": seller_id,
        "final_score": current_score_profile['score'],
        "reasons": current_score_profile['reasons']
    }), 200

# Endpoints to retrieve scores (for dashboard)
@app.route('/scores/reviews', methods=['GET'])
def get_review_scores():
    return jsonify({k: {**v, 'last_updated': v['last_updated'].isoformat() if v['last_updated'] else None} for k, v in review_scores.items()})

@app.route('/scores/reviewers', methods=['GET'])
def get_reviewer_scores():
    return jsonify({k: {**v, 'last_updated': v['last_updated'].isoformat() if v['last_updated'] else None} for k, v in reviewer_scores.items()})

@app.route('/scores/sellers', methods=['GET'])
def get_seller_scores():
    return jsonify({k: {**v, 'last_updated': v['last_updated'].isoformat() if v['last_updated'] else None} for k, v in seller_scores.items()})


if __name__ == '__main__':
    app.run(debug=True, port=5004)
