# backend/reviewer_activity_service.py
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Reviewer, ReviewActivity, FlaggedItem, Product

class ReviewerActivityDetector:
    def __init__(self, db_session_factory, high_volume_threshold=100, high_volume_period_days=30,
                 disparate_categories_threshold=5, disparate_categories_period_days=30):
        self.db_session_factory = db_session_factory
        self.high_volume_threshold = high_volume_threshold
        self.high_volume_period_days = high_volume_period_days
        self.disparate_categories_threshold = disparate_categories_threshold
        self.disparate_categories_period_days = disparate_categories_period_days

    def check_high_volume_and_disparate_reviews(self, reviewer_id: int) -> bool:
        session: Session = self.db_session_factory()
        try:
            flagging_reasons = []

            # Check for high volume
            time_window_start_volume = datetime.utcnow() - timedelta(days=self.high_volume_period_days)
            review_count = session.query(func.count(ReviewActivity.review_id))\
                                .filter(ReviewActivity.reviewer_id == reviewer_id)\
                                .filter(ReviewActivity.review_date >= time_window_start_volume)\
                                .scalar()

            if review_count >= self.high_volume_threshold:
                flagging_reasons.append(f"High volume reviews ({review_count} in {self.high_volume_period_days} days)")

            # Check for disparate categories
            time_window_start_categories = datetime.utcnow() - timedelta(days=self.disparate_categories_period_days)
            unique_categories_count = session.query(func.count(func.distinct(ReviewActivity.product_category)))\
                                            .filter(ReviewActivity.reviewer_id == reviewer_id)\
                                            .filter(ReviewActivity.review_date >= time_window_start_categories)\
                                            .scalar()

            if unique_categories_count >= self.disparate_categories_threshold:
                flagging_reasons.append(f"Reviews across disparate categories ({unique_categories_count} unique categories in {self.disparate_categories_period_days} days)")

            if flagging_reasons:
                self._flag_reviewer_in_db(session, reviewer_id, "review_farming", ", ".join(flagging_reasons))
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def _flag_reviewer_in_db(self, session: Session, reviewer_id: int, reason: str, details: str):
        existing_flag = session.query(FlaggedItem).filter_by(
            item_type='reviewer',
            item_id=reviewer_id,
            reason=reason
        ).first()

        if not existing_flag:
            flagged_item = FlaggedItem(
                item_type='reviewer',
                item_id=reviewer_id,
                reason=reason,
                details=details,
                timestamp=datetime.utcnow()
            )
            session.add(flagged_item)
            reviewer = session.query(Reviewer).filter_by(reviewer_id=reviewer_id).first()
            if reviewer:
                reviewer.is_flagged = True
                reviewer.flagging_reason = reason
            session.commit()

if __name__ == '__main__':
    # This block is for demonstration/testing purposes and assumes a running database
    # In a real application, this service would be instantiated and its methods called
    # by other services (e.g., review_ingestion_service) or a scheduled task runner.
    DATABASE_URL = "postgresql://user:password@host:port/database" # Replace with your actual DB URL
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine) # Ensure tables are created
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Example usage:
    detector = ReviewerActivityDetector(SessionLocal)
    # Simulate a reviewer with ID 1
    # You would typically call this after a new review is ingested
    # try:
    #     if detector.check_high_volume_and_disparate_reviews(1):
    #         print("Reviewer 1 flagged for review farming!")
    #     else:
    #         print("Reviewer 1 is within normal activity limits.")
    # except Exception as e:
    #     print(f"Error checking reviewer activity: {e}")