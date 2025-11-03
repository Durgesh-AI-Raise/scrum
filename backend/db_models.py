from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timedelta
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/review_db")

Base = declarative_base()

class Review(Base):
    __tablename__ = 'reviews'
    review_id = Column(String, primary_key=True)
    product_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    review_text = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    submission_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    is_flagged = Column(Boolean, default=False, nullable=False)
    flag_reason = Column(String, nullable=True)
    flag_date = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Review(id='{self.review_id}', product='{self.product_id}', flagged={self.is_flagged})>"

class DBClient:
    def __init__(self, database_url=DATABASE_URL):
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        self._create_tables()

    def _create_tables(self):
        Base.metadata.create_all(self.engine)
        print("Database tables ensured.")

    def save_review(self, review_data):
        session = self.Session()
        try:
            # Convert submission_date string to datetime object if present
            if 'submission_date' in review_data and isinstance(review_data['submission_date'], str):
                review_data['submission_date'] = datetime.fromisoformat(review_data['submission_date'])
            # Convert flag_date string to datetime object if present
            if 'flag_date' in review_data and isinstance(review_data['flag_date'], str):
                review_data['flag_date'] = datetime.fromisoformat(review_data['flag_date'])

            existing_review = session.query(Review).filter_by(review_id=review_data['review_id']).first()
            if existing_review:
                for key, value in review_data.items():
                    setattr(existing_review, key, value)
                session.add(existing_review)
                print(f"Updated review {review_data['review_id']}")
            else:
                new_review = Review(**review_data)
                session.add(new_review)
                print(f"Saved new review {review_data['review_id']}")
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error saving review: {e}")
            return False
        finally:
            session.close()

    def get_flagged_reviews(self):
        session = self.Session()
        try:
            flagged = session.query(Review).filter_by(is_flagged=True).order_by(Review.flag_date.desc()).all()
            return [
                {
                    "review_id": r.review_id,
                    "product_id": r.product_id,
                    "user_id": r.user_id,
                    "review_text": r.review_text,
                    "rating": r.rating,
                    "flag_reason": r.flag_reason,
                    "flag_date": r.flag_date.isoformat() if r.flag_date else None,
                    "submission_date": r.submission_date.isoformat()
                }
                for r in flagged
            ]
        finally:
            session.close()

    def count_reviews_for_product_in_window(self, product_id, hours):
        session = self.Session()
        try:
            time_threshold = datetime.utcnow() - timedelta(hours=hours)
            count = session.query(Review).filter(
                Review.product_id == product_id,
                Review.submission_date >= time_threshold
            ).count()
            return count
        finally:
            session.close()

    def check_for_duplicate_review_text(self, review_text, current_review_id):
        session = self.Session()
        try:
            duplicate = session.query(Review).filter(
                Review.review_text == review_text,
                Review.review_id != current_review_id
            ).first()
            return duplicate is not None
        finally:
            session.close()
