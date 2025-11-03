
# backend/models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# --- Core Data Models (Representing database entities) ---

class FlaggingReason(BaseModel):
    """Represents a reason why a review was flagged."""
    type: str = Field(..., description="Type of flag (e.g., 'NO_PURCHASE_HISTORY', 'SPAM_ACCOUNT', 'SUSPICIOUS_KEYWORDS')")
    description: str = Field(..., description="Detailed description of the flagging reason")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="ISO formatted timestamp when the flag was created")

class Review(BaseModel):
    """Represents a review in the system."""
    id: str = Field(..., description="Unique ID of the review")
    product_id: str = Field(..., description="ID of the product being reviewed")
    reviewer_id: str = Field(..., description="ID of the user who posted the review")
    review_text: str = Field(..., description="The actual text content of the review")
    images: List[str] = Field(default_factory=list, description="List of URLs to review images")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="ISO formatted timestamp when the review was posted")
    seller_id: Optional[str] = Field(None, description="ID of the seller for the product (if applicable)")
    # 'pending': Review is flagged and awaiting analyst review
    # 'legitimate': Analyst has manually marked as legitimate
    # 'abusive': Analyst has manually marked as abusive
    status: Literal["pending", "legitimate", "abusive"] = Field("pending", description="Current status of the review")
    flagging_reasons: List[FlaggingReason] = Field(default_factory=list, description="List of reasons why this review was flagged")

    def add_flagging_reason(self, reason_type: str, description: str):
        """Adds a new flagging reason to the review, ensuring unique types or updating descriptions."""
        existing_types = {r.type for r in self.flagging_reasons}
        if reason_type not in existing_types:
            self.flagging_reasons.append(FlaggingReason(type=reason_type, description=description))
            # If a review gets flagged, its status should ideally be 'pending' for review
            if self.status not in ["abusive", "legitimate"]:
                self.status = "pending"
        else:
            # Optionally update description if reason already exists
            for r in self.flagging_reasons:
                if r.type == reason_type:
                    r.description = description
                    r.timestamp = datetime.now().isoformat()
                    break

class User(BaseModel):
    """Represents a user (reviewer) in the system."""
    id: str
    name: str
    email: Optional[str] = None
    total_reviews: int = 0
    # Add more user history fields as needed

class Product(BaseModel):
    """Represents a product in the system."""
    id: str
    name: str
    image_url: Optional[str] = None
    category: Optional[str] = None
    product_link: Optional[str] = None

class Seller(BaseModel):
    """Represents a seller in the system."""
    id: str
    name: str

class PurchaseHistory(BaseModel):
    """Records a user's purchase of a product."""
    user_id: str
    product_id: str
    purchase_date: str # ISO format

# --- API Response Models (for specific endpoints) ---

class ReviewSummary(BaseModel):
    """Summary of a review for dashboard display."""
    id: str
    product_name: str
    reviewer_name: str
    timestamp: str
    primary_flag_reason_type: Optional[str] = None # Quick display of the main reason
    status: str

class DetailedReviewResponse(BaseModel):
    """Full details of a review for the detailed view."""
    id: str
    review_text: str
    images: List[str]
    timestamp: str
    status: str
    flagging_reasons: List[FlaggingReason]
    product: Product
    reviewer: User
    seller: Optional[Seller] = None

class ReviewStatusUpdate(BaseModel):
    """Model for updating a review's status."""
    status: Literal["legitimate", "abusive"]
