from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional

@dataclass
class FlaggedReview:
    review_id: str
    product_id: str
    user_id: str
    rating: int
    review_content: str
    review_timestamp: datetime
    flagging_timestamp: datetime
    severity: str
    reasons: List[Dict] # Each dict represents a triggered rule with 'rule_id', 'description', 'flag_reason'
    status: str = "FLAGGED" # Default status for a newly flagged review