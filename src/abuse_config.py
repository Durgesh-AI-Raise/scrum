# src/abuse_config.py
from datetime import datetime
from typing import List, Dict, Any, Optional
from data_models import AbuseCategory, AssociatedPattern

# This can be loaded from a JSON/YAML file in a real application
# For now, hardcoding for initial setup.
ABUSE_CATEGORIES_DATA: List[Dict[str, Any]] = [
    {
        "category_id": "FAKE_POSITIVE",
        "category_name": "Fake Positive Review",
        "description": "Reviews intentionally written to inflate product ratings, often by sellers or paid reviewers.",
        "severity_score": 9,
        "keywords_to_flag": ["best product ever", "must buy", "life changer", "amazing"],
        "associated_patterns": [{"pattern_id": "VELOCITY_SPIKE_PRODUCT", "strength": 4}]
    },
    {
        "category_id": "FAKE_NEGATIVE",
        "category_name": "Fake Negative Review",
        "description": "Reviews intentionally written to harm competitor product ratings.",
        "severity_score": 8,
        "keywords_to_flag": ["terrible product", "waste of money", "don't buy", "scam"],
        "associated_patterns": []
    },
    {
        "category_id": "INCENTIVIZED_UNDISCLOSED",
        "category_name": "Incentivized Review (Undisclosed)",
        "description": "Reviews given in exchange for free products or compensation without clear disclosure.",
        "severity_score": 7,
        "keywords_to_flag": ["received free product", "discounted for review", "sponsored"],
        "associated_patterns": []
    },
    {
        "category_id": "SPAM",
        "category_name": "Spam Review",
        "description": "Irrelevant, promotional, or repetitive content unrelated to the product.",
        "severity_score": 5,
        "keywords_to_flag": ["visit my website", "buy now", "promo code"],
        "associated_patterns": []
    },
     {
        "category_id": "VELOCITY_ANOMALY",
        "category_name": "Review Velocity Anomaly",
        "description": "Unusual patterns in review submission rates (e.g., too many reviews in a short period).",
        "severity_score": 6,
        "keywords_to_flag": [],
        "associated_patterns": [{"pattern_id": "VELOCITY_SPIKE_PRODUCT", "strength": 5}, {"pattern_id": "VELOCITY_SPIKE_REVIEWER", "strength": 5}]
    }
]

ABUSE_CATEGORIES: Dict[str, AbuseCategory] = {
    cat['category_id']: AbuseCategory(**cat) for cat in ABUSE_CATEGORIES_DATA
}

def get_abuse_category(category_id: str) -> Optional[AbuseCategory]:
    return ABUSE_CATEGORIES.get(category_id)

def get_all_abuse_categories() -> List[AbuseCategory]:
    return list(ABUSE_CATEGORIES.values())
