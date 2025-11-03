
# aris/data_models/review_data.py
from datetime import datetime
from typing import Dict, Any

class ReviewData:
    def __init__(self, review_id: str, user_id: str, product_id: str,
                 ip_address: str, text: str, timestamp: datetime):
        self.review_id = review_id
        self.user_id = user_id
        self.product_id = product_id
        self.ip_address = ip_address
        self.text = text
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "review_id": self.review_id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "ip_address": self.ip_address,
            "text": self.text,
            "timestamp": self.timestamp.isoformat()
        }

# aris/rule_engine/rules/base_rule.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

class Rule(ABC):
    def __init__(self, id: str, name: str, rule_type: str, definition: Dict[str, Any], is_enabled: bool = True, severity: str = "medium"):
        self.id = id
        self.name = name
        self.rule_type = rule_type
        self.definition = definition
        self.is_enabled = is_enabled
        self.severity = severity

    @abstractmethod
    def evaluate(self, review_data: 'ReviewData') -> bool:
        """
        Evaluates the given review data against the rule's criteria.
        Returns True if the rule is triggered, False otherwise.
        """
        pass

    def get_flag_details(self) -> Dict[str, Any]:
        """Returns details about the rule for flagging purposes."""
        return {
            "rule_id": self.id,
            "rule_name": self.name,
            "rule_type": self.rule_type,
            "severity": self.severity,
            "triggered_on": datetime.now().isoformat(),
            "rule_definition": self.definition # Include definition for context
        }

# aris/rule_engine/rules/ip_match_rule.py
from typing import Any, Dict
from .base_rule import Rule
from ...data_models.review_data import ReviewData # Corrected import path for ReviewData

class IpMatchRule(Rule):
    def __init__(self, id: str, name: str, definition: Dict[str, Any], is_enabled: bool = True, severity: str = "medium"):
        super().__init__(id, name, "IP_MATCH", definition, is_enabled, severity)
        self.suspicious_ips = set(definition.get("ips", []))

    def evaluate(self, review_data: ReviewData) -> bool:
        if not self.is_enabled:
            return False
        return review_data.ip_address in self.suspicious_ips

# aris/rule_engine/rules/keyword_match_rule.py
from typing import Any, Dict
from .base_rule import Rule
from ...data_models.review_data import ReviewData # Corrected import path for ReviewData

class KeywordMatchRule(Rule):
    def __init__(self, id: str, name: str, definition: Dict[str, Any], is_enabled: bool = True, severity: str = "medium"):
        super().__init__(id, name, "KEYWORD_MATCH", definition, is_enabled, severity)
        self.keywords = [kw.lower() for kw in definition.get("keywords", [])]
        self.match_any = definition.get("match_any", True)

    def evaluate(self, review_data: ReviewData) -> bool:
        if not self.is_enabled:
            return False
        review_text_lower = review_data.text.lower()
        if self.match_any:
            return any(keyword in review_text_lower for keyword in self.keywords)
        else:
            return all(keyword in review_text_lower for keyword in self.keywords)

# aris/rule_engine/rules/rapid_review_rule.py
from typing import Any, Dict
from .base_rule import Rule
from ...data_models.review_data import ReviewData # Corrected import path for ReviewData

class RapidReviewRule(Rule):
    def __init__(self, id: str, name: str, definition: Dict[str, Any], is_enabled: bool = True, severity: str = "medium"):
        super().__init__(id, name, "RAPID_REVIEW", definition, is_enabled, severity)
        self.max_reviews = definition.get("max_reviews", 5)
        self.time_window_minutes = definition.get("time_window_minutes", 60)
        self.group_by = definition.get("group_by", "user_id")

    def evaluate(self, review_data: ReviewData) -> bool:
        if not self.is_enabled:
            return False
        # Placeholder: This rule requires integration with a review history service.
        # For now, it will always return False and log a message.
        # Future implementation will query a database/service for review velocity within the defined window.
        print(f"INFO: RapidReviewRule \'{self.name}\' (ID: {self.id}) is a placeholder and requires external service integration. Not evaluating.")
        return False
