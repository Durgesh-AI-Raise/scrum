
# aris/data_models/flagged_review.py
from datetime import datetime
from typing import List, Dict, Any
import uuid
from .review_data import ReviewData

class FlaggedReview:
    def __init__(self, original_review: ReviewData, flags: List[Dict[str, Any]], timestamp: datetime = None, status: str = "PENDING_REVIEW"):
        self.id = str(uuid.uuid4())
        self.original_review = original_review
        self.flags = flags
        self.timestamp = timestamp if timestamp else datetime.now()
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "original_review": self.original_review.to_dict(),
            "flags": self.flags,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status
        }

# aris/repositories/flagged_review_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from aris.data_models.flagged_review import FlaggedReview

class FlaggedReviewRepository(ABC):
    @abstractmethod
    def add_flagged_review(self, flagged_review: FlaggedReview):
        pass

    @abstractmethod
    def get_all_flagged_reviews(self) -> List[FlaggedReview]:
        pass

    @abstractmethod
    def get_flagged_review_by_id(self, review_id: str) -> Optional[FlaggedReview]:
        pass

class InMemoryFlaggedReviewRepository(FlaggedReviewRepository):
    def __init__(self):
        self._flagged_reviews: Dict[str, FlaggedReview] = {}

    def add_flagged_review(self, flagged_review: FlaggedReview):
        self._flagged_reviews[flagged_review.id] = flagged_review
        print(f"Stored flagged review: {flagged_review.id}")

    def get_all_flagged_reviews(self) -> List[FlaggedReview]:
        return list(self._flagged_reviews.values())

    def get_flagged_review_by_id(self, review_id: str) -> Optional[FlaggedReview]:
        return self._flagged_reviews.get(review_id)

# aris/rule_engine/rule_engine.py
from typing import List, Dict, Any, Type
from aris.rule_engine.rules.base_rule import Rule
from aris.rule_engine.rules.ip_match_rule import IpMatchRule
from aris.rule_engine.rules.keyword_match_rule import KeywordMatchRule
from aris.rule_engine.rules.rapid_review_rule import RapidReviewRule
from aris.data_models.review_data import ReviewData

class RuleEngine:
    RULE_TYPE_MAP: Dict[str, Type[Rule]] = {
        "IP_MATCH": IpMatchRule,
        "KEYWORD_MATCH": KeywordMatchRule,
        "RAPID_REVIEW": RapidReviewRule,
    }

    def __init__(self):
        self._rules: List[Rule] = []
        self.load_rules() # Load rules on initialization for simplicity

    def load_rules(self, rule_configs: List[Dict[str, Any]] = None):
        # In a real scenario, this would load from a database or configuration service.
        # For now, we'll use a hardcoded list or accept configs.
        self._rules = []
        if rule_configs is None:
            # Example hardcoded rules for demonstration
            rule_configs = [
                {"id": "rule-1", "name": "Suspicious IP Address", "rule_type": "IP_MATCH", "definition": {"ips": ["1.1.1.1", "2.2.2.2"]}, "is_enabled": True, "severity": "high"},
                {"id": "rule-2", "name": "Profanity in Review", "rule_type": "KEYWORD_MATCH", "definition": {"keywords": ["hate", "scam", "fraud"], "match_any": True}, "is_enabled": True, "severity": "medium"},
                {"id": "rule-3", "name": "Rapid Posting (Placeholder)", "rule_type": "RAPID_REVIEW", "definition": {"max_reviews": 5, "time_window_minutes": 60, "group_by": "user_id"}, "is_enabled": True, "severity": "low"},
            ]

        for config in rule_configs:
            rule_type = config.get("rule_type")
            if rule_type in self.RULE_TYPE_MAP:
                rule_class = self.RULE_TYPE_MAP[rule_type]
                self._rules.append(rule_class(
                    id=config["id"],
                    name=config["name"],
                    definition=config["definition"],
                    is_enabled=config.get("is_enabled", True),
                    severity=config.get("severity", "medium")
                ))
            else:
                print(f"WARNING: Unknown rule type: {rule_type}. Skipping rule {config.get('id')}")

    def evaluate_review(self, review_data: ReviewData) -> List[Dict[str, Any]]:
        triggered_flags = []
        for rule in self._rules:
            if rule.is_enabled and rule.evaluate(review_data):
                triggered_flags.append(rule.get_flag_details())
        return triggered_flags

# aris/services/flagging_service.py
from typing import List, Dict, Any, Optional
from aris.data_models.review_data import ReviewData
from aris.data_models.flagged_review import FlaggedReview
from aris.rule_engine.rule_engine import RuleEngine
from aris.repositories.flagged_review_repository import FlaggedReviewRepository

class FlaggingService:
    def __init__(self, rule_engine: RuleEngine, flagged_review_repo: FlaggedReviewRepository):
        self.rule_engine = rule_engine
        self.flagged_review_repo = flagged_review_repo

    def flag_incoming_review(self, review_data: ReviewData) -> Optional[FlaggedReview]:
        """
        Processes an incoming review, applies flagging rules, and stores if flagged.
        Returns the FlaggedReview object if flagged, None otherwise.
        """
        triggered_flags = self.rule_engine.evaluate_review(review_data)

        if triggered_flags:
            flagged_review = FlaggedReview(original_review=review_data, flags=triggered_flags)
            self.flagged_review_repo.add_flagged_review(flagged_review)
            print(f"Review {review_data.review_id} flagged with {len(triggered_flags)} rules.")
            return flagged_review
        else:
            print(f"Review {review_data.review_id} passed all rules.")
            return None
