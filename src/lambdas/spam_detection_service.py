import json
import re
import math
from collections import Counter

SPAM_RULES = [
  {
    "rule_id": "SPAM_GIBBERISH_ENTROPY",
    "rule_name": "Low Entropy Gibberish Detection",
    "rule_type": "ENTROPY_CHECK",
    "threshold": 3.0, # Lower entropy indicates more gibberish
    "target_field": "review_text",
    "severity": "HIGH",
    "enabled": True
  },
  {
    "rule_id": "SPAM_EXCESSIVE_LINKS",
    "rule_name": "Multiple Link Detection",
    "rule_type": "REGEX_COUNT",
    "pattern": r"(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)",
    "threshold": 2, # More than 2 links
    "target_field": "review_text",
    "severity": "HIGH",
    "enabled": True
  },
  {
    "rule_id": "SPAM_COMMON_KEYWORDS",
    "rule_name": "Common Spam Keywords",
    "rule_type": "KEYWORD_LIST",
    "keywords": ["free gift card", "promo code", "click here", "discount code"],
    "target_field": "review_text",
    "severity": "MEDIUM",
    "enabled": True
  }
]

def calculate_entropy(text):
    if not text:
        return 0.0
    probabilities = [count / len(text) for count in Counter(text).values()]
    entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
    return entropy

def detect_spam(review):
    flags = []
    review_text = review.get("review_text", "").lower()

    for rule in SPAM_RULES:
        if not rule.get("enabled"):
            continue

        if rule["rule_type"] == "ENTROPY_CHECK":
            entropy = calculate_entropy(review_text)
            if entropy < rule["threshold"]:
                flags.append(rule["rule_id"])
        elif rule["rule_type"] == "REGEX_COUNT":
            matches = re.findall(rule["pattern"], review_text)
            if len(matches) > rule["threshold"]:
                flags.append(rule["rule_id"])
        elif rule["rule_type"] == "KEYWORD_LIST":
            for keyword in rule["keywords"]:
                if keyword in review_text:
                    flags.append(rule["rule_id"])
                    break

    return list(set(flags))

def lambda_handler(event, context):
    processed_records = []
    for record_body in event:
        review_data = record_body
        if not review_data.get("review_id"):
            print(f"Skipping record due to missing review_id: {review_data}")
            continue

        flags = detect_spam(review_data)
        
        existing_flags = review_data.get("detection_flags", [])
        review_data["detection_flags"] = list(set(existing_flags + flags))

        processed_records.append(review_data)
    return processed_records