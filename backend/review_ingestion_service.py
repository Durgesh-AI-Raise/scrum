# backend/review_ingestion_service.py
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models import Base, Review, Product, ReviewActivity
# from .similarity_detection_service import ReviewSimilarityDetector # Will integrate later

app = Flask(__name__)

# Database setup (replace with your actual connection string)
DATABASE_URL = "postgresql://user:password@host:port/database"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

@app.route('/api/reviews/ingest', methods=['POST'])
def ingest_review():
    session = Session()
    try:
        data = request.json
        if not all(key in data for key in ['reviewer_id', 'product_id', 'review_text']):
            return jsonify({'error': 'Missing required review fields'}), 400

        new_review = Review(
            reviewer_id=data['reviewer_id'],
            product_id=data['product_id'],
            review_text=data['review_text'],
            rating=data.get('rating'),
            review_date=datetime.utcnow()
        )
        session.add(new_review)
        session.flush() # To get new_review.review_id before commit

        # Update ReviewActivity (Task 3.2 integration)
        product = session.query(Product).filter_by(product_id=new_review.product_id).first()
        product_category = product.category if product else 'unknown'

        new_activity = ReviewActivity(
            reviewer_id=new_review.reviewer_id,
            review_id=new_review.review_id,
            review_date=new_review.review_date,
            product_category=product_category
        )
        session.add(new_activity)

        session.commit()

        # Trigger similarity detection (synchronously for now, can be async later)
        # For full implementation, this would involve a call to similarity_detection_service
        # Example:
        # detector = ReviewSimilarityDetector()
        # all_reviews = session.query(Review).all()
        # reviews_for_corpus = [{'review_id': r.review_id, 'review_text': r.review_text} for r in all_reviews]
        # detector.build_corpus(reviews_for_corpus)
        # similarities = detector.detect_similar_reviews(new_review.review_id, new_review.review_text)
        # for s in similarities:
        #    flag_similar_reviews(new_review.review_id, s['original_review_id'], 'similar_content', f"Similarity score: {s['similarity_score']}")


        return jsonify({'message': 'Review ingested successfully', 'review_id': new_review.review_id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(debug=True, port=5001) # Run on a different port than dashboard API
