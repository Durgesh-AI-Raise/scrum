
# detection_engine.py

RULE_SCORES = {
    "LOW_RATING_SHORT_TEXT": 20,
    "HIGH_RATING_SHORT_TEXT": 15,
    "NO_REVIEW_TEXT_WITH_EXTREME_RATING": 25,
    # "POTENTIALLY_NEW_REVIEWER": 10, # If implemented (requires DB lookup)
}

def detect_suspicious_characteristics(review_data):
    flagged_reasons = []

    review_text = review_data.get('text', '').strip()
    rating = review_data['rating']

    # Rule 1: Low Rating, Short Text (assuming non-empty text)
    if rating <= 2 and 0 < len(review_text.split()) < 10:
        flagged_reasons.append("LOW_RATING_SHORT_TEXT")

    # Rule 2: High Rating, Short Text (assuming non-empty text)
    if rating >= 4 and 0 < len(review_text.split()) < 10:
        flagged_reasons.append("HIGH_RATING_SHORT_TEXT")

    # Rule 3: No Review Text but has extreme rating (1 or 5 stars)
    if not review_text and review_data.get('title') and (rating == 1 or rating == 5):
        flagged_reasons.append("NO_REVIEW_TEXT_WITH_EXTREME_RATING")

    # Further rules would be added here, potentially requiring DB queries

    return flagged_reasons

def calculate_risk_score(flagged_reasons):
    total_score = 0
    for reason in flagged_reasons:
        total_score += RULE_SCORES.get(reason, 0)
    return total_score
