from flask import Blueprint, jsonify
from src.repositories.flagged_review_repository import FlaggedReviewRepository
from src.models.flagged_review import FlaggedReview
from datetime import datetime

# Initialize the repository globally for simplicity in this MVP
# In a production environment, consider dependency injection.
flagged_review_repo = FlaggedReviewRepository()

# Simulate some data for testing the API
# In a real scenario, data would come from the ingestion service.
initial_flagged_reviews_data = [
    {
        'review_id': 'api_review_001',
        'product_id': 'prodX',
        'user_id': 'user101',
        'rating': 1,
        'review_content': 'This product is absolutely terrible and broke on first use. I would not recommend it to anyone looking for a durable item.',
        'review_timestamp': datetime(2023, 10, 20, 10, 0, 0),
        'flagging_timestamp': datetime(2023, 11, 1, 14, 30, 0),
        'severity': 'HIGH',
        'reasons': [{'rule_id': 'velocity_spike_1', 'description': 'Reviews from new accounts for a single product with high velocity.', 'flag_reason': 'Suspicious review velocity for new accounts.'}],
        'status': 'FLAGGED'
    },
    {
        'review_id': 'api_review_002',
        'product_id': 'prodY',
        'user_id': 'user102',
        'rating': 5,
        'review_content': 'Excellent product, highly recommended to everyone interested in quality and performance. Exceeded all my expectations.',
        'review_timestamp': datetime(2023, 9, 15, 11, 0, 0),
        'flagging_timestamp': datetime(2023, 11, 1, 15, 0, 0),
        'severity': 'MEDIUM',
        'reasons': [{'rule_id': 'identical_content_1', 'description': 'Identical review content across multiple reviews.', 'flag_reason': 'Identical review content found across multiple reviews.'}],
        'status': 'FLAGGED'
    },
    {
        'review_id': 'api_review_003',
        'product_id': 'prodZ',
        'user_id': 'user103',
        'rating': 2,
        'review_content': 'Not worth the price. The features promised are not delivered as advertised, very disappointing overall experience.',
        'review_timestamp': datetime(2023, 10, 28, 9, 0, 0),
        'flagging_timestamp': datetime(2023, 11, 2, 9, 30, 0),
        'severity': 'MEDIUM',
        'reasons': [{'rule_id': 'low_rating_new_product', 'description': 'Low rating reviews on newly launched products from new accounts.', 'flag_reason': 'Low rating from new account on new product.'}],
        'status': 'FLAGGED'
    }
]

for data in initial_flagged_reviews_data:
    flagged_review_repo.save(FlaggedReview(**data))


api_bp = Blueprint('api', __name__)

@api_bp.route('/flagged-reviews', methods=['GET'])
def get_flagged_reviews():
    reviews = flagged_review_repo.get_all()
    serialized_reviews = []
    for review in reviews:
        # Create a snippet of the review content
        snippet = review.review_content[:100] + '...' if len(review.review_content) > 100 else review.review_content
        serialized_reviews.append({
            'review_id': review.review_id,
            'product_id': review.product_id,
            'user_id': review.user_id,
            'rating': review.rating,
            'review_content_snippet': snippet,
            'flagging_reasons': [r['flag_reason'] for r in review.reasons], # Extract just the flag_reason strings
            'severity': review.severity,
            'flagged_on': review.flagging_timestamp.isoformat(),
            'status': review.status
        })
    return jsonify(serialized_reviews)
