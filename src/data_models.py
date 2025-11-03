# src/data_models.py
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

class ReviewerMetadata:
    account_age_days: Optional[int]
    total_reviews: Optional[int]
    purchase_history_summary: Optional[str]
    is_prime_member: Optional[bool]

    def __init__(self, **kwargs):
        self.account_age_days = kwargs.get('account_age_days')
        self.total_reviews = kwargs.get('total_reviews')
        self.purchase_history_summary = kwargs.get('purchase_history_summary')
        self.is_prime_member = kwargs.get('is_prime_member')

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

class Review:
    review_id: str
    product_id: str
    reviewer_id: str
    review_text: str
    rating: int
    review_date: datetime # ISO 8601 format
    helpful_votes: Optional[int]
    total_votes: Optional[int]
    verified_purchase: Optional[bool]
    review_title: Optional[str]
    reviewer_metadata: Optional[ReviewerMetadata]
    ingestion_timestamp: datetime

    def __init__(self, **kwargs):
        self.review_id = kwargs['review_id']
        self.product_id = kwargs['product_id']
        self.reviewer_id = kwargs['reviewer_id']
        self.review_text = kwargs['review_text']
        self.rating = kwargs['rating']
        self.review_date = datetime.fromisoformat(kwargs['review_date'].replace('Z', '+00:00')) if isinstance(kwargs['review_date'], str) else kwargs['review_date']
        self.helpful_votes = kwargs.get('helpful_votes')
        self.total_votes = kwargs.get('total_votes')
        self.verified_purchase = kwargs.get('verified_purchase')
        self.review_title = kwargs.get('review_title')
        self.reviewer_metadata = ReviewerMetadata(**kwargs.get('reviewer_metadata', {})) if kwargs.get('reviewer_metadata') else None
        self.ingestion_timestamp = datetime.now()

    def to_dict(self):
        data = {
            'review_id': self.review_id,
            'product_id': self.product_id,
            'reviewer_id': self.reviewer_id,
            'review_text': self.review_text,
            'rating': self.rating,
            'review_date': self.review_date.isoformat().replace('+00:00', 'Z'),
            'ingestion_timestamp': self.ingestion_timestamp.isoformat().replace('+00:00', 'Z'),
        }
        if self.helpful_votes is not None: data['helpful_votes'] = self.helpful_votes
        if self.total_votes is not None: data['total_votes'] = self.total_votes
        if self.verified_purchase is not None: data['verified_purchase'] = self.verified_purchase
        if self.review_title is not None: data['review_title'] = self.review_title
        if self.reviewer_metadata:
            metadata_dict = self.reviewer_metadata.to_dict()
            if metadata_dict: # Only add if there's actual metadata
                data['reviewer_metadata'] = metadata_dict
        return data

class AssociatedPattern:
    pattern_id: str
    strength: int # 1-5, how strongly this pattern indicates this abuse

    def __init__(self, **kwargs):
        self.pattern_id = kwargs['pattern_id']
        self.strength = kwargs['strength']

    def to_dict(self):
        return self.__dict__

class AbuseCategory:
    category_id: str
    category_name: str
    description: str
    severity_score: int # 1-10
    keywords_to_flag: Optional[List[str]]
    associated_patterns: Optional[List[AssociatedPattern]]
    creation_date: datetime
    last_updated: datetime

    def __init__(self, **kwargs):
        self.category_id = kwargs['category_id']
        self.category_name = kwargs['category_name']
        self.description = kwargs['description']
        self.severity_score = kwargs['severity_score']
        self.keywords_to_flag = kwargs.get('keywords_to_flag')
        self.associated_patterns = [AssociatedPattern(**p) for p in kwargs['associated_patterns']] if kwargs.get('associated_patterns') else []
        self.creation_date = datetime.fromisoformat(kwargs['creation_date'].replace('Z', '+00:00')) if isinstance(kwargs.get('creation_date'), str) else kwargs.get('creation_date', datetime.now())
        self.last_updated = datetime.fromisoformat(kwargs['last_updated'].replace('Z', '+00:00')) if isinstance(kwargs.get('last_updated'), str) else kwargs.get('last_updated', datetime.now())

    def to_dict(self):
        data = self.__dict__.copy()
        data['creation_date'] = self.creation_date.isoformat().replace('+00:00', 'Z')
        data['last_updated'] = self.last_updated.isoformat().replace('+00:00', 'Z')
        if self.associated_patterns:
            data['associated_patterns'] = [p.to_dict() for p in self.associated_patterns]
        return {k: v for k, v in data.items() if v is not None and (not isinstance(v, list) or v)} # Remove empty lists/Nones


class VelocityThreshold:
    threshold_id: str
    entity_type: str # 'PRODUCT' or 'REVIEWER'
    window_size_hours: int
    max_reviews_in_window: int
    alert_level: str # 'WARNING', 'CRITICAL'
    description: str

    def __init__(self, **kwargs):
        self.threshold_id = kwargs['threshold_id']
        self.entity_type = kwargs['entity_type']
        self.window_size_hours = kwargs['window_size_hours']
        self.max_reviews_in_window = kwargs['max_reviews_in_window']
        self.alert_level = kwargs['alert_level']
        self.description = kwargs['description']

    def to_dict(self):
        return self.__dict__

class Alert:
    alert_id: str
    entity_type: str
    entity_id: str
    alert_type: str # e.g., 'HIGH_REVIEW_VELOCITY'
    triggered_threshold_id: str # FK to VelocityThreshold
    current_velocity_value: int
    context_reviews: List[str] # List of review_ids that contributed to velocity
    alert_timestamp: datetime
    status: str # 'NEW', 'INVESTIGATING', 'CLOSED'
    assigned_analyst_id: Optional[str]
    notes: Optional[str]

    def __init__(self, **kwargs):
        self.alert_id = kwargs.get('alert_id', str(uuid.uuid4()))
        self.entity_type = kwargs['entity_type']
        self.entity_id = kwargs['entity_id']
        self.alert_type = kwargs['alert_type']
        self.triggered_threshold_id = kwargs['triggered_threshold_id']
        self.current_velocity_value = kwargs['current_velocity_value']
        self.context_reviews = kwargs.get('context_reviews', [])
        self.alert_timestamp = datetime.fromisoformat(kwargs['alert_timestamp'].replace('Z', '+00:00')) if isinstance(kwargs.get('alert_timestamp'), str) else kwargs.get('alert_timestamp', datetime.now())
        self.status = kwargs.get('status', 'NEW')
        self.assigned_analyst_id = kwargs.get('assigned_analyst_id')
        self.notes = kwargs.get('notes')

    def to_dict(self):
        data = self.__dict__.copy()
        data['alert_timestamp'] = self.alert_timestamp.isoformat().replace('+00:00', 'Z')
        return {k: v for k, v in data.items() if v is not None and (not isinstance(v, list) or v)} # Remove empty lists/Nones
