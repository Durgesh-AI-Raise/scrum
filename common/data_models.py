from datetime import datetime
from typing import List, Optional, Dict

class Review:
    """
    Represents an Amazon product review.
    """
    review_id: str
    product_id: str
    reviewer_id: str
    review_text: str
    star_rating: int
    review_date: datetime
    helpfulness_votes: int
    purchase_verified: bool
    ingestion_timestamp: datetime
    status: str
    last_updated: datetime

    product_category: Optional[str] = None
    reviewer_account_age_days: Optional[int] = None

    def __init__(self, review_id: str, product_id: str, reviewer_id: str, review_text: str,
                 star_rating: int, review_date: datetime, helpfulness_votes: int,
                 purchase_verified: bool, ingestion_timestamp: datetime = None,
                 status: str = "ingested", last_updated: datetime = None,
                 product_category: Optional[str] = None, reviewer_account_age_days: Optional[int] = None):
        self.review_id = review_id
        self.product_id = product_id
        self.reviewer_id = reviewer_id
        self.review_text = review_text
        self.star_rating = star_rating
        self.review_date = review_date
        self.helpfulness_votes = helpfulness_votes
        self.purchase_verified = purchase_verified
        self.ingestion_timestamp = ingestion_timestamp if ingestion_timestamp else datetime.utcnow()
        self.status = status
        self.last_updated = last_updated if last_updated else datetime.utcnow()
        self.product_category = product_category
        self.reviewer_account_age_days = reviewer_account_age_days

    def to_dict(self):
        return {
            "review_id": self.review_id,
            "product_id": self.product_id,
            "reviewer_id": self.reviewer_id,
            "review_text": self.review_text,
            "star_rating": self.star_rating,
            "review_date": self.review_date.isoformat(),
            "helpfulness_votes": self.helpfulness_votes,
            "purchase_verified": self.purchase_verified,
            "ingestion_timestamp": self.ingestion_timestamp.isoformat(),
            "status": self.status,
            "last_updated": self.last_updated.isoformat(),
            "product_category": self.product_category,
            "reviewer_account_age_days": self.reviewer_account_age_days
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            review_id=data["review_id"],
            product_id=data["product_id"],
            reviewer_id=data["reviewer_id"],
            review_text=data["review_text"],
            star_rating=data["star_rating"],
            review_date=datetime.fromisoformat(data["review_date"]),
            helpfulness_votes=data["helpfulness_votes"],
            purchase_verified=data["purchase_verified"],
            ingestion_timestamp=datetime.fromisoformat(data["ingestion_timestamp"]),
            status=data.get("status", "ingested"),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            product_category=data.get("product_category"),
            reviewer_account_age_days=data.get("reviewer_account_age_days")
        )

class FlaggedReview:
    """
    Represents a review that has been flagged for potential abuse.
    """
    flag_id: str
    review_id: str
    flagging_timestamp: datetime
    reason: List[str]
    severity_score: int
    moderation_status: str
    moderator_notes: Optional[str] = None
    moderated_by: Optional[str] = None
    moderated_timestamp: Optional[datetime] = None

    def __init__(self, flag_id: str, review_id: str, flagging_timestamp: datetime,
                 reason: List[str], severity_score: int, moderation_status: str = "pending",
                 moderator_notes: Optional[str] = None, moderated_by: Optional[str] = None,
                 moderated_timestamp: Optional[datetime] = None):
        self.flag_id = flag_id
        self.review_id = review_id
        self.flagging_timestamp = flagging_timestamp
        self.reason = reason
        self.severity_score = severity_score
        self.moderation_status = moderation_status
        self.moderator_notes = moderator_notes
        self.moderated_by = moderated_by
        self.moderated_timestamp = moderated_timestamp

    def to_dict(self):
        return {
            "flag_id": self.flag_id,
            "review_id": self.review_id,
            "flagging_timestamp": self.flagging_timestamp.isoformat(),
            "reason": self.reason,
            "severity_score": self.severity_score,
            "moderation_status": self.moderation_status,
            "moderator_notes": self.moderator_notes,
            "moderated_by": self.moderated_by,
            "moderated_timestamp": self.moderated_timestamp.isoformat() if self.moderated_timestamp else None
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            flag_id=data["flag_id"],
            review_id=data["review_id"],
            flagging_timestamp=datetime.fromisoformat(data["flagging_timestamp"]),
            reason=data["reason"],
            severity_score=data["severity_score"],
            moderation_status=data.get("moderation_status", "pending"),
            moderator_notes=data.get("moderator_notes"),
            moderated_by=data.get("moderated_by"),
            moderated_timestamp=datetime.fromisoformat(data["moderated_timestamp"]) if data.get("moderated_timestamp") else None
        )