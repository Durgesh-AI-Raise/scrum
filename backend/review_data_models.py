# review_data_models.py

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from enum import Enum

# Represents a review from the core review system (simplified for ingestion)
class Review(BaseModel):
    review_id: str
    reviewer_id: str
    product_asin: str
    rating: int
    text: str
    timestamp: datetime

# Represents a flagged review specific to our system
class FlaggedReviewModel(BaseModel):
    flagged_id: str
    review_id: str
    flagged_by_heuristic: bool
    heuristic_rules_triggered: List[str]
    flagging_timestamp: datetime
    status: str # e.g., "pending_investigation", "abusive", "legitimate"
    investigation_notes: Optional[str] = None
    product_asin: str # Denormalized for convenience
    reviewer_id: str # Denormalized for convenience

# Enum for allowed review statuses
class ReviewStatus(str, Enum):
    PENDING = "pending_investigation"
    ABUSIVE = "abusive"
    LEGITIMATE = "legitimate"

# Request model for updating review status
class UpdateStatusRequest(BaseModel):
    new_status: ReviewStatus
    notes: Optional[str] = None
