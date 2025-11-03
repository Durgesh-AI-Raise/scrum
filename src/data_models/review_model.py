from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class AbuseFlag:
    ruleId: str
    flaggedAt: datetime
    reason: str
    status: str = "PENDING" # e.g., PENDING, APPROVED, REJECTED

@dataclass
class DetectionResults:
    suspiciousKeywords: bool = False
    identicalReview: bool = False
    triggeredRules: List[str] = field(default_factory=list)
    overallAbuseScore: Optional[float] = None # Placeholder

@dataclass
class ReviewMetadata:
    ingestedAt: datetime

@dataclass
class Review:
    reviewId: str
    productId: str
    reviewerId: str
    reviewText: str
    rating: int # 1-5
    timestamp: datetime
    reviewTitle: Optional[str] = None
    source: str = "Amazon"
    helpfulVotes: Optional[int] = None
    totalVotes: Optional[int] = None
    isVerifiedPurchase: Optional[bool] = None
    abuseFlags: List[AbuseFlag] = field(default_factory=list)
    detectionResults: DetectionResults = field(default_factory=DetectionResults)
    metadata: ReviewMetadata = field(default_factory=lambda: ReviewMetadata(ingestedAt=datetime.utcnow()))

    def to_dict(self) -> Dict[str, Any]:
        # Simple serialization for demonstration
        data = {
            "reviewId": self.reviewId,
            "productId": self.productId,
            "reviewerId": self.reviewerId,
            "reviewText": self.reviewText,
            "rating": self.rating,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "abuseFlags": [flag.__dict__ for flag in self.abuseFlags],
            "detectionResults": {
                "suspiciousKeywords": self.detectionResults.suspiciousKeywords,
                "identicalReview": self.detectionResults.identicalReview,
                "triggeredRules": self.detectionResults.triggeredRules,
                "overallAbuseScore": self.detectionResults.overallAbuseScore
            },
            "metadata": {
                "ingestedAt": self.metadata.ingestedAt.isoformat()
            }
        }
        if self.reviewTitle:
            data["reviewTitle"] = self.reviewTitle
        if self.helpfulVotes is not None:
            data["helpfulVotes"] = self.helpfulVotes
        if self.totalVotes is not None:
            data["totalVotes"] = self.totalVotes
        if self.isVerifiedPurchase is not None:
            data["isVerifiedPurchase"] = self.isVerifiedPurchase
        return data

# Example Usage:
# review = Review(
#     reviewId="R12345",
#     productId="P67890",
#     reviewerId="U11223",
#     reviewText="This product is amazing!",
#     rating=5,
#     timestamp=datetime.fromisoformat("2023-10-27T10:00:00Z"),
#     reviewTitle="Great product"
# )
# print(review.to_dict())
