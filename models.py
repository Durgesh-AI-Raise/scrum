# models.py
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Review(Base):
    __tablename__ = 'reviews'
    review_id = Column(Integer, primary_key=True)
    reviewer_id = Column(Integer)
    product_id = Column(Integer)
    review_text = Column(Text)
    rating = Column(Integer)
    review_date = Column(DateTime, default=datetime.utcnow)
    is_flagged = Column(Boolean, default=False)
    flagging_reason = Column(String)

class Reviewer(Base):
    __tablename__ = 'reviewers'
    reviewer_id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)
    registration_date = Column(DateTime, default=datetime.utcnow)
    is_flagged = Column(Boolean, default=False)
    flagging_reason = Column(String)

class Product(Base): # Added for product category lookup in ReviewActivity
    __tablename__ = 'products'
    product_id = Column(Integer, primary_key=True)
    product_name = Column(String)
    category = Column(String)

class FlaggedItem(Base):
    __tablename__ = 'flagged_items'
    flag_id = Column(Integer, primary_key=True)
    item_type = Column(String) # 'review' or 'reviewer'
    item_id = Column(Integer)
    reason = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='pending') # pending, investigating, resolved
    details = Column(Text) # JSON string of additional details

class ReviewActivity(Base):
    __tablename__ = 'review_activity'
    activity_id = Column(Integer, primary_key=True)
    reviewer_id = Column(Integer)
    review_id = Column(Integer)
    review_date = Column(DateTime)
    product_category = Column(String) # To track disparate categories

class PurchaseHistory(Base):
    __tablename__ = 'purchase_history'
    purchase_id = Column(Integer, primary_key=True)
    reviewer_id = Column(Integer)
    product_id = Column(Integer)
    purchase_date = Column(DateTime)
    quantity = Column(Integer)
    price = Column(Float)
