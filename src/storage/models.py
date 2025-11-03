from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class ReviewDB(Base):
    __tablename__ = 'reviews'

    reviewId = Column(String, primary_key=True)
    productId = Column(String, nullable=False)
    reviewerId = Column(String, nullable=False)
    reviewerName = Column(String)
    rating = Column(Integer, nullable=False)
    title = Column(String)
    content = Column(String)
    reviewDate = Column(DateTime, nullable=False)
    ingestionTimestamp = Column(DateTime, default=datetime.utcnow)
    isVerifiedPurchase = Column(Boolean, default=False)
    reviewerAccountCreationDate = Column(DateTime)

    def __repr__(self):
        return f"<Review(reviewId='{self.reviewId}', productId='{self.productId}', rating={self.rating})>"
