from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class ReviewModel(BaseModel):
    review_id: str = Field(alias='id') # Maps to 'id' in incoming data
    product_id: str = Field(alias='productId') # Maps to 'productId'
    user_id: str = Field(alias='userId') # Maps to 'userId'
    timestamp: datetime
    rating: int
    title: Optional[str] = None
    text: str = Field(alias='reviewText') # Maps to 'reviewText'
    raw_data: dict # Store original ingested data for fidelity
    flags: List[str] = [] # e.g., ["similar_phrasing", "keyword_stuffing"]
    is_flagged: bool = False
    analyst_status: str = "pending" # pending, legitimate, abusive
    analyst_id: Optional[str] = None
    analyst_decision_timestamp: Optional[datetime] = None

    @classmethod
    def from_raw_data(cls, raw_json: dict):
        # Ensure timestamp is parsed correctly, handles ISO format
        if isinstance(raw_json.get('timestamp'), str):
            raw_json['timestamp'] = datetime.fromisoformat(raw_json['timestamp'].replace('Z', '+00:00'))

        return cls(
            id=raw_json.get('id'),
            productId=raw_json.get('productId'),
            userId=raw_json.get('userId'),
            timestamp=raw_json.get('timestamp'),
            rating=raw_json.get('rating'),
            title=raw_json.get('title'),
            reviewText=raw_json.get('reviewText'),
            raw_data=raw_json # Store the entire original JSON
        )