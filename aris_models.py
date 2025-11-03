import uuid
import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Base class for SQLAlchemy declarative models
Base = declarative_base()

class DetectionRule(Base):
    """
    SQLAlchemy model for managing detection rules (keywords, velocity thresholds).
    Stored in PostgreSQL.
    """
    __tablename__ = 'detection_rules'

    rule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name = Column(String(255), unique=True, nullable=False)
    rule_type = Column(String(50), nullable=False)  # e.g., 'KEYWORD', 'VELOCITY_THRESHOLD'
    status = Column(String(20), default='ACTIVE')   # 'ACTIVE', 'INACTIVE', 'DRAFT'
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now, onupdate=datetime.datetime.now)
    config = Column(JSONB)  # Stores rule-specific configurations

    def __repr__(self):
        return f"<DetectionRule(name='{self.rule_name}', type='{self.rule_type}', status='{self.status}')>"

class FlaggedReview(Base):
    """
    SQLAlchemy model for storing summary information about flagged reviews.
    Stored in PostgreSQL, linking to the full review in MongoDB.
    """
    __tablename__ = 'flagged_reviews'

    flag_record_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(String(255), nullable=False, index=True) # Links to MongoDB review._id
    product_id = Column(String(255), nullable=False, index=True)
    reviewer_id = Column(String(255), nullable=False, index=True)
    flag_type = Column(String(50), nullable=False, index=True) # e.g., 'KEYWORD_MATCH', 'VELOCITY_ANOMALY'
    detection_rule_id = Column(UUID(as_uuid=True)) # Links to DetectionRule.rule_id
    detection_details = Column(JSONB) # Specifics about why it was flagged (e.g., matched keyword)
    flagged_at = Column(DateTime(timezone=True), default=datetime.datetime.now, index=True)
    analyst_status = Column(String(50), default='PENDING', index=True) # 'PENDING', 'LEGITIMATE', 'ABUSIVE'
    abuse_type = Column(String(50)) # 'FAKE', 'SPAM', 'INCENTIVIZED', etc.
    analyst_notes = Column(Text)
    last_updated_by_analyst = Column(DateTime(timezone=True))

    def __repr__(self):
        return (f"<FlaggedReview(review_id='{self.review_id}', flag_type='{self.flag_type}', "
                f"analyst_status='{self.analyst_status}')>")

# --- Database Setup (Example Usage) ---
# This part is for initial setup and creating tables. In a real application,
# this would be handled by migrations.

DATABASE_URL = "postgresql://user:password@localhost/aris_db" # Replace with your actual DB URL
Engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

def create_db_tables():
    """Creates all tables defined in Base metadata."""
    print("Attempting to create database tables...")
    Base.metadata.create_all(bind=Engine)
    print("Database tables created (or already exist).")

if __name__ == '__main__':
    # This block will run only when aris_models.py is executed directly.
    # It's useful for initial setup or schema updates.
    create_db_tables()

    # Example of adding a rule (for testing setup)
    # session = SessionLocal()
    # try:
    #     new_rule = DetectionRule(
    #         rule_name="Test Keyword Rule",
    #         rule_type="KEYWORD",
    #         config={"keywords": ["bad word", "spammy phrase"], "case_sensitive": False, "match_type": "contains"}
    #     )
    #     session.add(new_rule)
    #     session.commit()
    #     print(f"Added example rule: {new_rule.rule_name}")
    # except Exception as e:
    #     session.rollback()
    #     print(f"Error adding example rule: {e}")
    # finally:
    #     session.close()
