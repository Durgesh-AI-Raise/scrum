# backend/app/routes.py
from flask import Blueprint, jsonify, request
from .models import Review, db
from datetime import datetime

flagged_reviews_bp = Blueprint('flagged_reviews', __name__)

@flagged_reviews_bp.route('/api/flagged-reviews', methods=['GET'])
def get_flagged_reviews():
    """
    Retrieves all reviews marked as flagged.
    Supports basic filtering by manual_status if provided.
    """
    manual_status_filter = request.args.get('manual_status')

    try:
        query = Review.query.filter_by(is_flagged=True)

        if manual_status_filter and manual_status_filter != 'all':
            query = query.filter_by(manual_status=manual_status_filter)

        reviews = query.order_by(Review.flagged_at.desc()).all()
        results = []
        for review in reviews:
            results.append({
                'review_id': review.review_id,
                'product_id': review.product_id,
                'reviewer_id': review.reviewer_id,
                'review_text': review.review_text,
                'review_rating': review.review_rating,
                'review_date': review.review_date.isoformat(),
                'reviewer_ip': review.reviewer_ip,
                'is_flagged': review.is_flagged,
                'flag_reasons': review.flag_reasons,
                'manual_status': review.manual_status,
                'flagged_at': review.flagged_at.isoformat() if review.flagged_at else None,
                'ingested_at': review.ingested_at.isoformat()
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flagged_reviews_bp.route('/api/reviews/<string:review_id>', methods=['GET'])
def get_review_details(review_id):
    """
    Retrieves detailed information for a specific review.
    """
    review = Review.query.get(review_id)
    if not review:
        return jsonify({'message': 'Review not found'}), 404
    
    return jsonify({
        'review_id': review.review_id,
        'product_id': review.product_id,
        'reviewer_id': review.reviewer_id,
        'review_text': review.review_text,
        'review_rating': review.review_rating,
        'review_date': review.review_date.isoformat(),
        'reviewer_ip': review.reviewer_ip,
        'is_flagged': review.is_flagged,
        'flag_reasons': review.flag_reasons,
        'manual_status': review.manual_status,
        'flagged_at': review.flagged_at.isoformat() if review.flagged_at else None,
        'ingested_at': review.ingested_at.isoformat()
    }), 200


@flagged_reviews_bp.route('/api/reviews/<string:review_id>/status', methods=['PUT'])
def update_review_status(review_id):
    """
    Updates the manual classification status of a review.
    """
    data = request.get_json()
    new_status = data.get('manual_status')

    if not new_status or new_status not in ['pending', 'abusive', 'legitimate']:
        return jsonify({'message': 'Invalid status provided. Must be "pending", "abusive" or "legitimate".'}), 400

    review = Review.query.get(review_id)
    if not review:
        return jsonify({'message': 'Review not found'}), 404

    review.manual_status = new_status
    try:
        db.session.commit()
        return jsonify({'message': 'Review status updated successfully', 'review_id': review_id, 'new_status': new_status}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
