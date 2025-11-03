# backend/app/models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime

db = SQLAlchemy()

class Review(db.Model):
    __tablename__ = 'reviews'
    review_id = db.Column(db.String(255), primary_key=True)
    product_id = db.Column(db.String(255), nullable=False)
    reviewer_id = db.Column(db.String(255), nullable=False)
    review_text = db.Column(db.Text)
    review_rating = db.Column(db.Integer)
    review_date = db.Column(db.TIMESTAMP(timezone=True), nullable=False)
    reviewer_ip = db.Column(db.String(45))
    is_flagged = db.Column(db.Boolean, default=False)
    flag_reasons = db.Column(ARRAY(db.Text), default=[])
    manual_status = db.Column(db.String(50), default='pending') # 'pending', 'abusive', 'legitimate'
    flagged_at = db.Column(db.TIMESTAMP(timezone=True))
    ingested_at = db.Column(db.TIMESTAMP(timezone=True), default=datetime.utcnow)

    def __repr__(self):
        return f"<Review {self.review_id}>"

class SuspiciousEntity(db.Model):
    __tablename__ = 'suspicious_entities'
    entity_id = db.Column(db.String(255), primary_key=True)
    entity_type = db.Column(db.String(10), nullable=False) # 'ip' or 'user'
    reason = db.Column(db.Text)
    added_at = db.Column(db.TIMESTAMP(timezone=True), default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<SuspiciousEntity {self.entity_type}:{self.entity_id}>"

class IngestionMetadata(db.Model):
    __tablename__ = 'ingestion_metadata'
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), unique=True, nullable=False)
    last_successful_run = db.Column(db.TIMESTAMP(timezone=True))

    def __repr__(self):
        return f"<IngestionMetadata {self.service_name}>"
