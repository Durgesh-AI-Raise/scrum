# backend/dashboard_api.py
from flask import Flask, jsonify, request
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.orm import sessionmaker
from models import Base, Review, Reviewer, PurchaseHistory, FlaggedItem

app = Flask(__name__)

# Database setup (replace with your actual connection string)
DATABASE_URL = "postgresql://user:password@host:port/database"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

@app.route('/api/flagged-reviews', methods=['GET'])
def get_flagged_reviews():
    session = Session()
    try:
        query = session.query(FlaggedItem, Review).join(Review, FlaggedItem.item_id == Review.review_id).filter(FlaggedItem.item_type == 'review')

        reason_filter = request.args.get('reason')
        if reason_filter:
            query = query.filter(FlaggedItem.reason == reason_filter)

        sort_by = request.args.get('sort_by', 'timestamp')
        order = request.args.get('order', 'desc')

        if sort_by == 'timestamp':
            if order == 'asc':
                query = query.order_by(FlaggedItem.timestamp.asc())
            else:
                query = query.order_by(FlaggedItem.timestamp.desc())

        flagged_data = query.all()
        results = []
        for flagged_item, review in flagged_data:
            results.append({
                'flag_id': flagged_item.flag_id,
                'review_id': review.review_id,
                'reviewer_id': review.reviewer_id,
                'product_id': review.product_id,
                'review_text': review.review_text,
                'rating': review.rating,
                'review_date': review.review_date.isoformat(),
                'flagging_reason': flagged_item.reason,
                'flag_timestamp': flagged_item.timestamp.isoformat(),
                'status': flagged_item.status
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/reviewers/<int:reviewer_id>/reviews', methods=['GET'])
def get_reviewer_reviews(reviewer_id):
    session = Session()
    try:
        reviews = session.query(Review).filter_by(reviewer_id=reviewer_id).all()
        results = []
        for review in reviews:
            results.append({
                'review_id': review.review_id,
                'product_id': review.product_id,
                'review_text': review.review_text,
                'rating': review.rating,
                'review_date': review.review_date.isoformat(),
                'is_flagged': review.is_flagged,
                'flagging_reason': review.flagging_reason
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/reviewers/<int:reviewer_id>/purchases', methods=['GET'])
def get_reviewer_purchases(reviewer_id):
    session = Session()
    try:
        purchases = session.query(PurchaseHistory).filter_by(reviewer_id=reviewer_id).all()
        results = []
        for purchase in purchases:
            results.append({
                'purchase_id': purchase.purchase_id,
                'product_id': purchase.product_id,
                'purchase_date': purchase.purchase_date.isoformat(),
                'quantity': purchase.quantity,
                'price': float(purchase.price)
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/reviewers/<int:reviewer_id>', methods=['GET'])
def get_reviewer_details(reviewer_id):
    session = Session()
    try:
        reviewer = session.query(Reviewer).filter_by(reviewer_id=reviewer_id).first()
        if not reviewer:
            return jsonify({'error': 'Reviewer not found'}), 404
        return jsonify({
            'reviewer_id': reviewer.reviewer_id,
            'username': reviewer.username,
            'email': reviewer.email,
            'registration_date': reviewer.registration_date.isoformat(),
            'is_flagged': reviewer.is_flagged,
            'flagging_reason': reviewer.flagging_reason
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(debug=True)