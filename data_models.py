
from datetime import datetime
from typing import List, Optional

class Review:
    def __init__(self,
                 review_id: str,
                 product_id: str,
                 reviewer_id: str,
                 review_title: str,
                 review_content: str,
                 overall_rating: float,
                 review_date: datetime,
                 verified_purchase: bool,
                 helpful_vote_count: int,
                 sentiment_score: Optional[float] = None,
                 review_url: Optional[str] = None):
        self.review_id = review_id
        self.product_id = product_id
        self.reviewer_id = reviewer_id
        self.review_title = review_title
        self.review_content = review_content
        self.overall_rating = overall_rating
        self.review_date = review_date
        self.verified_purchase = verified_purchase
        self.helpful_vote_count = helpful_vote_count
        self.sentiment_score = sentiment_score
        self.review_url = review_url

class ReviewerProfile:
    def __init__(self,
                 reviewer_id: str,
                 reviewer_name: str,
                 account_creation_date: datetime,
                 total_reviews_submitted: int,
                 average_rating_given: Optional[float] = None,
                 is_prime_member: Optional[bool] = False,
                 reviewer_url: Optional[str] = None):
        self.reviewer_id = reviewer_id
        self.reviewer_name = reviewer_name
        self.account_creation_date = account_creation_date
        self.total_reviews_submitted = total_reviews_submitted
        self.average_rating_given = average_rating_given
        self.is_prime_member = is_prime_member
        self.reviewer_url = reviewer_url

class Product:
    def __init__(self,
                 product_id: str,
                 product_name: str,
                 product_category: str,
                 brand: str,
                 average_rating: float,
                 total_reviews: int,
                 price: float,
                 product_url: Optional[str] = None):
        self.product_id = product_id
        self.product_name = product_name
        self.product_category = product_category
        self.brand = brand
        self.average_rating = average_rating
        self.total_reviews = total_reviews
        self.price = price
        self.product_url = product_url

class FlaggedReview:
    def __init__(self,
                 flagged_review_id: str,
                 review_id: str,
                 product_id: str,
                 reviewer_id: str,
                 flagged_date: datetime,
                 flagging_reasons: List[str],
                 status: str = "PENDING_TRIAGE", # PENDING_TRIAGE, UNDER_INVESTIGATION, ABUSIVE, FALSE_POSITIVE, REMOVED
                 triage_notes: Optional[str] = None,
                 triage_analyst_id: Optional[str] = None):
        self.flagged_review_id = flagged_review_id
        self.review_id = review_id
        self.product_id = product_id
        self.reviewer_id = reviewer_id
        self.flagged_date = flagged_date
        self.flagging_reasons = flagging_reasons
        self.status = status
        self.triage_notes = triage_notes
        self.triage_analyst_id = triage_analyst_id
