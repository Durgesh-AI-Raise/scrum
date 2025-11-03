from datetime import datetime
from typing import List, Dict, Optional
import json
import os

# Assuming these modules will be created
from models.flagged_review import FlaggedReview
from repositories.flagged_review_repository import FlaggedReviewRepository

class RulesEngine:
    def __init__(self, rules_config_path="src/rules.json"):
        self.rules = self._load_rules(rules_config_path)

    def _load_rules(self, path):
        if not os.path.exists(path):
            print(f"Rules config file not found at {path}. Initializing with empty rules.")
            return []
        with open(path, 'r') as f:
            return json.load(f)

    def apply_rules(self, review_data) -> Optional[Dict]:
        matched_reasons = []
        highest_severity = "LOW" # Default

        for rule in self.rules:
            conditions_met = True
            for condition_key, condition_details in rule.get("conditions", {}).items():
                operator = condition_details.get("operator")
                value = condition_details.get("value")
                review_value = review_data.get(condition_key)

                if operator == "<":
                    # Assuming 'value' is like '7 days' and 'review_value' is a timedelta
                    if condition_key == "account_age" and isinstance(review_value, datetime) and isinstance(value, str):
                        num, unit = value.split(' ')
                        threshold_delta = None
                        if unit == 'days':
                            threshold_delta = timedelta(days=int(num))
                        elif unit == 'hours':
                            threshold_delta = timedelta(hours=int(num))
                        
                        if threshold_delta is not None and (review_data.get('current_time', datetime.now()) - review_value) >= threshold_delta:
                            conditions_met = False
                            break
                    elif isinstance(review_value, (int, float)) and isinstance(value, (int, float)):
                        if not (review_value < value):
                            conditions_met = False
                            break
                    else:
                        # Handle other types or raise error
                        pass
                elif operator == ">":
                    if condition_key == "review_velocity_per_product" and isinstance(review_value, (int, float)) and isinstance(value, str) and '/' in value:
                        # Handle '10/hour' format
                        num, _ = value.split('/')
                        if not (review_value > int(num)):
                            conditions_met = False
                            break
                    elif isinstance(review_value, (int, float)) and isinstance(value, (int, float)):
                        if not (review_value > value):
                            conditions_met = False
                            break
                    else:
                        # Handle other types or raise error
                        pass
                elif operator == "<=":
                    if isinstance(review_value, (int, float)) and isinstance(value, (int, float)):
                        if not (review_value <= value):
                            conditions_met = False
                            break
                elif operator == "duplicates_across_products":
                    threshold = condition_details.get("threshold")
                    if review_data.get("is_duplicate_content", False) and review_data.get("duplicate_count", 0) >= threshold:
                        pass
                    else:
                        conditions_met = False
                        break

            if conditions_met:
                matched_reasons.append({"rule_id": rule['rule_id'], "description": rule['description'], "flag_reason": rule['flag_reason']})
                # Update highest severity
                severity_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
                if severity_order.get(rule['severity'], 0) > severity_order.get(highest_severity, 0):
                    highest_severity = rule['severity']

        if matched_reasons:
            return {'severity': highest_severity, 'reasons': matched_reasons}
        return None


class ReviewIngestionService:
    def __init__(self, rules_engine: RulesEngine, flagged_review_repository: FlaggedReviewRepository):
        self.rules_engine = rules_engine
        self.flagged_review_repository = flagged_review_repository

    def process_review(self, review_data: Dict):
        print(f"Processing review: {review_data.get('review_id', 'N/A')}")
        flagging_results = self.rules_engine.apply_rules(review_data)

        if flagging_results:
            flagged_review = FlaggedReview(
                review_id=review_data['review_id'],
                product_id=review_data['product_id'],
                user_id=review_data['user_id'],
                rating=review_data['rating'],
                review_content=review_data['review_content'],
                review_timestamp=review_data['review_timestamp'],
                flagging_timestamp=datetime.now(),
                severity=flagging_results['severity'],
                reasons=flagging_results['reasons'],
                status="FLAGGED"
            )
            self.flagged_review_repository.save(flagged_review)
            print(f"Review {review_data['review_id']} FLAGGED with severity {flagging_results['severity']}. Reasons: {flagging_results['reasons']}")
        else:
            print(f"Review {review_data['review_id']} is legitimate.")

# Example Usage (Main entry point simulation)
# if __name__ == "__main__":
#     rules_engine = RulesEngine()
#     flagged_review_repo = FlaggedReviewRepository()
#     service = ReviewIngestionService(rules_engine, flagged_review_repo)

#     # Simulate incoming review data
#     sample_review_1 = {
#         'review_id': 'review123',
#         'product_id': 'prodA',
#         'user_id': 'userX',
#         'rating': 1,
#         'review_content': 'This product is terrible!',
#         'review_timestamp': datetime.now() - timedelta(days=20),
#         'account_age': datetime.now() - timedelta(days=5), # 5 days old account
#         'review_velocity_per_product': 8, # 8 reviews/hour for this product
#         'current_time': datetime.now()
#     }

#     sample_review_2 = {
#         'review_id': 'review456',
#         'product_id': 'prodB',
#         'user_id': 'userY',
#         'rating': 5,
#         'review_content': 'Great product, highly recommend.',
#         'review_timestamp': datetime.now() - timedelta(days=50),
#         'account_age': datetime.now() - timedelta(days=30), # 30 days old account
#         'review_velocity_per_product': 1,
#         'current_time': datetime.now()
#     }

#     service.process_review(sample_review_1)
#     service.process_review(sample_review_2)