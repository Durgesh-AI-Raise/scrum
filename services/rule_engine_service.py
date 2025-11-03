import json
import re
from datetime import datetime, timedelta

class RuleEngine:
    def __init__(self, rule_storage_client=None):
        self.rules = {}
        if rule_storage_client:
            self.load_rules(rule_storage_client) # Placeholder for real DB client
        else:
            self._load_mock_rules()

    def _load_mock_rules(self):
        self.add_rule({
            "rule_id": "profanity-keyword",
            "rule_name": "Profanity Keyword Match",
            "rule_type": "keyword_match",
            "status": "active",
            "priority": 1, # Higher priority
            "config": {
                "keywords": ["damn", "hell", "crap", "shit"],
                "match_case": False,
                "min_occurrences": 1
            }
        })
        self.add_rule({
            "rule_id": "cta-keyword",
            "rule_name": "Urgent Call to Action",
            "rule_type": "keyword_match",
            "status": "active",
            "priority": 2, # Medium priority
            "config": {
                "keywords": ["BUY NOW", "LIMITED TIME", "CLICK HERE"],
                "match_case": True,
                "min_occurrences": 1
            }
        })
        self.add_rule({
            "rule_id": "spam-phrase",
            "rule_name": "Generic Spam Phrase",
            "rule_type": "keyword_match",
            "status": "active",
            "priority": 3, # Lower priority
            "config": {
                "keywords": ["free money", "get rich quick"],
                "match_case": False,
                "min_occurrences": 1
            }
        })
        # Velocity rule is conceptual for now, would require historical data query
        self.add_rule({
            "rule_id": "review-velocity",
            "rule_name": "High Review Velocity",
            "rule_type": "review_velocity",
            "status": "inactive", # Inactive for MVP as no velocity logic
            "priority": 4,
            "config": {
                "time_window_minutes": 60,
                "max_reviews_per_user": 5
            }
        })

    def load_rules(self, rule_storage_client):
        # In a real system, fetch active rules from rule_storage_client (e.g., DB)
        # For MVP, we use _load_mock_rules or an in-memory store via API
        pass

    def add_rule(self, rule_data):
        if rule_data.get("status") == "active":
            self.rules[rule_data["rule_id"]] = rule_data

    def evaluate_review(self, review):
        flags = []
        review_text = review.get("review_text", "")
        if not review_text:
            return flags

        for rule_id, rule in self.rules.items():
            if rule["rule_type"] == "keyword_match":
                if self._evaluate_keyword_match(review_text, rule["config"]):
                    flags.append({
                        "rule_id": rule_id,
                        "rule_name": rule["rule_name"],
                        "priority": rule["priority"],
                        "matched_type": "keyword"
                    })
            # Add other rule types here (e.g., review_velocity)
            elif rule["rule_type"] == "review_velocity" and rule["status"] == "active":
                # This would involve querying a database for historical reviews
                # For MVP, this is a placeholder
                pass
        return flags

    def _evaluate_keyword_match(self, text, config):
        keywords = config.get("keywords", [])
        match_case = config.get("match_case", False)
        min_occurrences = config.get("min_occurrences", 1)

        matched_count = 0
        for keyword in keywords:
            if not match_case:
                matched_count += len(re.findall(re.escape(keyword), text, re.IGNORECASE))
            else:
                matched_count += len(re.findall(re.escape(keyword), text))
        return matched_count >= min_occurrences

if __name__ == "__main__":
    rule_engine = RuleEngine()
    sample_review_1 = {"review_id": "r1", "review_text": "This product is damn good! BUY NOW!", "timestamp": datetime.now().isoformat()}
    sample_review_2 = {"review_id": "r2", "review_text": "A perfectly fine item, no issues.", "timestamp": datetime.now().isoformat()}
    sample_review_3 = {"review_id": "r3", "review_text": "Get rich quick with this!", "timestamp": datetime.now().isoformat()}

    print(f"Review 1 flags: {rule_engine.evaluate_review(sample_review_1)}")
    print(f"Review 2 flags: {rule_engine.evaluate_review(sample_review_2)}")
    print(f"Review 3 flags: {rule_engine.evaluate_review(sample_review_3)}")
