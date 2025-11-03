from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from typing import List
from datetime import datetime

from src.storage.models import Base, ReviewDB
from src.ingestion.amazon_api_client import Review # Assuming Review dataclass is imported or defined similarly

class ReviewRepository:
    def __init__(self, database_url='sqlite:///./reviews.db'):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine) # Create tables if they don't exist
        self.Session = sessionmaker(bind=self.engine)

    def save_review(self, review: Review):
        session = self.Session()
        try:
            # Check if review already exists to prevent duplicates (idempotency)
            existing_review = session.query(ReviewDB).filter_by(reviewId=review.reviewId).first()
            if existing_review:
                # Optionally update existing review or log that it's a duplicate
                print(f"Review with ID {review.reviewId} already exists. Skipping save.")
                return

            db_review = ReviewDB(
                reviewId=review.reviewId,
                productId=review.productId,
                reviewerId=review.reviewerId,
                reviewerName=review.reviewerName,
                rating=review.rating,
                title=review.title,
                content=review.content,
                reviewDate=review.reviewDate,
                ingestionTimestamp=review.ingestionTimestamp,
                isVerifiedPurchase=review.isVerifiedPurchase,
                reviewerAccountCreationDate=review.reviewerAccountCreationDate
            )
            session.add(db_review)
            session.commit()
            print(f"Saved review: {review.reviewId}")
        except Exception as e:
            session.rollback()
            print(f"Error saving review {review.reviewId}: {e}")
            raise
        finally:
            session.close()

    def get_all_reviews(self) -> List[ReviewDB]:
        session = self.Session()
        try:
            return session.query(ReviewDB).all()
        finally:
            session.close()

    def get_reviews_since(self, since: datetime) -> List[ReviewDB]:
        session = self.Session()
        try:
            return session.query(ReviewDB).filter(ReviewDB.ingestionTimestamp >= since).all()
        finally:
            session.close()

    def get_review_by_id(self, review_id: str) -> ReviewDB:
        session = self.Session()
        try:
            return session.query(ReviewDB).filter_by(reviewId=review_id).first()
        finally:
            session.close()
