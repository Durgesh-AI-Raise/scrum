from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ReviewData:
    review_id: str
    product_id: str
    reviewer_id: str
    review_text: str
    star_rating: int
    review_timestamp: str  # ISO 8601 format
    # Optional fields for future extensibility or handling missing data
    sentiment_score: Optional[float] = None
    detected_patterns: list[str] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict) # To store original raw data for debugging/auditing
