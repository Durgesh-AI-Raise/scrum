
# backend/services/review_flagging_service.py

from ..models import Review, FlaggingReason, PurchaseHistory
from ..config import SPAM_ACCOUNT_FLAGGING_CONFIG, SUSPICIOUS_KEYWORDS
from typing import Optional, List, Dict, Set
from datetime import datetime, timedelta

# Mock Database for Purchase History (This would be a real DB in production)
mock_purchase_history_db: List[PurchaseHistory] = [
    PurchaseHistory(user_id='user1', product_id='prod1', purchase_date='2023-01-15T00:00:00Z'),
    PurchaseHistory(user_id='user4', product_id='prodX', purchase_date='2023-05-20T00:00:00Z'),
    # Add more mock data as needed for testing various scenarios
]

# This is a placeholder for accessing all reviews. In a real application,
# this would be a database query. For mock purposes, we assume a global
# dictionary of reviews can be passed or accessed (e.g., from main.py's mock_db_reviews_dict).
# For now, we'll assume the _get_reviews_by_reviewer method can access relevant data.

class ReviewFlaggingService:
    def __init__(self, all_reviews_accessor: Optional[Dict[str, Review]] = None):
        """
        Initializes the flagging service.
        all_reviews_accessor: A dictionary (or similar) to simulate database access for all reviews.
                              Used for spam account detection.
        """
        self._all_reviews_accessor = all_reviews_accessor

    async def _get_reviews_by_reviewer(self, reviewer_id: str, start_time: datetime, end_time: datetime) -> List[Review]:
        """
        Mocks fetching reviews by a reviewer within a time window from the 'database'.
        In a real app, this would be a DB query.
        """
        if not self._all_reviews_accessor:
            return []

        filtered_reviews = []
        for review_id, review in self._all_reviews_accessor.items():
            if review.reviewer_id == reviewer_id:
                review_time = datetime.fromisoformat(review.timestamp)
                if start_time <= review_time < end_time:
                    filtered_reviews.append(review)
        return filtered_reviews


    async def check_no_purchase_history(self, review: Review) -> Optional[FlaggingReason]:
        """Checks if the reviewer has a purchase history for the reviewed product."""
        has_purchased = False
        for purchase in mock_purchase_history_db:
            if purchase.user_id == review.reviewer_id and purchase.product_id == review.product_id:
                has_purchased = True
                break

        if not has_purchased:
            return FlaggingReason(
                type='NO_PURCHASE_HISTORY',
                description='Reviewer has no purchase history for the reviewed product.'
            )
        return None

    async def flag_spam_account(self, new_review: Review) -> Optional[FlaggingReason]:
        """Analyzes reviewer's recent activity to detect spam account patterns."""
        config = SPAM_ACCOUNT_FLAGGING_CONFIG
        
        # Define the time window for historical reviews
        end_time = datetime.fromisoformat(new_review.timestamp)
        start_time = end_time - timedelta(hours=config["time_period_hours"])

        # Fetch recent reviews by the reviewer (excluding the new_review itself, handled in analysis)
        recent_reviews_by_reviewer = await self._get_reviews_by_reviewer(new_review.reviewer_id, start_time, end_time)

        # Include the current new_review in the calculation for thresholds
        # Ensure we don't double-count if new_review is already in _all_reviews_accessor (e.g., for testing)
        if not any(r.id == new_review.id for r in recent_reviews_by_reviewer):
            recent_reviews_by_reviewer.append(new_review)

        total_reviews = len(recent_reviews_by_reviewer)
        distinct_products: Set[str] = {r.product_id for r in recent_reviews_by_reviewer}
        distinct_sellers: Set[str] = {r.seller_id for r in recent_reviews_by_reviewer if r.seller_id}

        # Check against configured thresholds
        if (total_reviews >= config["min_reviews_count"] and
            len(distinct_products) >= config["min_distinct_products"] and
            len(distinct_sellers) >= config["min_distinct_sellers"]):
            
            return FlaggingReason(
                type='SPAM_ACCOUNT',
                description=(f'Reviewer posted {total_reviews} reviews across '
                             f'{len(distinct_products)} products and '
                             f'{len(distinct_sellers)} sellers within '
                             f'{config["time_period_hours"]} hours.')
            )
        return None

    async def flag_suspicious_keywords(self, review: Review) -> Optional[FlaggingReason]:
        """Scans review text for suspicious keywords indicating incentivized abuse."""
        review_text_lower = review.review_text.lower()
        found_keywords = []

        for keyword in SUSPICIOUS_KEYWORDS:
            if keyword.lower() in review_text_lower:
                found_keywords.append(keyword)

        if found_keywords:
            return FlaggingReason(
                type='SUSPICIOUS_KEYWORDS',
                description=f'Review contains suspicious keyword(s): {", ".join(found_keywords)}.'
            )
        return None
